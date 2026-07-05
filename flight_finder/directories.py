from __future__ import annotations

import json
import re
from functools import cached_property
from pathlib import Path

from .models import Destination


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def normalize_name(value: str) -> str:
    value = value.strip().lower().replace("ё", "е")
    value = re.sub(r"[\s_\-]+", " ", value)
    return value


class Directory:
    """Small local directory for UX-friendly city/country names.

    The bundled dataset intentionally covers the most likely MVP markets.
    Add more aliases to data/city2code.json and data/countries.json without
    touching bot logic.
    """

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    @cached_property
    def city2code(self) -> dict[str, str]:
        with open(self.data_dir / "city2code.json", encoding="utf-8") as f:
            raw = json.load(f)
        return {normalize_name(k): v.upper() for k, v in raw.items()}

    @cached_property
    def code2city(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for name, code in self.city2code.items():
            result.setdefault(code, name.title())
        preferred = {
            "LED": "Санкт-Петербург",
            "MOW": "Москва",
            "BJS": "Пекин",
            "SHA": "Шанхай",
            "CAN": "Гуанчжоу",
            "SZX": "Шэньчжэнь",
            "HGH": "Ханчжоу",
            "CTU": "Чэнду",
            "CKG": "Чунцин",
            "TAO": "Циндао",
            "SIA": "Сиань",
            "XMN": "Сямэнь",
            "KMG": "Куньмин",
            "URC": "Урумчи",
            "HKG": "Гонконг",
            "MFM": "Макао",
            "BKK": "Бангкок",
            "HKT": "Пхукет",
            "SGN": "Хошимин",
            "HAN": "Ханой",
            "IST": "Стамбул",
            "DXB": "Дубай",
            "AUH": "Абу-Даби",
            "DOH": "Доха",
            "TAS": "Ташкент",
            "ALA": "Алматы",
            "NQZ": "Астана",
            "EVN": "Ереван",
            "TBS": "Тбилиси",
            "BAK": "Баку",
            "KUL": "Куала-Лумпур",
            "SIN": "Сингапур",
            "TYO": "Токио",
            "ICN": "Сеул",
            "DAD": "Дананг",
            "CNX": "Чиангмай",
            "AYT": "Анталья",
        }
        result.update(preferred)
        return result

    @cached_property
    def countries(self) -> dict[str, Destination]:
        with open(self.data_dir / "countries.json", encoding="utf-8") as f:
            raw = json.load(f)
        result: dict[str, Destination] = {}
        for alias, payload in raw.items():
            result[normalize_name(alias)] = Destination(
                label=payload["label"],
                codes=tuple(code.upper() for code in payload["codes"]),
                kind="country" if alias != "азия" else "region",
            )
        return result

    @cached_property
    def airlines(self) -> dict[str, str]:
        with open(self.data_dir / "airlines.json", encoding="utf-8") as f:
            return json.load(f)

    @cached_property
    def idea_destinations(self) -> dict[str, dict[str, str]]:
        with open(self.data_dir / "idea_destinations.json", encoding="utf-8") as f:
            raw = json.load(f)
        return {code.upper(): payload for code, payload in raw.items()}

    def idea_destination_codes(self) -> tuple[str, ...]:
        return tuple(self.idea_destinations.keys())

    def idea_profile(self, code: str) -> dict[str, str]:
        code = code.upper()
        return self.idea_destinations.get(
            code,
            {"label": self.label_for_code(code), "country": "Другое", "category": "вариант"},
        )

    def resolve_city_code(self, value: str) -> tuple[str, str] | None:
        normalized = normalize_name(value)
        if len(normalized) == 3 and normalized.isascii() and normalized.isalpha():
            code = normalized.upper()
            return self.code2city.get(code, code), code
        code = self.city2code.get(normalized)
        if not code:
            return None
        return self.code2city.get(code, value.strip().title()), code

    def resolve_destination(self, value: str) -> Destination | None:
        normalized = normalize_name(value)
        if normalized in self.countries:
            return self.countries[normalized]
        city = self.resolve_city_code(value)
        if city:
            label, code = city
            return Destination(label=label, codes=(code,), kind="city")
        return None

    def label_for_code(self, code: str) -> str:
        return self.code2city.get(code.upper(), code.upper())

    def airline_label(self, code: str | None) -> str:
        if not code:
            return "не указана"
        return self.airlines.get(code.upper(), code.upper())
