from __future__ import annotations

import itertools
import logging
import re
import time
from dataclasses import replace
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from .directories import Directory
from .models import CityPoint, FlightOffer, MultiCityLeg, MultiCityQuery, MultiCityRoute, RoundTripOffer, SearchMode, SearchQuery

logger = logging.getLogger(__name__)


class TravelpayoutsClient:
    """Small client for Aviasales Data API.

    It uses cached Data API offers and adds UX filters/ranking locally.
    The important product flow is unordered multi-city optimization: user gives
    cities to visit, while we choose the cheapest feasible order.
    """

    API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    LINKS_API_URL = "https://api.travelpayouts.com/links/v1/create"
    LINKS_BATCH_SIZE = 10

    def __init__(
        self,
        token: str,
        marker: str | None = None,
        trs: int | None = None,
        timeout_seconds: int = 15,
        session: requests.Session | None = None,
    ):
        self.token = token
        self.marker = marker
        self.trs = trs
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def search(self, query: SearchQuery, directory: Directory, limit_per_destination: int = 10) -> list[FlightOffer]:
        if not self.token:
            raise RuntimeError("AVIASALES_TOKEN пустой. Укажи токен в .env")

        destinations = [c for c in query.destination.codes if c != query.origin_code]
        logger.info(
            "Search start: %s → %s (codes=%s), dates=%s..%s, mode=%s, max_price=%s, max_transfers=%s, max_duration=%s",
            query.origin_code,
            query.destination.label,
            destinations,
            query.date_from,
            query.date_to,
            query.mode.value,
            query.max_price,
            query.max_transfers,
            query.max_duration_minutes,
        )
        offers: list[FlightOffer] = []
        for destination_code in destinations:
            offers.extend(self._search_one_destination(query, destination_code, directory, limit_per_destination))

        before_dedup = len(offers)
        offers = self._dedupe(offers)
        logger.info("Search dedup: %d → %d offers", before_dedup, len(offers))
        offers.sort(key=lambda offer: offer.score)
        self._convert_links_to_partner(offers)
        logger.info("Search done: %d offers for %s → %s", len(offers), query.origin_code, query.destination.label)
        return offers

    def search_ideas(
        self,
        query: SearchQuery,
        directory: Directory,
        limit_per_destination: int = 3,
        max_results: int = 10,
    ) -> list[FlightOffer]:
        """Open-ended budget search.

        The user does not choose a destination. We scan a curated pool from
        data/idea_destinations.json and intentionally diversify results by country
        so the bot returns genuinely different trip ideas, not ten nearby airports
        from the same market.
        """
        offers = self.search(query, directory, limit_per_destination=limit_per_destination)
        return self._diversify_ideas(offers, directory, max_results=max_results)

    def search_ideas_round_trip(
        self,
        query: SearchQuery,
        directory: Directory,
        limit_per_destination: int = 6,
        max_results: int = 10,
    ) -> list[RoundTripOffer]:
        """Open-ended budget search for round trips.

        In ideas mode the budget is user-facing total budget. For `и обратно`,
        it must be applied to outbound + inbound together, not to each leg.
        """
        routes = self.search_round_trip(
            query,
            directory,
            limit_per_destination=max(limit_per_destination, max_results * 2),
        )
        return self._diversify_roundtrip_ideas(routes, directory, max_results=max_results)

    @staticmethod
    def _diversify_ideas(offers: list[FlightOffer], directory: Directory, max_results: int = 10) -> list[FlightOffer]:
        # Keep only the best offer per destination city first.
        best_by_destination: dict[str, FlightOffer] = {}
        for offer in sorted(offers, key=lambda item: (item.score, item.price)):
            best_by_destination.setdefault(offer.destination, offer)

        pool = sorted(best_by_destination.values(), key=lambda item: (item.score, item.price))
        selected: list[FlightOffer] = []
        used_countries: set[str] = set()

        # First pass: maximize country diversity.
        for offer in pool:
            country = directory.idea_profile(offer.destination).get("country", "Другое")
            if country in used_countries:
                continue
            selected.append(offer)
            used_countries.add(country)
            if len(selected) >= max_results:
                return selected

        # Second pass: fill remaining slots with the next best cities.
        selected_codes = {offer.destination for offer in selected}
        for offer in pool:
            if offer.destination in selected_codes:
                continue
            selected.append(offer)
            selected_codes.add(offer.destination)
            if len(selected) >= max_results:
                break
        return selected

    @staticmethod
    def _diversify_roundtrip_ideas(routes: list[RoundTripOffer], directory: Directory, max_results: int = 10) -> list[RoundTripOffer]:
        # Keep only the best round-trip per destination first.
        best_by_destination: dict[str, RoundTripOffer] = {}
        for route in sorted(routes, key=lambda item: (item.score, item.total_price)):
            best_by_destination.setdefault(route.destination.code, route)

        pool = sorted(best_by_destination.values(), key=lambda item: (item.score, item.total_price))
        selected: list[RoundTripOffer] = []
        used_countries: set[str] = set()

        for route in pool:
            country = directory.idea_profile(route.destination.code).get("country", "Другое")
            if country in used_countries:
                continue
            selected.append(route)
            used_countries.add(country)
            if len(selected) >= max_results:
                return selected

        selected_codes = {route.destination.code for route in selected}
        for route in pool:
            if route.destination.code in selected_codes:
                continue
            selected.append(route)
            selected_codes.add(route.destination.code)
            if len(selected) >= max_results:
                break
        return selected


    def search_round_trip(
        self,
        query: SearchQuery,
        directory: Directory,
        limit_per_destination: int = 8,
        max_offers_per_leg: int = 40,
    ) -> list[RoundTripOffer]:
        """Search `origin → destination → origin` for city/country discovery.

        UX rule: `из СПб в Китай и обратно 06.07-14.07` is not an unknown
        destination. It is parsed as outbound on 06.07 and return on 14.07.
        With two ranges, e.g. `туда 06.07-08.07 обратно 14.07-16.07`, both
        legs are flexible inside their own windows.
        """
        if not self.token:
            raise RuntimeError("AVIASALES_TOKEN пустой. Укажи токен в .env")
        if not query.is_round_trip:
            return []
        assert query.return_date_from is not None and query.return_date_to is not None

        logger.info(
            "Round-trip start: %s → %s, outbound=%s..%s, return=%s..%s, budget=%s",
            query.origin_code,
            query.destination.label,
            query.date_from,
            query.date_to,
            query.return_date_from,
            query.return_date_to,
            query.max_price,
        )
        results: list[RoundTripOffer] = []
        origin_point = CityPoint(query.origin_label, query.origin_code)
        for destination_code in query.destination.codes:
            if destination_code == query.origin_code:
                continue
            destination_point = CityPoint(directory.label_for_code(destination_code), destination_code)

            outbound_query = SearchQuery(
                origin_label=query.origin_label,
                origin_code=query.origin_code,
                destination=replace_destination(destination_point),
                date_from=query.date_from,
                date_to=query.date_to,
                max_price=query.max_price,
                max_transfers=query.max_transfers,
                max_duration_minutes=query.max_duration_minutes,
                currency=query.currency,
                market=query.market,
                mode=SearchMode.ROUND_TRIP,
                raw_text=query.raw_text,
            )
            inbound_query = SearchQuery(
                origin_label=destination_point.label,
                origin_code=destination_code,
                destination=replace_destination(origin_point),
                date_from=query.return_date_from,
                date_to=query.return_date_to,
                max_price=query.max_price,
                max_transfers=query.max_transfers,
                max_duration_minutes=query.max_duration_minutes,
                currency=query.currency,
                market=query.market,
                mode=SearchMode.ROUND_TRIP,
                raw_text=query.raw_text,
            )

            outbound_offers = self._search_one_destination(outbound_query, destination_code, directory, max_offers_per_leg)
            inbound_offers = self._search_one_destination(inbound_query, query.origin_code, directory, max_offers_per_leg)
            if not outbound_offers or not inbound_offers:
                logger.debug(
                    "Round-trip %s→%s: skipped (outbound=%d, inbound=%d)",
                    query.origin_code,
                    destination_code,
                    len(outbound_offers),
                    len(inbound_offers),
                )
                continue

            best_for_destination: RoundTripOffer | None = None
            for outbound in outbound_offers:
                for inbound in inbound_offers:
                    if outbound.arrival_at and inbound.departure_at and inbound.departure_at <= outbound.arrival_at:
                        continue
                    total_price = outbound.price + inbound.price
                    if query.max_price is not None and total_price > query.max_price:
                        continue
                    score = outbound.score + inbound.score
                    candidate = RoundTripOffer(
                        destination=destination_point,
                        outbound=outbound,
                        inbound=inbound,
                        total_price=total_price,
                        score=score,
                    )
                    if best_for_destination is None or (candidate.score, candidate.total_price) < (best_for_destination.score, best_for_destination.total_price):
                        best_for_destination = candidate
            if best_for_destination:
                results.append(best_for_destination)
                logger.info(
                    "Round-trip %s→%s: best pair price=%d (outbound=%d + inbound=%d)",
                    query.origin_code,
                    destination_code,
                    best_for_destination.total_price,
                    best_for_destination.outbound.price,
                    best_for_destination.inbound.price,
                )
            else:
                logger.debug("Round-trip %s→%s: no valid pair within budget", query.origin_code, destination_code)

        results.sort(key=lambda item: (item.score, item.total_price))
        truncated = results[:limit_per_destination]
        logger.info("Round-trip done: %d results (showing %d)", len(results), len(truncated))
        leg_offers: list[FlightOffer] = []
        for item in truncated:
            leg_offers.append(item.outbound)
            leg_offers.append(item.inbound)
        self._convert_links_to_partner(leg_offers)
        return truncated

    def optimize_multicity(
        self,
        query: MultiCityQuery,
        directory: Directory,
        max_routes: int = 5,
        max_offers_per_pair: int = 80,
        beam_width: int = 40,
    ) -> list[MultiCityRoute]:
        """Find cheapest order for an unordered list of cities.

        This is the core feature that Aviasales does not provide as a simple UI:
        the user says "I want to visit A, B, C" and the bot decides whether the
        cheapest route is A→C→B, B→A→C, etc. It also picks concrete legs inside
        the date window and respects min/max stay between visited cities.
        """
        if not self.token:
            raise RuntimeError("AVIASALES_TOKEN пустой. Укажи токен в .env")

        route_points = (query.origin, *query.visit_cities)
        if query.final_destination and query.final_destination.code not in {point.code for point in route_points}:
            route_points = (*route_points, query.final_destination)

        pairs = list(itertools.permutations(route_points, 2))
        logger.info(
            "Multi-city start: %d points, %d city pairs to search, dates=%s..%s, budget=%s",
            len(route_points),
            len(pairs),
            query.date_from,
            query.date_to,
            query.max_price,
        )

        offers_by_pair: dict[tuple[str, str], list[FlightOffer]] = {}
        for origin, destination in pairs:
            pair_query = SearchQuery(
                origin_label=origin.label,
                origin_code=origin.code,
                destination=replace_destination(destination),
                date_from=query.date_from,
                date_to=query.date_to,
                max_price=None,
                max_transfers=query.max_transfers,
                max_duration_minutes=query.max_duration_minutes,
                currency=query.currency,
                market=query.market,
                mode=SearchMode.MULTI_CITY,
                raw_text=query.raw_text,
            )
            offers = self._search_one_destination(pair_query, destination.code, directory, max_offers_per_pair)
            offers.sort(key=lambda offer: (offer.departure_at or datetime.max, offer.score))
            offers_by_pair[(origin.code, destination.code)] = offers
            logger.debug("Multi-city pair %s→%s: %d offers", origin.code, destination.code, len(offers))

        permutations = list(itertools.permutations(query.visit_cities))
        logger.info("Multi-city: checking %d permutations", len(permutations))
        routes: list[MultiCityRoute] = []
        for order in permutations:
            if query.final_destination:
                sequence = (query.origin, *order, query.final_destination)
            elif query.return_to_origin:
                sequence = (query.origin, *order, query.origin)
            else:
                sequence = (query.origin, *order)
            seq_labels = " → ".join(p.label for p in sequence)
            best_for_order = self._best_route_for_sequence(
                sequence=sequence,
                offers_by_pair=offers_by_pair,
                query=query,
                beam_width=beam_width,
            )
            if best_for_order:
                routes.append(best_for_order)
                logger.debug(
                    "Multi-city permutation %s: FOUND route price=%d score=%.0f",
                    seq_labels,
                    best_for_order.total_price,
                    best_for_order.score,
                )
            else:
                logger.debug("Multi-city permutation %s: no feasible route", seq_labels)

        routes.sort(key=lambda route: route.score)
        truncated_routes = routes[:max_routes]
        logger.info(
            "Multi-city done: %d feasible routes (showing %d)",
            len(routes),
            len(truncated_routes),
        )
        leg_offers: list[FlightOffer] = []
        for route in truncated_routes:
            leg_offers.extend(leg.offer for leg in route.legs)
        self._convert_links_to_partner(leg_offers)
        return truncated_routes

    def _best_route_for_sequence(
        self,
        sequence: tuple[CityPoint, ...],
        offers_by_pair: dict[tuple[str, str], list[FlightOffer]],
        query: MultiCityQuery,
        beam_width: int,
    ) -> MultiCityRoute | None:
        if len(sequence) < 2:
            return None

        earliest = datetime.combine(query.date_from, dt_time.min, tzinfo=timezone.utc)
        latest = datetime.combine(query.date_to, dt_time.max, tzinfo=timezone.utc)
        # Each state: (legs, earliest_next_departure, latest_next_departure, total_price, score)
        states: list[tuple[tuple[MultiCityLeg, ...], datetime, datetime, int, float]] = [
            (tuple(), earliest, latest, 0, 0.0)
        ]

        for index, (origin, destination) in enumerate(zip(sequence, sequence[1:])):
            pair_offers = offers_by_pair.get((origin.code, destination.code), [])
            if not pair_offers:
                return None
            next_states: list[tuple[tuple[MultiCityLeg, ...], datetime, datetime, int, float]] = []
            is_last_leg = index == len(sequence) - 2

            for legs, min_departure, max_departure, total_price, score in states:
                for offer in pair_offers:
                    if not offer.departure_at or not offer.arrival_at:
                        continue
                    if offer.departure_at < min_departure or offer.departure_at > max_departure:
                        continue
                    if offer.arrival_at > latest:
                        continue

                    new_total = total_price + offer.price
                    if query.max_price is not None and new_total > query.max_price:
                        continue

                    leg = MultiCityLeg(origin=origin, destination=destination, offer=offer)
                    if is_last_leg:
                        next_min = offer.arrival_at
                        next_max = latest
                    else:
                        # Stay in each visited city before the next flight. We use arrival_at
                        # from Data API duration; if max stay is absent, the outer date window is the limit.
                        next_min = offer.arrival_at + timedelta(days=query.min_stay_days)
                        if query.max_stay_days is None:
                            next_max = latest
                        else:
                            next_max = min(latest, offer.arrival_at + timedelta(days=query.max_stay_days))

                    next_score = score + offer.score
                    next_states.append((legs + (leg,), next_min, next_max, new_total, next_score))

            if not next_states:
                return None
            next_states.sort(key=lambda state: (state[4], state[3]))
            states = next_states[:beam_width]

        best = min(states, key=lambda state: (state[4], state[3]), default=None)
        if not best:
            return None
        legs, _min_dep, _max_dep, total_price, score = best
        total_duration = sum(leg.offer.duration_minutes for leg in legs)
        # Slight tie-breaker: users usually prefer less airport time and fewer transfers
        transfer_penalty = sum(leg.offer.transfers for leg in legs) * 2_000
        return MultiCityRoute(
            order=tuple(sequence),
            legs=legs,
            total_price=total_price,
            total_duration_minutes=total_duration,
            score=score + transfer_penalty,
        )

    def _search_one_destination(
        self,
        query: SearchQuery,
        destination_code: str,
        directory: Directory,
        limit: int,
    ) -> list[FlightOffer]:
        offers: list[FlightOffer] = []
        months = _months_between(query.date_from, query.date_to)
        logger.debug(
            "API request %s→%s: %d months=%s, limit=%d",
            query.origin_code,
            destination_code,
            len(months),
            months,
            limit,
        )
        for month in months:
            params = {
                "origin": query.origin_code,
                "destination": destination_code,
                "departure_at": month,
                "sorting": "price",
                "currency": query.currency,
                "market": query.market,
                "limit": max(limit, 50),
                "token": self.token,
            }
            started = time.time()
            try:
                response = self.session.get(self.API_URL, params=params, timeout=self.timeout_seconds)
                response.raise_for_status()
                payload = response.json()
            except requests.RequestException as exc:
                logger.warning(
                    "API HTTP error %s→%s month=%s: %s (took %.2fs)",
                    query.origin_code,
                    destination_code,
                    month,
                    exc,
                    time.time() - started,
                )
                continue
            except ValueError as exc:
                logger.warning(
                    "API JSON parse error %s→%s month=%s: %s",
                    query.origin_code,
                    destination_code,
                    month,
                    exc,
                )
                continue

            elapsed = time.time() - started
            success = payload.get("success")
            raw_items = payload.get("data") or []
            logger.info(
                "API %s→%s month=%s: success=%s, items=%d in %.2fs",
                query.origin_code,
                destination_code,
                month,
                success,
                len(raw_items),
                elapsed,
            )
            if not success:
                continue

            parsed = 0
            filtered_out = 0
            for item in raw_items:
                offer = self._to_offer(item, query, destination_code, directory)
                if not offer:
                    continue
                parsed += 1
                if not self._passes_filters(offer, query):
                    filtered_out += 1
                    continue
                offers.append(offer)
            logger.debug(
                "API %s→%s month=%s: parsed=%d, passed_filters=%d, filtered_out=%d",
                query.origin_code,
                destination_code,
                month,
                parsed,
                parsed - filtered_out,
                filtered_out,
            )
        before_dedup = len(offers)
        offers = self._dedupe(offers)
        if before_dedup != len(offers):
            logger.debug("Dedup %s→%s: %d → %d", query.origin_code, destination_code, before_dedup, len(offers))
        offers.sort(key=lambda offer: offer.score)
        logger.info(
            "API result %s→%s: %d offers after all filters (returning %d)",
            query.origin_code,
            destination_code,
            len(offers),
            min(len(offers), limit),
        )
        return offers[:limit]

    def _to_offer(
        self,
        item: dict,
        query: SearchQuery,
        destination_code: str,
        directory: Directory,
    ) -> FlightOffer | None:
        try:
            departure = _parse_datetime(item.get("departure_at"))
            if departure is None:
                return None
            if not (query.date_from <= departure.date() <= query.date_to):
                return None
            price = int(item["price"])
            duration = int(item.get("duration") or 0)
            transfers = int(item.get("transfers") or 0)
        except (TypeError, ValueError, KeyError):
            logger.debug("Cannot parse offer: %r", item, exc_info=True)
            return None

        raw_link = str(item.get("link") or "")
        link, sub_id = self._build_ticket_link(raw_link, query, destination_code)
        raw_with_meta = dict(item)
        if sub_id:
            raw_with_meta["_sub_id"] = sub_id
        offer = FlightOffer(
            origin=query.origin_code,
            destination=destination_code,
            origin_label=query.origin_label,
            destination_label=directory.label_for_code(destination_code),
            price=price,
            airline=item.get("airline"),
            transfers=transfers,
            duration_minutes=duration,
            departure_at=departure,
            link=link,
            raw=raw_with_meta,
        )
        offer.score = self._score(offer)
        return offer

    def _passes_filters(self, offer: FlightOffer, query: SearchQuery) -> bool:
        if query.max_price is not None and offer.price > query.max_price:
            logger.debug(
                "Filter reject %s→%s price=%d (max_price=%d)",
                offer.origin, offer.destination, offer.price, query.max_price,
            )
            return False
        if query.max_transfers is not None and offer.transfers > query.max_transfers:
            logger.debug(
                "Filter reject %s→%s transfers=%d (max_transfers=%d)",
                offer.origin, offer.destination, offer.transfers, query.max_transfers,
            )
            return False
        if query.max_duration_minutes is not None and offer.duration_minutes > query.max_duration_minutes:
            logger.debug(
                "Filter reject %s→%s duration=%d (max_duration=%d)",
                offer.origin, offer.destination, offer.duration_minutes, query.max_duration_minutes,
            )
            return False
        return True

    @staticmethod
    def _score(offer: FlightOffer) -> float:
        # Product ranking: price is primary, but awful routes should go lower.
        transfer_penalty = offer.transfers * 5_000
        duration_penalty = max(0, offer.duration_minutes - 5 * 60) * 30
        night_penalty = 2_000 if offer.departure_at and offer.departure_at.hour < 6 else 0
        return offer.price + transfer_penalty + duration_penalty + night_penalty

    def _build_ticket_link(self, raw_link: str, query: SearchQuery, destination_code: str) -> tuple[str, str | None]:
        """Build a ticket URL plus an optional sub_id for partner-link conversion.

        Returns ``(url, sub_id)``:
          * When ``self.trs`` is set, the URL is a clean Aviasales link and
            ``sub_id`` is returned separately so the caller can later convert
            the URL via the Travelpayouts Partner Links API.
          * When ``self.trs`` is not set, the URL already carries
            ``?marker=<id>&sub_id=<sub_id>`` (the safest manual format for
            direct Aviasales URLs) and ``sub_id`` is ``None``.
        """
        if not raw_link:
            raw_link = f"/search/{query.origin_code}{query.date_from:%d%m}{destination_code}1"
        if raw_link.startswith("/"):
            url = "https://www.aviasales.ru" + raw_link
        else:
            url = raw_link

        sub_id = sanitize_sub_id(
            f"tg_{query.mode.value}_{query.origin_code}_{destination_code}_{query.date_from:%Y%m%d}"
        )

        if not self.marker:
            logger.debug("Built link (no marker): %s", url)
            return url, None

        if self.trs:
            logger.debug("Built link (trs=%s, sub_id=%s): %s", self.trs, sub_id, url)
            return url, sub_id

        final_url = add_query_params(url, {"marker": self.marker, "sub_id": sub_id})
        logger.debug("Built link (fallback, marker=%s sub_id=%s): %s", self.marker, sub_id, final_url)
        return final_url, None

    @staticmethod
    def _dedupe(offers: Iterable[FlightOffer]) -> list[FlightOffer]:
        best_by_key: dict[tuple[str, str, str, int], FlightOffer] = {}
        for offer in offers:
            date_key = offer.departure_at.isoformat() if offer.departure_at else "unknown"
            key = (offer.origin, offer.destination, date_key, offer.transfers)
            current = best_by_key.get(key)
            if current is None or offer.price < current.price:
                best_by_key[key] = offer
        return list(best_by_key.values())

    def _create_partner_links(self, pairs: list[tuple[str, str | None]]) -> dict[str, str]:
        """Convert raw brand URLs into real partner links via Travelpayouts API.

        ``pairs`` is a list of ``(raw_url, sub_id)`` tuples. Returns a mapping
        ``{raw_url: partner_url}`` for successfully converted links. On any
        error (network, auth, invalid response) returns an empty dict so the
        caller can fall back to manual marker/sub_id links.
        """
        if not self.trs or not self.marker or not pairs:
            return {}

        marker_str = self.marker.strip()
        try:
            marker_int = int(marker_str)
        except ValueError:
            logger.warning("Partner Links API requires numeric marker, got %r", self.marker)
            return {}

        result: dict[str, str] = {}
        total_batches = (len(pairs) + self.LINKS_BATCH_SIZE - 1) // self.LINKS_BATCH_SIZE
        for batch_idx, start in enumerate(range(0, len(pairs), self.LINKS_BATCH_SIZE), start=1):
            batch = pairs[start : start + self.LINKS_BATCH_SIZE]
            payload = {
                "trs": self.trs,
                "marker": marker_int,
                "shorten": True,
                "links": [
                    {"url": url, **({"sub_id": sub_id} if sub_id else {})}
                    for url, sub_id in batch
                ],
            }
            logger.info(
                "Partner Links API: batch %d/%d, %d URLs (marker=%s trs=%s)",
                batch_idx,
                total_batches,
                len(batch),
                self.marker,
                self.trs,
            )
            try:
                response = self.session.post(
                    self.LINKS_API_URL,
                    json=payload,
                    headers={"X-Access-Token": self.token},
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                payload_json = response.json()
            except Exception as exc:
                logger.warning(
                    "Partner Links API: batch %d/%d FAILED: %s",
                    batch_idx,
                    total_batches,
                    exc,
                )
                return result

            links = (payload_json.get("result") or {}).get("links") or []
            batch_mapped = 0
            for entry in links:
                if entry.get("code") != "success":
                    logger.debug(
                        "Partner Links API: URL %s conversion failed: code=%s message=%s",
                        entry.get("url"),
                        entry.get("code"),
                        entry.get("message"),
                    )
                    continue
                partner_url = entry.get("partner_url") or ""
                original_url = entry.get("url") or ""
                if partner_url and original_url:
                    result[original_url] = partner_url
                    batch_mapped += 1
            logger.info(
                "Partner Links API: batch %d/%d done, mapped %d/%d URLs",
                batch_idx,
                total_batches,
                batch_mapped,
                len(batch),
            )
        return result

    def _convert_links_to_partner(self, offers: list[FlightOffer]) -> None:
        """Replace raw Aviasales URLs in ``offers`` with real partner links in place.

        Offers built with ``self.trs`` set carry a clean URL plus a ``_sub_id``
        stored in ``offer.raw``. This method batches those URLs through the
        Partner Links API and rewrites ``offer.link`` to the returned
        ``partner_url``. Offers whose URL could not be converted fall back to a
        direct Aviasales URL with ``?marker=<id>&sub_id=<sub_id>``.
        """
        candidate_pairs: list[tuple[str, str | None]] = []
        candidate_offers: list[FlightOffer] = []
        for offer in offers:
            sub_id = offer.raw.get("_sub_id") if isinstance(offer.raw, dict) else None
            if not sub_id:
                continue
            candidate_pairs.append((offer.link, sub_id))
            candidate_offers.append(offer)

        if not candidate_pairs:
            logger.debug("Convert links: no candidates with sub_id, skipping (already fallback format)")
            return

        partner_map = self._create_partner_links(candidate_pairs)
        converted = 0
        fallback = 0
        for offer, (url, sub_id) in zip(candidate_offers, candidate_pairs):
            partner_url = partner_map.get(url)
            if partner_url:
                offer.link = partner_url
                converted += 1
            else:
                offer.link = add_query_params(url, {"marker": self.marker, "sub_id": sub_id})
                fallback += 1
                logger.debug("Convert links: fallback for %s → marker=%s sub_id=%s", url, self.marker, sub_id)
        logger.info(
            "Partner Links API: converted %d/%d offers, fallback %d (marker=%s trs=%s)",
            converted,
            len(candidate_offers),
            fallback,
            self.marker,
            self.trs,
        )


def replace_destination(point: CityPoint):
    # Local helper to avoid importing Destination in old callers and to keep
    # SearchQuery construction explicit at callsite.
    from .models import Destination

    return Destination(label=point.label, codes=(point.code,), kind="city")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


def _months_between(date_from: date, date_to: date) -> list[str]:
    current = date(date_from.year, date_from.month, 1)
    end = date(date_to.year, date_to.month, 1)
    months: list[str] = []
    while current <= end:
        months.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def add_query_params(url: str, params: dict[str, str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({k: v for k, v in params.items() if v})
    return urlunparse(parsed._replace(query=urlencode(query)))


def sanitize_sub_id(value: str) -> str:
    """Keep SubID compatible with Travelpayouts reporting: latin letters, digits, underscores."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    return value.strip("_") or "tg"


def build_marker(marker: str, sub_id: str | None = None) -> str:
    marker = marker.strip()
    if not sub_id:
        return marker
    # If the user already configured marker with a SubID, keep it unchanged.
    if "." in marker:
        return marker
    return f"{marker}.{sanitize_sub_id(sub_id)}"
