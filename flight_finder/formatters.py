from __future__ import annotations

import html

from .directories import Directory
from .models import FlightOffer, MultiCityQuery, MultiCityRoute, RoundTripOffer, SearchQuery


def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₽"


def welcome_text() -> str:
    return (
        "✈️ <b>Гибкий поиск авиабилетов</b>\n\n"
        "Главная фича — не просто multi-city в заданном порядке, а подбор порядка городов. "
        "Ты даёшь список городов, которые хочешь посетить, а я ищу самый дешёвый маршрут.\n\n"
        "Ещё есть режим идей: задай бюджет и примерный период, а бот предложит разные направления.\n\n"
        "Пример multi-city:\n"
        "<code>из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 по 2-4 дня до 120000</code>\n\n"
        "Пример идей:\n"
        "<code>из СПб куда угодно в августе до 50000</code>"
    )


def examples_text() -> str:
    return (
        "<b>Примеры запросов</b>\n\n"
        "🧭 <b>Multi-city optimizer</b> — порядок городов НЕ задаёшь:\n"
        "• <code>из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 по 2-4 дня до 120000</code>\n"
        "• <code>СПб: Стамбул, Шанхай, Бангкок 06.07-25.07 до 1 пересадки</code>\n"
        "• <code>из LED через IST, SHA, BKK 06.07-25.07 без возврата</code>\n\n"
        "🎲 <b>Идеи в бюджет</b> — направление не задаёшь:\n"
        "• <code>из СПб куда угодно в августе до 50000</code>\n"
        "• <code>куда слетать из Москвы 10.08-20.08 до 60000</code>\n"
        "• <code>идеи из LED в июле до 40000 до 1 пересадки</code>\n\n"
        "🌏 <b>Куда можно улететь</b>:\n"
        "• <code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч</code>\n"
        "• <code>из Москвы в Таиланд 10.08-20.08 до 60000</code>\n\n"
        "↩️ <b>Туда-обратно</b>:\n"
        "• <code>из СПб в Китай и обратно 06.07-14.07 до 90000</code>\n"
        "• <code>из СПб в Китай туда 06.07-08.07 обратно 14.07-16.07 до 90000</code>\n\n"
        "Для MVP страны лежат в <code>data/countries.json</code>, города/алиасы — в <code>data/city2code.json</code>."
    )


def search_started_text(query: SearchQuery) -> str:
    if query.is_round_trip:
        tail = "Сначала найду дешёвые варианты туда, затем обратные плечи и соберу пары туда-обратно."
    else:
        tail = "Сначала проверю самые дешёвые cached-офферы, затем отфильтрую по пересадкам, цене и длительности."
    return (
        "🔎 <b>Ищу варианты</b>\n"
        f"{html.escape(query.describe())}\n\n"
        f"{tail}"
    )


def ideas_help_text() -> str:
    return (
        "🎲 <b>Идеи в бюджет</b>\n\n"
        "Это режим для ситуации, когда ты не знаешь, куда хочешь лететь. "
        "Укажи город отправления, бюджет и примерный период — бот просканирует разные направления "
        "и покажет разнообразную подборку по странам и типам поездки.\n\n"
        "Форматы:\n"
        "• <code>из СПб куда угодно в августе до 50000</code>\n"
        "• <code>куда слетать из Москвы 10.08-20.08 до 60000</code>\n"
        "• <code>идеи из LED в июле до 40000 до 1 пересадки</code>\n\n"
        "Важно: бюджет здесь считается на один перелёт в одну сторону. "
        "Для туда-обратно используй режим поиска по стране с <code>и обратно</code>."
    )


def ideas_started_text(query: SearchQuery) -> str:
    return (
        "🎲 <b>Ищу идеи в бюджет</b>\n"
        f"{html.escape(query.describe())}\n\n"
        "Проверю разные направления из базы идей и специально разбавлю выдачу по странам, "
        "чтобы не показать 10 похожих городов подряд."
    )


def no_ideas_results_text(query: SearchQuery) -> str:
    return (
        "😕 <b>Не нашёл идей в этот бюджет</b>\n\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        "Что попробовать: поднять бюджет, расширить период, разрешить пересадки или убрать лимит времени в пути."
    )


def ideas_summary_text(query: SearchQuery, offers: list[FlightOffer], directory: Directory) -> str:
    if not offers:
        return no_ideas_results_text(query)
    countries: list[str] = []
    for offer in offers:
        country = directory.idea_profile(offer.destination).get("country", "Другое")
        if country not in countries:
            countries.append(country)
    return (
        f"✅ <b>Нашёл {len(offers)} разных идей</b>\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        f"🌍 Страны/направления: {html.escape(', '.join(countries[:8]))}\n"
        "Ниже — не просто самые дешёвые билеты, а разнообразная подборка: город, пляж, культура, хабы и соседние страны."
    )


def idea_card(offer: FlightOffer, directory: Directory, index: int) -> str:
    profile = directory.idea_profile(offer.destination)
    country = profile.get("country", "Другое")
    category = profile.get("category", "вариант")
    dep = offer.departure_at.strftime("%d.%m.%Y %H:%M") if offer.departure_at else "дата не указана"
    airline = directory.airline_label(offer.airline)
    return (
        f"<b>#{index} {html.escape(offer.destination_label)}</b> — <b>{money(offer.price)}</b>\n"
        f"🌍 {html.escape(country)} · {html.escape(category)}\n"
        f"✈️ {html.escape(offer.origin_label)} → {html.escape(offer.destination_label)}\n"
        f"🕒 {dep}, в пути {offer.duration_hm}\n"
        f"🔁 {offer.transfers_label}\n"
        f"✈️ {html.escape(airline)}"
    )


def multicity_help_text() -> str:
    return (
        "🧭 <b>Multi-city optimizer</b>\n\n"
        "Это главный режим: укажи список городов без порядка, а бот переберёт варианты и найдёт дешёвый порядок посещения.\n\n"
        "Формат:\n"
        "<code>из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 по 2-4 дня до 120000</code>\n\n"
        "Что поддерживается:\n"
        "• стартовый город;\n"
        "• 2–7 городов для посещения;\n"
        "• общее окно дат;\n"
        "• сколько дней провести в каждом городе;\n"
        "• общий бюджет;\n"
        "• максимум пересадок и длительность на каждое плечо;\n"
        "• <code>без возврата</code>, если не нужно возвращаться в стартовый город."
    )


def multicity_started_text(query: MultiCityQuery) -> str:
    return (
        "🧮 <b>Оптимизирую порядок городов</b>\n"
        f"{html.escape(query.describe())}\n\n"
        "Проверю пары городов, переберу перестановки и оставлю маршруты, где перелёты идут в хронологическом порядке "
        "и выдерживается остановка в каждом городе."
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


def no_multicity_results_text(query: MultiCityQuery) -> str:
    return (
        "😕 <b>Не нашёл цельный multi-city маршрут</b>\n\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        "Что попробовать: расширить общее окно дат, увеличить допустимое число пересадок, "
        "уменьшить минимальную остановку в городе или поднять общий бюджет."
    )


def no_roundtrip_results_text(query: SearchQuery) -> str:
    return (
        "😕 <b>Не нашёл пару туда-обратно</b>\n\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        "Что попробовать: расширить даты туда/обратно, поднять общий бюджет, "
        "разрешить больше пересадок или искать страну без строгого лимита длительности."
    )


def roundtrip_summary_text(query: SearchQuery, offers: list[RoundTripOffer]) -> str:
    if not offers:
        return no_roundtrip_results_text(query)
    best = offers[0]
    return (
        f"✅ <b>Нашёл {len(offers)} вариантов туда-обратно</b>\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        f"💸 Лучший: {html.escape(best.destination.label)} — <b>{money(best.total_price)}</b>\n"
        f"🧭 {html.escape(best.outbound.origin_label)} → {html.escape(best.destination.label)} → {html.escape(best.inbound.destination_label)}\n\n"
        "Ниже — карточки. У каждой две кнопки: открыть билет туда и открыть обратный билет."
    )


def roundtrip_offer_card(item: RoundTripOffer, directory: Directory, index: int) -> str:
    out = item.outbound
    back = item.inbound
    out_dep = out.departure_at.strftime("%d.%m.%Y %H:%M") if out.departure_at else "дата?"
    back_dep = back.departure_at.strftime("%d.%m.%Y %H:%M") if back.departure_at else "дата?"
    return (
        f"<b>#{index} Туда-обратно: {html.escape(item.destination.label)}</b> — <b>{money(item.total_price)}</b>\n\n"
        f"➡️ <b>Туда</b>: {html.escape(out.origin_label)} → {html.escape(out.destination_label)}\n"
        f"🕒 {out_dep}, {out.duration_hm}, {out.transfers_label}, {html.escape(directory.airline_label(out.airline))}\n"
        f"💸 {money(out.price)}\n\n"
        f"⬅️ <b>Обратно</b>: {html.escape(back.origin_label)} → {html.escape(back.destination_label)}\n"
        f"🕒 {back_dep}, {back.duration_hm}, {back.transfers_label}, {html.escape(directory.airline_label(back.airline))}\n"
        f"💸 {money(back.price)}"
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


def multicity_summary_text(query: MultiCityQuery, routes: list[MultiCityRoute]) -> str:
    if not routes:
        return no_multicity_results_text(query)
    best = routes[0]
    return (
        f"✅ <b>Нашёл {len(routes)} multi-city маршрутов</b>\n"
        f"Запрос: {html.escape(query.describe())}\n\n"
        f"💸 Лучший маршрут: <b>{money(best.total_price)}</b>\n"
        f"🧭 Порядок: {' → '.join(html.escape(label) for label in best.route_labels)}\n\n"
        "Ниже — карточки маршрутов. Кнопки открывают конкретные плечи на Aviasales."
    )


def offer_card(offer: FlightOffer, directory: Directory, index: int | None = None) -> str:
    prefix = f"<b>#{index}</b> " if index else ""
    dep = offer.departure_at.strftime("%d.%m.%Y %H:%M") if offer.departure_at else "дата не указана"
    airline = directory.airline_label(offer.airline)
    return (
        f"{prefix}✈️ <b>{html.escape(offer.destination_label)}</b> — <b>{money(offer.price)}</b>\n"
        f"{html.escape(offer.origin_label)} → {html.escape(offer.destination_label)}\n"
        f"🕒 {dep}, в пути {offer.duration_hm}\n"
        f"🔁 {offer.transfers_label}\n"
        f"✈️ {html.escape(airline)}"
    )


def multicity_route_card(route: MultiCityRoute, directory: Directory, index: int) -> str:
    lines = [
        f"<b>#{index} Multi-city маршрут</b> — <b>{money(route.total_price)}</b>",
        f"🧭 {' → '.join(html.escape(label) for label in route.route_labels)}",
        "",
    ]
    for leg_index, leg in enumerate(route.legs, start=1):
        offer = leg.offer
        dep = offer.departure_at.strftime("%d.%m %H:%M") if offer.departure_at else "дата?"
        arr = offer.arrival_at.strftime("%d.%m %H:%M") if offer.arrival_at else "дата?"
        airline = directory.airline_label(offer.airline)
        lines.append(
            f"{leg_index}. {html.escape(leg.origin.label)} → {html.escape(leg.destination.label)}: "
            f"<b>{money(offer.price)}</b>, {dep}–{arr}, {offer.transfers_label}, {html.escape(airline)}"
        )
    return "\n".join(lines)


def error_text(exc: Exception) -> str:
    return (
        "⚠️ <b>Не получилось обработать запрос</b>\n\n"
        f"{html.escape(str(exc))}\n\n"
        "Пример multi-city:\n"
        "<code>из СПб посетить Стамбул, Шанхай, Бангкок 06.07-25.07 по 2-4 дня</code>\n\n"
        "Пример идей в бюджет:\n"
        "<code>из СПб куда угодно в августе до 50000</code>\n\n"
        "Пример поиска по стране:\n"
        "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки</code>\n\n"
        "Пример туда-обратно:\n"
        "<code>из СПб в Китай и обратно 06.07-14.07 до 90000</code>"
    )
