from datetime import datetime, timezone

from flight_finder.directories import Directory
from flight_finder.models import FlightOffer
from flight_finder.models import CityPoint, RoundTripOffer
from flight_finder.travelpayouts_client import TravelpayoutsClient


def make_offer(code: str, price: int) -> FlightOffer:
    return FlightOffer(
        origin="LED",
        destination=code,
        origin_label="Санкт-Петербург",
        destination_label=Directory().label_for_code(code),
        price=price,
        airline="TK",
        transfers=1,
        duration_minutes=600,
        departure_at=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc),
        link="https://example.com",
        score=float(price),
    )


def test_ideas_are_diversified_by_country_before_filling_same_country():
    directory = Directory()
    offers = [
        make_offer("BJS", 10000),  # China
        make_offer("SHA", 11000),  # China, should wait
        make_offer("BKK", 12000),  # Thailand
        make_offer("TAS", 13000),  # Uzbekistan
    ]
    selected = TravelpayoutsClient._diversify_ideas(offers, directory, max_results=3)
    assert [offer.destination for offer in selected] == ["BJS", "BKK", "TAS"]


def make_roundtrip(code: str, total_price: int) -> RoundTripOffer:
    outbound = make_offer(code, total_price // 2)
    inbound = FlightOffer(
        origin=code,
        destination="LED",
        origin_label=Directory().label_for_code(code),
        destination_label="Санкт-Петербург",
        price=total_price - total_price // 2,
        airline="TK",
        transfers=1,
        duration_minutes=600,
        departure_at=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
        link="https://example.com/back",
        score=float(total_price - total_price // 2),
    )
    return RoundTripOffer(
        destination=CityPoint(Directory().label_for_code(code), code),
        outbound=outbound,
        inbound=inbound,
        total_price=total_price,
        score=float(total_price),
    )


def test_roundtrip_ideas_are_diversified_by_country():
    directory = Directory()
    routes = [
        make_roundtrip("BJS", 20000),  # China
        make_roundtrip("SHA", 21000),  # China, should wait
        make_roundtrip("BKK", 22000),  # Thailand
        make_roundtrip("TAS", 23000),  # Uzbekistan
    ]
    selected = TravelpayoutsClient._diversify_roundtrip_ideas(routes, directory, max_results=3)
    assert [route.destination.code for route in selected] == ["BJS", "BKK", "TAS"]
