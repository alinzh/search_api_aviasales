from datetime import date

import pytest

from flight_finder.directories import Directory
from flight_finder.models import SearchMode
from flight_finder.quick_parser import ParseError, parse_ideas_query


def test_parse_ideas_query_with_month_period():
    query = parse_ideas_query(
        "из СПб куда угодно в августе до 50000",
        directory=Directory(),
        today=date(2026, 7, 5),
    )
    assert query.mode == SearchMode.IDEAS
    assert query.origin_code == "LED"
    assert query.destination.kind == "ideas"
    assert query.date_from == date(2026, 8, 1)
    assert query.date_to == date(2026, 8, 31)
    assert query.max_price == 50000
    assert "BKK" in query.destination.codes


def test_parse_ideas_query_with_natural_order_and_date_range():
    query = parse_ideas_query(
        "куда слетать из Москвы 10.08-20.08 до 60000",
        directory=Directory(),
        today=date(2026, 7, 5),
    )
    assert query.origin_code == "MOW"
    assert query.date_from == date(2026, 8, 10)
    assert query.date_to == date(2026, 8, 20)
    assert query.max_price == 60000


def test_ideas_query_requires_budget():
    with pytest.raises(ParseError):
        parse_ideas_query("из СПб куда угодно в августе", directory=Directory(), today=date(2026, 7, 5))
