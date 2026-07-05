from datetime import date

from flight_finder.directories import Destination
from flight_finder.models import SearchMode, SearchQuery
from flight_finder.travelpayouts_client import build_marker, sanitize_sub_id, TravelpayoutsClient


def test_build_marker_adds_subid_with_dot():
    assert build_marker("123456", "tg_quick_led_sha_20260706") == "123456.tg_quick_led_sha_20260706"


def test_build_marker_preserves_existing_subid():
    assert build_marker("123456.custom", "ignored") == "123456.custom"


def test_sanitize_sub_id():
    assert sanitize_sub_id("TG Quick LED-SHA 2026/07/06") == "tg_quick_led_sha_2026_07_06"


def test_ticket_link_uses_marker_dot_subid():
    query = SearchQuery(
        origin_code="LED",
        origin_label="Санкт-Петербург",
        destination=Destination(label="Шанхай", codes=["SHA"]),
        date_from=date(2026, 7, 6),
        date_to=date(2026, 7, 14),
        mode=SearchMode.QUICK,
    )
    client = TravelpayoutsClient(token="token", marker="123456")
    link = client._build_ticket_link("/search/LED0607SHA1", query, "SHA")
    assert "marker=123456.tg_quick_led_sha_20260706" in link
    assert "sub_id=" not in link
