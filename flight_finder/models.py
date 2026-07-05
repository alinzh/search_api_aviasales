from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any


class SearchMode(str, Enum):
    QUICK = "quick"
    DISCOVERY = "discovery"
    MULTI_CITY = "multi_city"
    ROUND_TRIP = "round_trip"
    IDEAS = "ideas"


@dataclass(frozen=True)
class Destination:
    label: str
    codes: tuple[str, ...]
    kind: str = "city"  # city | country | region


@dataclass(frozen=True)
class CityPoint:
    label: str
    code: str


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
    return_to_origin: bool = False
    return_date_from: date | None = None
    return_date_to: date | None = None

    @property
    def is_round_trip(self) -> bool:
        return self.return_to_origin and self.return_date_from is not None and self.return_date_to is not None

    def describe(self) -> str:
        parts = [f"{self.origin_label} → {self.destination.label}"]
        if self.is_round_trip:
            if self.date_from == self.date_to:
                outbound = f"туда {self.date_from:%d.%m.%Y}"
            else:
                outbound = f"туда {self.date_from:%d.%m.%Y}–{self.date_to:%d.%m.%Y}"
            assert self.return_date_from is not None and self.return_date_to is not None
            if self.return_date_from == self.return_date_to:
                back = f"обратно {self.return_date_from:%d.%m.%Y}"
            else:
                back = f"обратно {self.return_date_from:%d.%m.%Y}–{self.return_date_to:%d.%m.%Y}"
            parts.append(f"{outbound}, {back}")
        else:
            parts.append(f"{self.date_from:%d.%m.%Y}–{self.date_to:%d.%m.%Y}")
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
class MultiCityQuery:
    """Unordered multi-city route query.

    The user gives cities they want to visit, but not their order. The optimizer
    chooses the cheapest feasible order and concrete flight legs inside the date
    window.
    """

    origin: CityPoint
    visit_cities: tuple[CityPoint, ...]
    date_from: date
    date_to: date
    final_destination: CityPoint | None = None
    min_stay_days: int = 1
    max_stay_days: int | None = 7
    return_to_origin: bool = True
    max_price: int | None = None  # total route price limit
    max_transfers: int | None = None  # per leg
    max_duration_minutes: int | None = None  # per leg
    currency: str = "rub"
    market: str = "ru"
    raw_text: str = ""

    def describe(self) -> str:
        cities = ", ".join(city.label for city in self.visit_cities)
        parts = [
            f"старт: {self.origin.label}",
            f"посетить: {cities}",
            f"окно: {self.date_from:%d.%m.%Y}–{self.date_to:%d.%m.%Y}",
        ]
        if self.final_destination:
            parts.append(f"финиш: {self.final_destination.label}")
        elif self.return_to_origin:
            parts.append("с возвратом в стартовый город")
        else:
            parts.append("без обязательного возврата")
        if self.min_stay_days or self.max_stay_days:
            if self.max_stay_days and self.max_stay_days != self.min_stay_days:
                parts.append(f"в городе {self.min_stay_days}–{self.max_stay_days} дн.")
            else:
                parts.append(f"в городе от {self.min_stay_days} дн.")
        if self.max_price:
            parts.append(f"общий бюджет до {self.max_price:,} ₽".replace(",", " "))
        if self.max_transfers is not None:
            parts.append("без пересадок на плечо" if self.max_transfers == 0 else f"до {self.max_transfers} перес. на плечо")
        if self.max_duration_minutes:
            hours = self.max_duration_minutes // 60
            minutes = self.max_duration_minutes % 60
            parts.append(f"до {hours}ч {minutes:02d}м на плечо")
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

    @property
    def arrival_at(self) -> datetime | None:
        if not self.departure_at:
            return None
        return self.departure_at + timedelta(minutes=self.duration_minutes)


@dataclass
class RoundTripOffer:
    destination: CityPoint
    outbound: FlightOffer
    inbound: FlightOffer
    total_price: int
    score: float

    @property
    def total_duration_minutes(self) -> int:
        return self.outbound.duration_minutes + self.inbound.duration_minutes

    @property
    def duration_hm(self) -> str:
        hours = self.total_duration_minutes // 60
        minutes = self.total_duration_minutes % 60
        return f"{hours}ч {minutes:02d}м"


@dataclass
class MultiCityLeg:
    origin: CityPoint
    destination: CityPoint
    offer: FlightOffer


@dataclass
class MultiCityRoute:
    order: tuple[CityPoint, ...]
    legs: tuple[MultiCityLeg, ...]
    total_price: int
    total_duration_minutes: int
    score: float

    @property
    def route_labels(self) -> list[str]:
        if not self.legs:
            return [city.label for city in self.order]
        labels = [self.legs[0].origin.label]
        labels.extend(leg.destination.label for leg in self.legs)
        return labels
