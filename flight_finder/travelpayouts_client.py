from __future__ import annotations

import logging
import time
from dataclasses import replace
from datetime import date, datetime
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from .directories import Directory
from .models import FlightOffer, SearchQuery

logger = logging.getLogger(__name__)


class TravelpayoutsClient:
    """Small client for Aviasales Data API.

    It uses cached Data API offers and adds UX filters/ranking locally.
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

    def _search_one_destination(
        self,
        query: SearchQuery,
        destination_code: str,
        directory: Directory,
        limit: int,
    ) -> list[FlightOffer]:
        params = {
            "origin": query.origin_code,
            "destination": destination_code,
            "departure_at": query.date_from.strftime("%Y-%m"),
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
            "Travelpayouts %s→%s returned success=%s in %.2fs",
            query.origin_code,
            destination_code,
            payload.get("success"),
            time.time() - started,
        )
        if not payload.get("success"):
            return []
        raw_items = payload.get("data") or []
        offers: list[FlightOffer] = []
        for item in raw_items:
            offer = self._to_offer(item, query, destination_code, directory)
            if not offer:
                continue
            if not self._passes_filters(offer, query):
                continue
            offers.append(offer)
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
        sub_id = f"tg_{query.mode.value}_{query.origin_code}_{destination_code}_{query.date_from:%Y%m%d}"
        return add_query_params(url, {"marker": self.marker, "sub_id": sub_id})

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


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


def add_query_params(url: str, params: dict[str, str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({k: v for k, v in params.items() if v})
    return urlunparse(parsed._replace(query=urlencode(query)))
