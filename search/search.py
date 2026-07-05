from __future__ import annotations

from datetime import date

from flight_finder.config import Settings
from flight_finder.directories import Directory
from flight_finder.models import Destination, SearchMode, SearchQuery
from flight_finder.travelpayouts_client import TravelpayoutsClient


class Search:
    """Compatibility wrapper for the old `from search import Search` import.

    New code should use `flight_finder.travelpayouts_client.TravelpayoutsClient`.
    This wrapper exposes a small, product-oriented API for simple city/country
    discovery searches and keeps the old project import path alive.
    """

    def __init__(self, token: str | None = None, marker: str | None = None):
        settings = Settings.from_env()
        self.directory = Directory()
        self.client = TravelpayoutsClient(
            token=token or settings.aviasales_token,
            marker=marker or settings.travelpayouts_marker,
            timeout_seconds=settings.request_timeout_seconds,
        )
        self.settings = settings

    def search_destinations(
        self,
        origin: str,
        destination: str,
        date_from: date,
        date_to: date,
        max_price: int | None = None,
        max_transfers: int | None = None,
        max_duration_minutes: int | None = None,
        limit_per_destination: int = 10,
    ):
        origin_resolved = self.directory.resolve_city_code(origin)
        if not origin_resolved:
            raise ValueError(f"Unknown origin city: {origin}")
        origin_label, origin_code = origin_resolved
        destination_resolved = self.directory.resolve_destination(destination)
        if not destination_resolved:
            raise ValueError(f"Unknown destination: {destination}")
        query = SearchQuery(
            origin_label=origin_label,
            origin_code=origin_code,
            destination=destination_resolved,
            date_from=date_from,
            date_to=date_to,
            max_price=max_price,
            max_transfers=max_transfers,
            max_duration_minutes=max_duration_minutes,
            currency=self.settings.currency,
            market=self.settings.market,
            mode=SearchMode.DISCOVERY if len(destination_resolved.codes) > 1 else SearchMode.QUICK,
        )
        return self.client.search(query, self.directory, limit_per_destination=limit_per_destination)
