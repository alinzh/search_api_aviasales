from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class SearchMode(str, Enum):
    QUICK = "quick"
    DISCOVERY = "discovery"
    MULTI_CITY = "multi_city"


@dataclass(frozen=True)
class Destination:
    label: str
    codes: tuple[str, ...]
    kind: str = "city"  # city | country | region


@dataclass
class SearchQuery:
    origin_label: str
    origin_code: str
    destination: Destination
    date_from: date
    date_to: date
    max_price: int | None = None
    max_transfers: int | None = None
    max_duration_minutes: int | None = None
    currency: str = "rub"
    market: str = "ru"
    mode: SearchMode = SearchMode.QUICK
    raw_text: str = ""

    def describe(self) -> str:
        parts = [
            f"{self.origin_label} → {self.destination.label}",
            f"{self.date_from:%d.%m.%Y}–{self.date_to:%d.%m.%Y}",
        ]
        if self.max_price:
            parts.append(f"до {self.max_price:,} ₽".replace(",", " "))
        if self.max_transfers is not None:
            parts.append("без пересадок" if self.max_transfers == 0 else f"до {self.max_transfers} перес.")
        if self.max_duration_minutes:
            hours = self.max_duration_minutes // 60
            minutes = self.max_duration_minutes % 60
            parts.append(f"до {hours}ч {minutes:02d}м")
        return ", ".join(parts)


@dataclass
class FlightOffer:
    origin: str
    destination: str
    origin_label: str
    destination_label: str
    price: int
    airline: str | None
    transfers: int
    duration_minutes: int
    departure_at: datetime | None
    link: str
    raw: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    @property
    def duration_hm(self) -> str:
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}ч {minutes:02d}м"

    @property
    def transfers_label(self) -> str:
        if self.transfers == 0:
            return "без пересадок"
        if self.transfers == 1:
            return "1 пересадка"
        if 2 <= self.transfers <= 4:
            return f"{self.transfers} пересадки"
        return f"{self.transfers} пересадок"


@dataclass
class MultiCityLeg:
    origin_label: str
    destination_label: str
    date_from: date
    date_to: date
    best_offer: FlightOffer | None
