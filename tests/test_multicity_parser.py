from datetime import date

from flight_finder.directories import Directory
from flight_finder.quick_parser import parse_multicity_query


def test_parse_unordered_multicity_query():
    query = parse_multicity_query(
        "из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 по 2-4 дня до 120000 до 1 пересадки",
        directory=Directory(),
        today=date(2026, 7, 1),
    )
    assert query.origin.code == "LED"
    assert [city.code for city in query.visit_cities] == ["IST", "SHA", "BKK"]
    assert query.date_from == date(2026, 7, 6)
    assert query.date_to == date(2026, 7, 25)
    assert query.min_stay_days == 2
    assert query.max_stay_days == 4
    assert query.max_price == 120000
    assert query.max_transfers == 1
    assert query.return_to_origin is True


def test_parse_unordered_multicity_without_return():
    query = parse_multicity_query(
        "LED: IST, SHA, BKK 06.07-25.07 без возврата",
        directory=Directory(),
        today=date(2026, 7, 1),
    )
    assert query.origin.code == "LED"
    assert query.return_to_origin is False
