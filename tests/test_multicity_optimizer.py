from datetime import date, datetime, timezone

from flight_finder.directories import Directory
from flight_finder.models import CityPoint, FlightOffer, MultiCityQuery
from flight_finder.travelpayouts_client import TravelpayoutsClient


class FakeClient(TravelpayoutsClient):
    def __init__(self, offers_by_pair):
        super().__init__(token="token", marker="123456")
        self._fake = offers_by_pair

    def _search_one_destination(self, query, destination_code, directory, limit):
        return self._fake.get((query.origin_code, destination_code), [])[:limit]


def offer(origin, dest, day, price):
    return FlightOffer(
        origin=origin,
        destination=dest,
        origin_label=origin,
        destination_label=dest,
        price=price,
        airline="TK",
        transfers=1,
        duration_minutes=180,
        departure_at=datetime(2026, 7, day, 10, 0, tzinfo=timezone.utc),
        link=f"https://example.com/{origin}-{dest}-{day}",
        score=price,
    )


def test_optimizer_finds_cheapest_order_not_input_order():
    # Input order is IST, SHA, BKK, but cheapest feasible route is LED→SHA→BKK→IST→LED.
    offers = {
        ("LED", "IST"): [offer("LED", "IST", 6, 50000)],
        ("LED", "SHA"): [offer("LED", "SHA", 6, 10000)],
        ("LED", "BKK"): [offer("LED", "BKK", 6, 30000)],
        ("SHA", "BKK"): [offer("SHA", "BKK", 9, 10000)],
        ("BKK", "IST"): [offer("BKK", "IST", 12, 10000)],
        ("IST", "LED"): [offer("IST", "LED", 15, 10000)],
        # Expensive alternatives to make other permutations worse.
        ("IST", "SHA"): [offer("IST", "SHA", 9, 50000)],
        ("IST", "BKK"): [offer("IST", "BKK", 9, 50000)],
        ("SHA", "IST"): [offer("SHA", "IST", 9, 50000)],
        ("BKK", "SHA"): [offer("BKK", "SHA", 12, 50000)],
        ("SHA", "LED"): [offer("SHA", "LED", 15, 50000)],
        ("BKK", "LED"): [offer("BKK", "LED", 15, 50000)],
    }
    query = MultiCityQuery(
        origin=CityPoint("Санкт-Петербург", "LED"),
        visit_cities=(CityPoint("Стамбул", "IST"), CityPoint("Шанхай", "SHA"), CityPoint("Бангкок", "BKK")),
        date_from=date(2026, 7, 6),
        date_to=date(2026, 7, 25),
        min_stay_days=1,
        max_stay_days=5,
    )
    routes = FakeClient(offers).optimize_multicity(query, Directory(), max_routes=1)
    assert routes
    assert routes[0].route_labels == ["Санкт-Петербург", "Шанхай", "Бангкок", "Стамбул", "Санкт-Петербург"]
    assert routes[0].total_price == 40000
