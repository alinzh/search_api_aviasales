from datetime import datetime, timezone

from flight_finder.directories import Directory
from flight_finder.formatters import offer_card
from flight_finder.models import FlightOffer


def test_offer_card_contains_main_fields():
    offer = FlightOffer(
        origin="LED",
        destination="SHA",
        origin_label="Санкт-Петербург",
        destination_label="Шанхай",
        price=42300,
        airline="TK",
        transfers=1,
        duration_minutes=820,
        departure_at=datetime(2026, 7, 6, 13, 40, tzinfo=timezone.utc),
        link="https://www.aviasales.ru/search/test",
    )
    card = offer_card(offer, Directory(), index=1)
    assert "Шанхай" in card
    assert "42 300 ₽" in card
    assert "1 пересадка" in card
    assert "13ч 40м" in card
