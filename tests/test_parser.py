from datetime import date

import pytest

from flight_finder.directories import Directory
from flight_finder.models import SearchMode
from flight_finder.quick_parser import ParseError, parse_search_query


def test_parse_china_discovery_query():
    query = parse_search_query(
        "из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч",
        directory=Directory(),
        today=date(2026, 7, 1),
        mode=SearchMode.DISCOVERY,
    )
    assert query.origin_code == "LED"
    assert query.destination.label == "Китай"
    assert "SHA" in query.destination.codes
    assert query.date_from == date(2026, 7, 6)
    assert query.date_to == date(2026, 7, 14)
    assert query.max_price == 70000
    assert query.max_transfers == 1
    assert query.max_duration_minutes == 18 * 60


def test_parse_direct_flight():
    query = parse_search_query(
        "из LED в Шанхай 01.09-10.09 без пересадок",
        directory=Directory(),
        today=date(2026, 7, 1),
    )
    assert query.origin_code == "LED"
    assert query.destination.codes == ("SHA",)
    assert query.max_transfers == 0


def test_unknown_destination():
    with pytest.raises(ParseError):
        parse_search_query("из СПб в Нарнию 06.07-14.07", directory=Directory(), today=date(2026, 7, 1))


def test_parse_roundtrip_china_query_single_range_means_trip_endpoints():
    query = parse_search_query(
        "из СПб в Китай и обратно 06.07-14.07 до 90000 до 1 пересадки",
        directory=Directory(),
        today=date(2026, 7, 1),
        mode=SearchMode.DISCOVERY,
    )
    assert query.origin_code == "LED"
    assert query.destination.label == "Китай"
    assert query.is_round_trip is True
    assert query.date_from == date(2026, 7, 6)
    assert query.date_to == date(2026, 7, 6)
    assert query.return_date_from == date(2026, 7, 14)
    assert query.return_date_to == date(2026, 7, 14)
    assert query.max_price == 90000
    assert query.max_transfers == 1


def test_parse_roundtrip_china_query_with_flexible_outbound_and_return_windows():
    query = parse_search_query(
        "из СПб в Китай туда 06.07-08.07 обратно 14.07-16.07 до 90000",
        directory=Directory(),
        today=date(2026, 7, 1),
        mode=SearchMode.DISCOVERY,
    )
    assert query.destination.label == "Китай"
    assert query.is_round_trip is True
    assert query.date_from == date(2026, 7, 6)
    assert query.date_to == date(2026, 7, 8)
    assert query.return_date_from == date(2026, 7, 14)
    assert query.return_date_to == date(2026, 7, 16)
