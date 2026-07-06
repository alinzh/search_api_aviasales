from __future__ import annotations

from datetime import date

from flight_finder.config import Settings
from flight_finder.directories import Directory
from flight_finder.models import CityPoint, Destination, MultiCityQuery, SearchMode, SearchQuery
from flight_finder.travelpayouts_client import TravelpayoutsClient


class Search:
    """Compatibility wrapper for the old `from search import Search` import.

    New code should use `flight_finder.travelpayouts_client.TravelpayoutsClient`.
    This wrapper keeps the original project idea alive: unordered multi-city route
    optimization, where the user gives cities to visit and the algorithm chooses
    the cheapest order.
    """

    def __init__(self, token: str | None = None, marker: str | None = None):
        settings = Settings.from_env()
        self.directory = Directory()
        self.client = TravelpayoutsClient(
            token=token or settings.aviasales_token,
            marker=marker or settings.travelpayouts_marker,
            trs=settings.travelpayouts_trs,
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

    def optimize_multicity(
        self,
        origin: str,
        cities: list[str],
        date_from: date,
        date_to: date,
        final_destination: str | None = None,
        min_stay_days: int = 1,
        max_stay_days: int | None = 7,
        return_to_origin: bool = True,
        max_price: int | None = None,
        max_transfers: int | None = None,
        max_duration_minutes: int | None = None,
        max_routes: int = 5,
    ):
        origin_resolved = self.directory.resolve_city_code(origin)
        if not origin_resolved:
            raise ValueError(f"Unknown origin city: {origin}")
        origin_label, origin_code = origin_resolved
        final_point: CityPoint | None = None
        if final_destination:
            final_resolved = self.directory.resolve_city_code(final_destination)
            if not final_resolved:
                raise ValueError(f"Unknown final destination city: {final_destination}")
            final_label, final_code = final_resolved
            final_point = CityPoint(final_label, final_code)
            return_to_origin = False

        points: list[CityPoint] = []
        seen = {origin_code}
        if final_point:
            seen.add(final_point.code)
        for city_name in cities:
            city = self.directory.resolve_city_code(city_name)
            if not city:
                raise ValueError(f"Unknown city: {city_name}")
            label, code = city
            if code in seen:
                continue
            seen.add(code)
            points.append(CityPoint(label, code))
        query = MultiCityQuery(
            origin=CityPoint(origin_label, origin_code),
            visit_cities=tuple(points),
            date_from=date_from,
            date_to=date_to,
            final_destination=final_point,
            min_stay_days=min_stay_days,
            max_stay_days=max_stay_days,
            return_to_origin=return_to_origin,
            max_price=max_price,
            max_transfers=max_transfers,
            max_duration_minutes=max_duration_minutes,
            currency=self.settings.currency,
            market=self.settings.market,
        )
        return self.client.optimize_multicity(query, self.directory, max_routes=max_routes)
