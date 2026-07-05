from datetime import date, datetime, timezone

from flight_finder.directories import Directory
from flight_finder.models import FlightOffer, SearchMode
from flight_finder.quick_parser import parse_search_query
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


def test_roundtrip_search_combines_outbound_and_return_legs():
    query = parse_search_query(
        "из LED в SHA и обратно 06.07-14.07 до 90000",
        directory=Directory(),
        today=date(2026, 7, 1),
        mode=SearchMode.DISCOVERY,
    )
    routes = FakeClient(
        {
            ("LED", "SHA"): [offer("LED", "SHA", 6, 30000)],
            ("SHA", "LED"): [offer("SHA", "LED", 14, 31000)],
        }
    ).search_round_trip(query, Directory())
    assert len(routes) == 1
    assert routes[0].destination.code == "SHA"
    assert routes[0].total_price == 61000
