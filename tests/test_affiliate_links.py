from datetime import date
from unittest.mock import MagicMock, patch

from flight_finder.directories import Destination
from flight_finder.models import FlightOffer, SearchMode, SearchQuery
from flight_finder.travelpayouts_client import (
    TravelpayoutsClient,
    add_query_params,
    build_marker,
    sanitize_sub_id,
)


def _query() -> SearchQuery:
    return SearchQuery(
        origin_code="LED",
        origin_label="Санкт-Петербург",
        destination=Destination(label="Шанхай", codes=["SHA"]),
        date_from=date(2026, 7, 6),
        date_to=date(2026, 7, 14),
        mode=SearchMode.QUICK,
    )


def test_build_marker_adds_subid_with_dot():
    assert build_marker("123456", "tg_quick_led_sha_20260706") == "123456.tg_quick_led_sha_20260706"


def test_build_marker_preserves_existing_subid():
    assert build_marker("123456.custom", "ignored") == "123456.custom"


def test_sanitize_sub_id():
    assert sanitize_sub_id("TG Quick LED-SHA 2026/07/06") == "tg_quick_led_sha_2026_07_06"


def test_build_ticket_link_without_trs_uses_separate_marker_and_sub_id():
    client = TravelpayoutsClient(token="token", marker="123456")
    url, sub_id = client._build_ticket_link("/search/LED0607SHA1", _query(), "SHA")
    assert "marker=123456" in url
    assert "sub_id=tg_quick_led_sha_20260706" in url
    assert "marker=123456." not in url
    assert sub_id is None


def test_build_ticket_link_with_trs_returns_clean_url_and_sub_id():
    client = TravelpayoutsClient(token="token", marker="123456", trs=211747)
    url, sub_id = client._build_ticket_link("/search/LED0607SHA1", _query(), "SHA")
    assert url == "https://www.aviasales.ru/search/LED0607SHA1"
    assert "marker" not in url
    assert sub_id == "tg_quick_led_sha_20260706"


def test_build_ticket_link_without_marker_returns_plain_url():
    client = TravelpayoutsClient(token="token")
    url, sub_id = client._build_ticket_link("/search/LED0607SHA1", _query(), "SHA")
    assert url == "https://www.aviasales.ru/search/LED0607SHA1"
    assert sub_id is None


def _offer(link: str, sub_id: str | None = None) -> FlightOffer:
    raw: dict = {}
    if sub_id:
        raw["_sub_id"] = sub_id
    return FlightOffer(
        origin="LED",
        destination="SHA",
        origin_label="Санкт-Петербург",
        destination_label="Шанхай",
        price=10000,
        airline="SU",
        transfers=0,
        duration_minutes=120,
        departure_at=None,
        link=link,
        raw=raw,
    )


def test_create_partner_links_batches_and_maps_urls():
    client = TravelpayoutsClient(token="token", marker="123456", trs=211747)
    pairs = [
        ("https://www.aviasales.ru/search/A1", "tg_a"),
        ("https://www.aviasales.ru/search/B1", "tg_b"),
    ]

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "result": {
            "trs": 211747,
            "marker": 123456,
            "shorten": True,
            "links": [
                {
                    "url": "https://www.aviasales.ru/search/A1",
                    "code": "success",
                    "partner_url": "https://aviasales.tp.st/AAA",
                },
                {
                    "url": "https://www.aviasales.ru/search/B1",
                    "code": "success",
                    "partner_url": "https://aviasales.tp.st/BBB",
                },
            ],
        },
        "code": "success",
        "status": 200,
    }

    with patch.object(client.session, "post", return_value=fake_response) as mock_post:
        result = client._create_partner_links(pairs)

    assert result == {
        "https://www.aviasales.ru/search/A1": "https://aviasales.tp.st/AAA",
        "https://www.aviasales.ru/search/B1": "https://aviasales.tp.st/BBB",
    }
    mock_post.assert_called_once()
    body = mock_post.call_args.kwargs["json"]
    assert body["trs"] == 211747
    assert body["marker"] == 123456
    assert body["shorten"] is True
    assert body["links"] == [
        {"url": "https://www.aviasales.ru/search/A1", "sub_id": "tg_a"},
        {"url": "https://www.aviasales.ru/search/B1", "sub_id": "tg_b"},
    ]


def test_create_partner_links_without_trs_returns_empty():
    client = TravelpayoutsClient(token="token", marker="123456")
    result = client._create_partner_links([("https://example.com", "tg")])
    assert result == {}


def test_convert_links_to_partner_replaces_offer_links():
    client = TravelpayoutsClient(token="token", marker="123456", trs=211747)
    offers = [
        _offer("https://www.aviasales.ru/search/A1", "tg_a"),
        _offer("https://www.aviasales.ru/search/B1", "tg_b"),
    ]

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "result": {
            "trs": 211747,
            "marker": 123456,
            "shorten": True,
            "links": [
                {
                    "url": "https://www.aviasales.ru/search/A1",
                    "code": "success",
                    "partner_url": "https://aviasales.tp.st/AAA",
                },
                {
                    "url": "https://www.aviasales.ru/search/B1",
                    "code": "failed",
                    "partner_url": "",
                },
            ],
        },
        "code": "success",
        "status": 200,
    }

    with patch.object(client.session, "post", return_value=fake_response):
        client._convert_links_to_partner(offers)

    assert offers[0].link == "https://aviasales.tp.st/AAA"
    assert "marker=123456" in offers[1].link
    assert "sub_id=tg_b" in offers[1].link


def test_convert_links_to_partner_fallback_on_api_error():
    client = TravelpayoutsClient(token="token", marker="123456", trs=211747)
    offers = [_offer("https://www.aviasales.ru/search/A1", "tg_a")]

    with patch.object(client.session, "post", side_effect=Exception("network down")):
        client._convert_links_to_partner(offers)

    assert "marker=123456" in offers[0].link
    assert "sub_id=tg_a" in offers[0].link


def test_convert_links_to_partner_skips_offers_without_sub_id():
    client = TravelpayoutsClient(token="token", marker="123456", trs=211747)
    offers = [_offer("https://www.aviasales.ru/search/A1", sub_id=None)]
    with patch.object(client.session, "post") as mock_post:
        client._convert_links_to_partner(offers)
    mock_post.assert_not_called()
    assert offers[0].link == "https://www.aviasales.ru/search/A1"
