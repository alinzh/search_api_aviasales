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

    def __init__(
        self,
        token: str,
        marker: str | None = None,
        timeout_seconds: int = 15,
        session: requests.Session | None = None,
    ):
        self.token = token
        self.marker = marker
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def search(self, query: SearchQuery, directory: Directory, limit_per_destination: int = 10) -> list[FlightOffer]:
        if not self.token:
            raise RuntimeError("AVIASALES_TOKEN пустой. Укажи токен в .env")

        offers: list[FlightOffer] = []
        for destination_code in query.destination.codes:
            if destination_code == query.origin_code:
                continue
            offers.extend(self._search_one_destination(query, destination_code, directory, limit_per_destination))

        offers = self._dedupe(offers)
        offers.sort(key=lambda offer: offer.score)
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

        results.sort(key=lambda item: (item.score, item.total_price))
        return results[:limit_per_destination]

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

        offers_by_pair: dict[tuple[str, str], list[FlightOffer]] = {}
        for origin, destination in itertools.permutations(route_points, 2):
            pair_query = SearchQuery(
                origin_label=origin.label,
                origin_code=origin.code,
                destination=replace_destination(destination),
                date_from=query.date_from,
                date_to=query.date_to,
                # For multi-city, max_price means total budget, not per-leg budget.
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

        routes: list[MultiCityRoute] = []
        for order in itertools.permutations(query.visit_cities):
            if query.final_destination:
                sequence = (query.origin, *order, query.final_destination)
            elif query.return_to_origin:
                sequence = (query.origin, *order, query.origin)
            else:
                sequence = (query.origin, *order)
            best_for_order = self._best_route_for_sequence(
                sequence=sequence,
                offers_by_pair=offers_by_pair,
                query=query,
                beam_width=beam_width,
            )
            if best_for_order:
                routes.append(best_for_order)

        routes.sort(key=lambda route: route.score)
        return routes[:max_routes]

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
        for month in _months_between(query.date_from, query.date_to):
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
            response = self.session.get(self.API_URL, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            logger.info(
                "Travelpayouts %s→%s month=%s returned success=%s in %.2fs",
                query.origin_code,
                destination_code,
                month,
                payload.get("success"),
                time.time() - started,
            )
            if not payload.get("success"):
                continue
            raw_items = payload.get("data") or []
            for item in raw_items:
                offer = self._to_offer(item, query, destination_code, directory)
                if not offer:
                    continue
                if not self._passes_filters(offer, query):
                    continue
                offers.append(offer)
        offers = self._dedupe(offers)
        offers.sort(key=lambda offer: offer.score)
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
        link = self._build_ticket_link(raw_link, query, destination_code)
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
            raw=item,
        )
        offer.score = self._score(offer)
        return offer

    def _passes_filters(self, offer: FlightOffer, query: SearchQuery) -> bool:
        if query.max_price is not None and offer.price > query.max_price:
            return False
        if query.max_transfers is not None and offer.transfers > query.max_transfers:
            return False
        if query.max_duration_minutes is not None and offer.duration_minutes > query.max_duration_minutes:
            return False
        return True

    @staticmethod
    def _score(offer: FlightOffer) -> float:
        # Product ranking: price is primary, but awful routes should go lower.
        transfer_penalty = offer.transfers * 5_000
        duration_penalty = max(0, offer.duration_minutes - 5 * 60) * 30
        night_penalty = 2_000 if offer.departure_at and offer.departure_at.hour < 6 else 0
        return offer.price + transfer_penalty + duration_penalty + night_penalty

    def _build_ticket_link(self, raw_link: str, query: SearchQuery, destination_code: str) -> str:
        if not raw_link:
            raw_link = f"/search/{query.origin_code}{query.date_from:%d%m}{destination_code}1"
        if raw_link.startswith("/"):
            url = "https://www.aviasales.ru" + raw_link
        else:
            url = raw_link
        if not self.marker:
            return url

        # Travelpayouts/Aviasales manual links expect partner tracking in `marker`.
        # SubID is encoded as `<partner_id>.<sub_id>` for direct/White Label style URLs.
        # The Partner Links API also accepts a separate `sub_id`, but here we build
        # direct Aviasales URLs without calling that API.
        sub_id = sanitize_sub_id(
            f"tg_{query.mode.value}_{query.origin_code}_{destination_code}_{query.date_from:%Y%m%d}"
        )
        return add_query_params(url, {"marker": build_marker(self.marker, sub_id)})

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
