from __future__ import annotations

import html
from datetime import datetime

from .directories import Directory
from .models import FlightOffer, SearchQuery


def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₽"


def welcome_text() -> str:
    return (
        "✈️ <b>Гибкий поиск авиабилетов</b>\n\n"
        "Я ищу не только конкретный билет, а варианты по ограничениям: страна/город, даты, цена, пересадки и время в пути.\n\n"
        "Можно написать одной фразой:\n"
        "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч</code>"
    )


def examples_text() -> str:
    return (
        "<b>Примеры запросов</b>\n\n"
        "• <code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч</code>\n"
        "• <code>из Москвы в Таиланд 10.08-20.08 до 60000</code>\n"
        "• <code>из LED в Шанхай 01.09-10.09 без пересадок</code>\n\n"
        "Для MVP страны лежат в <code>data/countries.json</code>, города/алиасы — в <code>data/city2code.json</code>."
    )


def search_started_text(query: SearchQuery) -> str:
    return (
        "🔎 <b>Ищу варианты</b>\n"
        f"{html.escape(query.describe())}\n\n"
        "Сначала проверю самые дешёвые cached-офферы, затем отфильтрую по пересадкам, цене и длительности."
    )


def no_results_text(query: SearchQuery) -> str:
    hints = []
    if query.max_transfers is not None:
        hints.append("увеличить число пересадок")
    if query.max_price is not None:
        hints.append("поднять бюджет")
    if query.max_duration_minutes is not None:
        hints.append("увеличить лимит времени в пути")
    hints.append("расширить даты")
    return (
        "😕 <b>Ничего не нашлось</b>\n\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        "Что попробовать: " + ", ".join(hints) + "."
    )


def summary_text(query: SearchQuery, offers: list[FlightOffer]) -> str:
    if not offers:
        return no_results_text(query)
    cheapest = min(offers, key=lambda offer: offer.price)
    fastest = min(offers, key=lambda offer: offer.duration_minutes)
    return (
        f"✅ <b>Нашёл {len(offers)} вариантов</b>\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        f"💸 Самый дешёвый: {html.escape(cheapest.destination_label)} — {money(cheapest.price)}\n"
        f"⚡ Самый быстрый: {html.escape(fastest.destination_label)} — {fastest.duration_hm}\n\n"
        "Ниже — лучшие карточки по score: цена + штраф за пересадки/долгую дорогу/ночной вылет."
    )


def offer_card(offer: FlightOffer, directory: Directory, index: int | None = None) -> str:
    prefix = f"<b>#{index}</b> " if index else ""
    dep = offer.departure_at.strftime("%d.%m.%Y %H:%M") if offer.departure_at else "дата не указана"
    airline = directory.airline_label(offer.airline)
    return (
        f"{prefix}🇨🇳 <b>{html.escape(offer.destination_label)}</b> — <b>{money(offer.price)}</b>\n"
        f"{html.escape(offer.origin_label)} → {html.escape(offer.destination_label)}\n"
        f"🕒 {dep}, в пути {offer.duration_hm}\n"
        f"🔁 {offer.transfers_label}\n"
        f"✈️ {html.escape(airline)}"
    )


def error_text(exc: Exception) -> str:
    return (
        "⚠️ <b>Не получилось обработать запрос</b>\n\n"
        f"{html.escape(str(exc))}\n\n"
        "Пример рабочего формата:\n"
        "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч</code>"
    )
