from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import set

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _csv_ints(value: str | None) -> set[int]:
    if not value:
        return set()
    result: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if item.isdigit():
            result.add(int(item))
    return result


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    aviasales_token: str
    travelpayouts_marker: str | None
    admin_telegram_ids: set[int]
    currency: str = "rub"
    market: str = "ru"
    top_limit: int = 7
    request_timeout_seconds: int = 15

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            aviasales_token=os.environ.get("AVIASALES_TOKEN", ""),
            travelpayouts_marker=os.environ.get("TRAVELPAYOUTS_MARKER") or None,
            admin_telegram_ids=_csv_ints(os.environ.get("ADMIN_TELEGRAM_IDS")),
            currency=os.environ.get("BOT_CURRENCY", "rub"),
            market=os.environ.get("BOT_MARKET", "ru"),
            top_limit=int(os.environ.get("BOT_TOP_LIMIT", "7")),
            request_timeout_seconds=int(os.environ.get("BOT_REQUEST_TIMEOUT_SECONDS", "15")),
        )

    def validate_for_bot(self) -> None:
        missing = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.aviasales_token:
            missing.append("AVIASALES_TOKEN")
        if missing:
            raise RuntimeError(
                "Не заданы обязательные переменные окружения: "
                + ", ".join(missing)
                + ". Скопируй .env.example в .env и заполни значения."
            )
