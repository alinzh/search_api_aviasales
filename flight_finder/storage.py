from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import SearchQuery


class Storage:
    def __init__(self, path: str | Path = "flight_finder.sqlite3"):
        self.path = Path(path)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    raw_query TEXT NOT NULL,
                    parsed_query_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    query_json TEXT NOT NULL,
                    threshold_price INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_checked_at TEXT
                )
                """
            )

    def save_search(self, chat_id: int, query: SearchQuery) -> None:
        payload = query_to_jsonable(query)
        with self._connect() as con:
            con.execute(
                "INSERT INTO searches(chat_id, raw_query, parsed_query_json, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, query.raw_text, json.dumps(payload, ensure_ascii=False), now_iso()),
            )

    def create_alert(self, chat_id: int, query: SearchQuery, threshold_price: int | None = None) -> int:
        payload = query_to_jsonable(query)
        if threshold_price is None:
            threshold_price = query.max_price
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO price_alerts(chat_id, query_json, threshold_price, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, json.dumps(payload, ensure_ascii=False), threshold_price, now_iso()),
            )
            return int(cur.lastrowid)

    def list_alerts(self, chat_id: int) -> list[dict]:
        with self._connect() as con:
            cur = con.execute(
                "SELECT id, query_json, threshold_price, is_active, created_at FROM price_alerts WHERE chat_id=? ORDER BY id DESC LIMIT 20",
                (chat_id,),
            )
            rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "query": json.loads(row[1]),
                "threshold_price": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def query_to_jsonable(query: SearchQuery) -> dict:
    return {
        "origin_label": query.origin_label,
        "origin_code": query.origin_code,
        "destination": {
            "label": query.destination.label,
            "codes": list(query.destination.codes),
            "kind": query.destination.kind,
        },
        "date_from": query.date_from.isoformat(),
        "date_to": query.date_to.isoformat(),
        "max_price": query.max_price,
        "max_transfers": query.max_transfers,
        "max_duration_minutes": query.max_duration_minutes,
        "currency": query.currency,
        "market": query.market,
        "mode": query.mode.value,
        "raw_text": query.raw_text,
    }
