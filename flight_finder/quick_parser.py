from __future__ import annotations

import calendar
import re
from datetime import date

from .directories import Directory, normalize_name
from .models import CityPoint, Destination, MultiCityQuery, SearchMode, SearchQuery

_DATE_RANGE_RE = re.compile(
    r"(?P<d1>\d{1,2})[./-](?P<m1>\d{1,2})(?:[./-](?P<y1>\d{2,4}))?\s*(?:-|—|–|до|по|\.\.)\s*(?P<d2>\d{1,2})[./-](?P<m2>\d{1,2})(?:[./-](?P<y2>\d{2,4}))?",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(r"(?:до|<|≤|макс(?:имум)?\.?|не дороже)\s*(?P<value>\d+[\d\s]*(?:к|k)?)\s*(?:₽|р|руб|rub)?", re.IGNORECASE)
_TRANSFER_RE = re.compile(r"(?:(?:до|макс(?:имум)?\.?)\s*)?(?P<n>\d+)\s*пересад(?:ка|ки|ок)?", re.IGNORECASE)
_DURATION_RE = re.compile(r"(?:до|<|≤|макс(?:имум)?\.?)\s*(?P<h>\d{1,2})\s*(?:ч|час|часов|h)(?:\s*(?P<m>\d{1,2})\s*(?:м|мин|min))?", re.IGNORECASE)
_STAY_RE = re.compile(
    r"(?:по|в каждом городе|в городе|остановка|остановки|stay)\s*"
    r"(?P<min>\d{1,2})(?:\s*(?:-|—|–|до|по)\s*(?P<max>\d{1,2}))?\s*"
    r"(?:дней|дня|день|дн|days?)",
    re.IGNORECASE,
)
_ROUND_TRIP_RE = re.compile(
    r"\b(?:и\s+обратно|туда\s*[-–—]?\s*обратно|обратно|назад|return|round\s*trip)\b",
    re.IGNORECASE,
)

_MONTH_ALIASES = {
    "январь": 1, "январе": 1, "января": 1,
    "февраль": 2, "феврале": 2, "февраля": 2,
    "март": 3, "марте": 3, "марта": 3,
    "апрель": 4, "апреле": 4, "апреля": 4,
    "май": 5, "мае": 5, "мая": 5,
    "июнь": 6, "июне": 6, "июня": 6,
    "июль": 7, "июле": 7, "июля": 7,
    "август": 8, "августе": 8, "августа": 8,
    "сентябрь": 9, "сентябре": 9, "сентября": 9,
    "октябрь": 10, "октябре": 10, "октября": 10,
    "ноябрь": 11, "ноябре": 11, "ноября": 11,
    "декабрь": 12, "декабре": 12, "декабря": 12,
}
_MONTH_PERIOD_RE = re.compile(
    r"(?:\bв\s+|\bна\s+)?(?P<month>январ[ьяе]|феврал[ьяе]|март[ае]?|апрел[ьяе]|ма[йяе]|июн[ьяе]|июл[ьяе]|август[ае]?|сентябр[ьяе]|октябр[ьяе]|ноябр[ьяе]|декабр[ьяе])(?:\s+(?P<year>\d{4}))?",
    re.IGNORECASE,
)


class ParseError(ValueError):
    pass


def _year(value: str | None, default: int) -> int:
    if not value:
        return default
    y = int(value)
    if y < 100:
        return 2000 + y
    return y




def _dates_from_match(match: re.Match[str], today: date) -> tuple[date, date]:
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
        first = date(first.year + 1, first.month, first.day)
        second = date(second.year + 1, second.month, second.day)
    return first, second


def _remove_spans(text: str, spans: list[tuple[int, int]]) -> str:
    cleaned = text
    for start, end in sorted(spans, reverse=True):
        cleaned = cleaned[:start] + " " + cleaned[end:]
    return cleaned


def _parse_roundtrip_dates(text: str, today: date | None = None) -> tuple[bool, date, date, date | None, date | None, str]:
    """Parse one-way or round-trip dates.

    Normal one-way/discovery semantics keep the old behavior: a single date range
    is a departure window. If the text contains `и обратно`/`туда-обратно`, the
    same single range becomes trip endpoints: outbound on the first date, return
    on the second date. For flexible round-trip windows, users can give two ranges:
    `туда 06.07-08.07 обратно 14.07-16.07`.
    """
    today = today or date.today()
    is_round_trip = bool(_ROUND_TRIP_RE.search(text))
    matches = list(_DATE_RANGE_RE.finditer(text))
    if not matches:
        raise ParseError("Не нашел диапазон дат. Пример: 06.07-14.07")

    if is_round_trip and len(matches) >= 2:
        out_from, out_to = _dates_from_match(matches[0], today)
        ret_from, ret_to = _dates_from_match(matches[1], today)
        if ret_from < out_from:
            raise ParseError("Дата обратного вылета раньше даты вылета туда.")
        cleaned = _remove_spans(text, [(matches[0].start(), matches[0].end()), (matches[1].start(), matches[1].end())])
        cleaned = _strip_roundtrip_markers(cleaned)
        return True, out_from, out_to, ret_from, ret_to, cleaned

    first, second = _dates_from_match(matches[0], today)
    cleaned = text[: matches[0].start()] + " " + text[matches[0].end() :]
    if is_round_trip:
        # `из СПб в Китай и обратно 06.07-14.07` means depart on 06.07 and return on 14.07.
        cleaned = _strip_roundtrip_markers(cleaned)
        return True, first, first, second, second, cleaned
    return False, first, second, None, None, cleaned


def _strip_roundtrip_markers(text: str) -> str:
    text = _ROUND_TRIP_RE.sub(" ", text)
    text = re.sub(r"\b(?:туда|вылет|обратный\s+вылет|возврат)\b", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())

def _parse_date_range(text: str, today: date | None = None) -> tuple[date, date, str]:
    today = today or date.today()
    match = _DATE_RANGE_RE.search(text)
    if not match:
        raise ParseError("Не нашел диапазон дат. Пример: 06.07-14.07")
    first, second = _dates_from_match(match, today)
    return first, second, text[: match.start()] + " " + text[match.end() :]


def _parse_period(text: str, today: date | None = None) -> tuple[date, date, str]:
    """Parse exact date range or a fuzzy month like `в августе`."""
    today = today or date.today()
    match = _DATE_RANGE_RE.search(text)
    if match:
        first, second = _dates_from_match(match, today)
        return first, second, text[: match.start()] + " " + text[match.end() :]

    month_match = _MONTH_PERIOD_RE.search(text)
    if not month_match:
        raise ParseError("Не нашел период. Пример: 06.07-14.07 или в августе")
    month_word = normalize_name(month_match.group("month"))
    month = _MONTH_ALIASES.get(month_word)
    if not month:
        raise ParseError("Не понял месяц. Пример: в августе")
    year = int(month_match.group("year") or today.year)
    if date(year, month, 1) < date(today.year, today.month, 1) and not month_match.group("year"):
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day), text[: month_match.start()] + " " + text[month_match.end() :]


def _parse_ideas_dates(text: str, today: date | None = None) -> tuple[bool, date, date, date | None, date | None, str]:
    """Parse date semantics for open-ended ideas search.

    Ideas mode accepts both one-way and round-trip wording:
    - `из СПб куда угодно в июле до 50000` -> one-way offers in July.
    - `из СПб куда угодно в июле до 50000 и обратно` -> round-trip offers fully inside July.
    - `из СПб куда угодно 06.07-14.07 до 50000 и обратно` -> outbound 06.07, return 14.07.
    - `из СПб куда угодно туда 06.07-08.07 обратно 14.07-16.07 до 50000` -> flexible windows.

    This keeps `и обратно` out of origin/destination extraction and prevents the
    discovery mode from silently returning one-way tickets for a round-trip query.
    """
    today = today or date.today()
    is_round_trip = bool(_ROUND_TRIP_RE.search(text))

    if is_round_trip:
        date_matches = list(_DATE_RANGE_RE.finditer(text))
        if date_matches:
            return _parse_roundtrip_dates(text, today=today)

        # Fuzzy month + round-trip: both outbound and return are flexible inside
        # the same month. Pairing later rejects return legs before the outbound.
        date_from, date_to, cleaned = _parse_period(text, today=today)
        cleaned = _strip_roundtrip_markers(cleaned)
        return True, date_from, date_to, date_from, date_to, cleaned

    date_from, date_to, cleaned = _parse_period(text, today=today)
    return False, date_from, date_to, None, None, cleaned


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


def _parse_stay(text: str) -> tuple[int, int | None, str]:
    match = _STAY_RE.search(text)
    if not match:
        return 1, 7, text
    min_days = int(match.group("min"))
    max_days = int(match.group("max") or min_days)
    if max_days < min_days:
        raise ParseError("Максимум дней в городе меньше минимума.")
    cleaned = text[: match.start()] + " " + text[match.end() :]
    return min_days, max_days, cleaned


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

    is_round_trip, date_from, date_to, return_date_from, return_date_to, cleaned = _parse_roundtrip_dates(original, today=today)
    max_price, cleaned = _parse_price(cleaned)
    max_transfers, cleaned = _parse_transfers(cleaned)
    max_duration, cleaned = _parse_duration(cleaned)
    cleaned = re.sub(r"\b(билет|билеты|маршрут|найди|покажи|улететь|можно|рейсы|туда|обратно)\b", " ", cleaned, flags=re.IGNORECASE)
    origin_text, dest_text = _extract_route(cleaned)

    origin = directory.resolve_city_code(origin_text)
    if not origin:
        raise ParseError(f"Не знаю город отправления: {origin_text!r}. Добавь alias в data/city2code.json.")
    origin_label, origin_code = origin

    destination: Destination | None = directory.resolve_destination(dest_text)
    if not destination:
        raise ParseError(f"Не знаю направление: {dest_text!r}. Добавь город или страну в data/*.json.")

    if is_round_trip and not (return_date_from and return_date_to):
        raise ParseError("Для туда-обратно укажи даты: например, 06.07-14.07 или туда 06.07-08.07 обратно 14.07-16.07")

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
        mode=SearchMode.ROUND_TRIP if is_round_trip else mode,
        raw_text=original,
        return_to_origin=is_round_trip,
        return_date_from=return_date_from,
        return_date_to=return_date_to,
    )


def parse_ideas_query(
    text: str,
    directory: Directory | None = None,
    today: date | None = None,
    currency: str = "rub",
    market: str = "ru",
) -> SearchQuery:
    """Parse open-ended travel ideas query.

    The user gives origin, approximate period and budget, but no destination.
    Examples:
    - из СПб куда угодно в августе до 50000
    - куда слетать из Москвы 10.08-20.08 до 60000
    - идеи из LED в июле до 40000 до 1 пересадки
    """
    directory = directory or Directory()
    original = text.strip()
    if not original:
        raise ParseError("Пустой запрос идей.")

    is_round_trip, date_from, date_to, return_date_from, return_date_to, cleaned = _parse_ideas_dates(original, today=today)
    max_price, cleaned = _parse_price(cleaned)
    if max_price is None:
        raise ParseError("Для режима идей нужен бюджет. Пример: из СПб куда угодно в августе до 50000")
    max_transfers, cleaned = _parse_transfers(cleaned)
    max_duration, cleaned = _parse_duration(cleaned)

    origin_text = _extract_ideas_origin(cleaned)
    origin = directory.resolve_city_code(origin_text)
    if not origin:
        raise ParseError(f"Не знаю город отправления: {origin_text!r}. Добавь alias в data/city2code.json.")
    origin_label, origin_code = origin

    codes = tuple(code for code in directory.idea_destination_codes() if code != origin_code)
    if not codes:
        raise ParseError("Нет направлений для режима идей. Добавь города в data/idea_destinations.json.")

    return SearchQuery(
        origin_label=origin_label,
        origin_code=origin_code,
        destination=Destination(label="куда угодно", codes=codes, kind="ideas"),
        date_from=date_from,
        date_to=date_to,
        max_price=max_price,
        max_transfers=max_transfers,
        max_duration_minutes=max_duration,
        currency=currency,
        market=market,
        mode=SearchMode.IDEAS,
        raw_text=original,
        return_to_origin=is_round_trip,
        return_date_from=return_date_from,
        return_date_to=return_date_to,
    )


def _extract_ideas_origin(text: str) -> str:
    # First try to capture the city right after `из/с/от` and before idea words.
    direct = re.search(
        r"(?:^|\s)(?:из|с|от)\s+(?P<origin>.+?)(?:\s+(?:куда(?:-нибудь|\s+угодно)?|идеи|варианты|подборка|съездить|слетать|улететь|полететь|отпуск|уикенд)\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    if direct:
        origin = direct.group("origin").strip(" ,.;:-")
        if origin:
            return origin

    cleaned = re.sub(
        r"\b(куда\s+угодно|куда-нибудь|идеи|варианты|подборка|куда|угодно|съездить|слетать|улететь|полететь|отпуск|уикенд|на\s+выходные|можно|билеты|найди|подбери|покажи)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    cleaned = " ".join(cleaned.split())
    patterns = [
        r"(?:^|\s)(?:из|с|от)\s+(?P<origin>.+)$",
        r"^(?P<origin>[A-Za-zА-Яа-яЁё\- ]{2,30})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            origin = match.group("origin").strip(" ,.;:-")
            origin = re.split(r"\s+(?:до|макс|без|прям)", origin, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            if origin:
                return origin
    raise ParseError("Не понял город отправления. Пример: из СПб куда угодно в августе до 50000")


def parse_multicity_query(
    text: str,
    directory: Directory | None = None,
    today: date | None = None,
    currency: str = "rub",
    market: str = "ru",
) -> MultiCityQuery:
    """Parse the unique product flow: unordered list of cities to visit.

    Examples:
    - из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 по 2-4 дня до 120000
    - из СПб в Сидней посетить Ханой, Бангкок, Куала-Лумпур 06.07-25.07 по 2-4 дня
    - из СПб до Сиднея через Вьетнам, Таиланд 06.07-25.07
    - СПб: Стамбул, Шанхай, Бангкок 06.07-25.07
    - из LED через IST, SHA, BKK 06.07-25.07 без возврата
    """
    directory = directory or Directory()
    original = text.strip()
    if not original:
        raise ParseError("Пустой multi-city запрос.")

    date_from, date_to, cleaned = _parse_date_range(original, today=today)
    max_price, cleaned = _parse_price(cleaned)
    max_transfers, cleaned = _parse_transfers(cleaned)
    max_duration, cleaned = _parse_duration(cleaned)
    min_stay, max_stay, cleaned = _parse_stay(cleaned)

    explicit_no_return = bool(re.search(r"без\s+возврата|в\s+одну\s+сторону|не\s+возвращ", cleaned, flags=re.IGNORECASE))
    return_to_origin = not explicit_no_return
    cleaned = re.sub(r"без\s+возврата|в\s+одну\s+сторону|не\s+возвращ\w*", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(хочу|надо|нужно|маршрут|найди|подбери|самый|дешевый|дешевый|порядок|города|городов)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())

    origin_text, final_text, cities_text = _extract_multicity_origin_final_and_cities(cleaned)
    origin = directory.resolve_city_code(origin_text)
    if not origin:
        raise ParseError(f"Не знаю стартовый город: {origin_text!r}. Добавь alias в data/city2code.json.")
    origin_label, origin_code = origin
    origin_point = CityPoint(origin_label, origin_code)

    final_destination: CityPoint | None = None
    if final_text:
        final_destination = _resolve_multicity_point(final_text, directory)
        if not final_destination:
            raise ParseError(f"Не знаю конечный город: {final_text!r}. Добавь alias в data/city2code.json.")
        # Fixed finish changes the route shape from origin→permutation→origin
        # to origin→permutation→final_destination.
        return_to_origin = False

    city_tokens = _split_city_list(cities_text)
    min_stopovers = 1 if final_destination else 2
    if len(city_tokens) < min_stopovers:
        raise ParseError(
            "Для multi-city с конечным городом нужен минимум 1 промежуточный город; "
            "без конечного города — минимум 2 города для подбора порядка. "
            "Пример: из СПб в Сидней посетить Ханой, Бангкок 06.07-25.07"
        )

    seen_codes = {origin_code}
    if final_destination:
        seen_codes.add(final_destination.code)
    visit_cities: list[CityPoint] = []
    unknown: list[str] = []
    for token in city_tokens:
        city = _resolve_multicity_point(token, directory)
        if not city:
            unknown.append(token)
            continue
        if city.code in seen_codes:
            continue
        seen_codes.add(city.code)
        visit_cities.append(city)

    if unknown:
        raise ParseError(f"Не знаю города/страны: {', '.join(unknown)}. Добавь aliases в data/city2code.json или data/countries.json.")
    if len(visit_cities) < min_stopovers:
        raise ParseError("После удаления дублей осталось слишком мало промежуточных городов.")
    if len(visit_cities) > 7:
        raise ParseError("Пока ограничил unordered multi-city до 7 промежуточных городов: иначе слишком много API-запросов и перестановок.")

    return MultiCityQuery(
        origin=origin_point,
        visit_cities=tuple(visit_cities),
        date_from=date_from,
        date_to=date_to,
        final_destination=final_destination,
        min_stay_days=min_stay,
        max_stay_days=max_stay,
        return_to_origin=return_to_origin,
        max_price=max_price,
        max_transfers=max_transfers,
        max_duration_minutes=max_duration,
        currency=currency,
        market=market,
        raw_text=original,
    )


def _extract_multicity_origin_final_and_cities(text: str) -> tuple[str, str | None, str]:
    """Extract origin, optional fixed finish, and unordered stopovers."""
    with_finish_patterns = [
        r"(?:^|\s)из\s+(?P<origin>.+?)\s+(?:в|до)\s+(?P<final>.+?)\s+(?:по\s+пути\s+)?(?:посетить|через|с\s+посещением|заехать\s+в|побывать\s+в)\s+(?P<cities>.+)$",
        r"(?:^|\s)из\s+(?P<origin>.+?)\s+(?:через|с\s+посещением)\s+(?P<cities>.+?)\s+(?:в|до)\s+(?P<final>.+)$",
    ]
    for pattern in with_finish_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group("origin").strip(), match.group("final").strip(), match.group("cities").strip()

    patterns = [
        r"(?:^|\s)из\s+(?P<origin>.+?)\s+(?:посетить|через|по)\s+(?P<cities>.+)$",
        r"(?P<origin>.+?)\s*:\s*(?P<cities>.+)$",
        r"(?P<origin>.+?)\s*(?:->|→)\s*(?P<cities>.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group("origin").strip(), None, match.group("cities").strip()
    raise ParseError(
        "Не понял multi-city формат. Примеры: "
        "из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 или "
        "из СПб в Сидней посетить Ханой, Бангкок 06.07-25.07"
    )


def _resolve_multicity_point(value: str, directory: Directory) -> CityPoint | None:
    """Resolve a stopover to a concrete city code.

    If the user types a country like `Вьетнам` or `Таиланд`, use the first
    configured city from data/countries.json as a default stopover city.
    """
    city = directory.resolve_city_code(value)
    if city:
        label, code = city
        return CityPoint(label, code)
    destination = directory.resolve_destination(value)
    if destination and destination.codes:
        code = destination.codes[0]
        return CityPoint(directory.label_for_code(code), code)
    return None

def _split_city_list(value: str) -> list[str]:
    value = re.sub(r"\b(посетить|через|побывать|заехать|и)\b", " ", value, flags=re.IGNORECASE)
    parts = re.split(r"\s*(?:,|;|/|\+|->|→|\s+и\s+)\s*", value, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]


def parse_multicity_points(text: str, directory: Directory | None = None) -> list[tuple[str, str]]:
    """Backward-compatible helper for old code/tests.

    It only returns recognized city points and does not imply that the order is fixed.
    """
    directory = directory or Directory()
    parts = re.split(r"\s*(?:,|;|/|\+|->|→|—|-)\s*", normalize_name(text))
    result: list[tuple[str, str]] = []
    for part in parts:
        city = directory.resolve_city_code(part)
        if city:
            result.append(city)
    return result
