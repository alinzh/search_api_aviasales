from datetime import datetime, timezone

from flight_finder.directories import Directory
from flight_finder.models import FlightOffer
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
