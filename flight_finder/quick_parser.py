from __future__ import annotations

import re
from datetime import date

from .directories import Directory, normalize_name
from .models import Destination, SearchMode, SearchQuery

_DATE_RANGE_RE = re.compile(
    r"(?P<d1>\d{1,2})[./-](?P<m1>\d{1,2})(?:[./-](?P<y1>\d{2,4}))?\s*(?:-|—|–|до|по|\.\.)\s*(?P<d2>\d{1,2})[./-](?P<m2>\d{1,2})(?:[./-](?P<y2>\d{2,4}))?",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(r"(?:до|<|≤|макс(?:имум)?\.?|не дороже)\s*(?P<value>\d+[\d\s]*(?:к|k)?)\s*(?:₽|р|руб|rub)?", re.IGNORECASE)
_TRANSFER_RE = re.compile(r"(?:(?:до|макс(?:имум)?\.?)\s*)?(?P<n>\d+)\s*пересад(?:ка|ки|ок)?", re.IGNORECASE)
_DURATION_RE = re.compile(r"(?:до|<|≤|макс(?:имум)?\.?)\s*(?P<h>\d{1,2})\s*(?:ч|час|часов|h)(?:\s*(?P<m>\d{1,2})\s*(?:м|мин|min))?", re.IGNORECASE)


class ParseError(ValueError):
    pass


def _year(value: str | None, default: int) -> int:
    if not value:
        return default
    y = int(value)
    if y < 100:
        return 2000 + y
    return y


def _parse_date_range(text: str, today: date | None = None) -> tuple[date, date, str]:
    today = today or date.today()
    match = _DATE_RANGE_RE.search(text)
    if not match:
        raise ParseError("Не нашёл диапазон дат. Пример: 06.07-14.07")
    year1 = _year(match.group("y1"), today.year)
    year2 = _year(match.group("y2"), year1)
    first = date(year1, int(match.group("m1")), int(match.group("d1")))
    second = date(year2, int(match.group("m2")), int(match.group("d2")))
    if second < first:
        if not match.group("y2"):
            second = date(year2 + 1, second.month, second.day)
        else:
            raise ParseError("Дата окончания раньше даты начала.")
    if first < today and not match.group("y1"):
        # UX-friendly behavior around New Year: if user omitted year and the date is already gone,
        # assume next year instead of silently searching in the past.
        first = date(first.year + 1, first.month, first.day)
        second = date(second.year + 1, second.month, second.day)
    return first, second, text[: match.start()] + " " + text[match.end() :]


def _parse_price(text: str) -> tuple[int | None, str]:
    match = _PRICE_RE.search(text)
    if not match:
        return None, text
    raw = match.group("value").replace(" ", "").lower()
    if raw.endswith(("к", "k")):
        value = int(raw[:-1]) * 1000
    else:
        value = int(raw)
    return value, text[: match.start()] + " " + text[match.end() :]


def _parse_transfers(text: str) -> tuple[int | None, str]:
    lower = text.lower()
    if "без пересад" in lower or "прям" in lower:
        cleaned = re.sub(r"без\s+пересад\w*|прям\w*", " ", text, flags=re.IGNORECASE)
        return 0, cleaned
    match = _TRANSFER_RE.search(text)
    if not match:
        return None, text
    return int(match.group("n")), text[: match.start()] + " " + text[match.end() :]


def _parse_duration(text: str) -> tuple[int | None, str]:
    match = _DURATION_RE.search(text)
    if not match:
        return None, text
    minutes = int(match.group("h")) * 60 + int(match.group("m") or 0)
    return minutes, text[: match.start()] + " " + text[match.end() :]


def _extract_route(text: str) -> tuple[str, str]:
    text = " ".join(text.split())
    # Supports: "из СПб в Китай", "СПб -> Китай", "LED China"
    patterns = [
        r"(?:^|\s)из\s+(?P<origin>.+?)\s+(?:в|на)\s+(?P<dest>.+)$",
        r"(?P<origin>.+?)\s*(?:->|→)\s*(?P<dest>.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group("origin").strip(), match.group("dest").strip()
    words = text.split()
    if len(words) >= 2:
        return words[0], " ".join(words[1:])
    raise ParseError("Не понял маршрут. Пример: из СПб в Китай 06.07-14.07")


def parse_search_query(
    text: str,
    directory: Directory | None = None,
    today: date | None = None,
    currency: str = "rub",
    market: str = "ru",
    mode: SearchMode = SearchMode.QUICK,
) -> SearchQuery:
    directory = directory or Directory()
    original = text.strip()
    if not original:
        raise ParseError("Пустой запрос.")

    date_from, date_to, cleaned = _parse_date_range(original, today=today)
    max_price, cleaned = _parse_price(cleaned)
    max_transfers, cleaned = _parse_transfers(cleaned)
    max_duration, cleaned = _parse_duration(cleaned)
    cleaned = re.sub(r"\b(билет|билеты|маршрут|найди|покажи|улететь|можно|рейсы)\b", " ", cleaned, flags=re.IGNORECASE)
    origin_text, dest_text = _extract_route(cleaned)

    origin = directory.resolve_city_code(origin_text)
    if not origin:
        raise ParseError(f"Не знаю город отправления: {origin_text!r}. Добавь alias в data/city2code.json.")
    origin_label, origin_code = origin

    destination: Destination | None = directory.resolve_destination(dest_text)
    if not destination:
        raise ParseError(f"Не знаю направление: {dest_text!r}. Добавь город или страну в data/*.json.")

    return SearchQuery(
        origin_label=origin_label,
        origin_code=origin_code,
        destination=destination,
        date_from=date_from,
        date_to=date_to,
        max_price=max_price,
        max_transfers=max_transfers,
        max_duration_minutes=max_duration,
        currency=currency,
        market=market,
        mode=mode,
        raw_text=original,
    )


def parse_multicity_points(text: str, directory: Directory | None = None) -> list[tuple[str, str]]:
    """Parse only city points from "СПб -> Стамбул -> Шанхай".

    Dates for legs are intentionally not inferred here; the bot uses this to
    show a better error/help message and to prepare future multi-city UI.
    """
    directory = directory or Directory()
    parts = re.split(r"\s*(?:->|→|—|-)\s*", normalize_name(text))
    result: list[tuple[str, str]] = []
    for part in parts:
        city = directory.resolve_city_code(part)
        if city:
            result.append(city)
    return result
