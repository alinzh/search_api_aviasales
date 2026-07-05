from __future__ import annotations

import logging
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

import telebot
from telebot import types

from .config import Settings
from .directories import Directory
from .formatters import (
    error_text,
    examples_text,
    idea_card,
    ideas_help_text,
    ideas_started_text,
    ideas_summary_text,
    multicity_help_text,
    multicity_route_card,
    multicity_started_text,
    multicity_summary_text,
    no_ideas_results_text,
    no_multicity_results_text,
    no_results_text,
    no_roundtrip_results_text,
    offer_card,
    roundtrip_offer_card,
    roundtrip_summary_text,
    search_started_text,
    summary_text,
    welcome_text,
)
from .models import MultiCityQuery, SearchMode, SearchQuery
from .quick_parser import parse_ideas_query, parse_multicity_query, parse_search_query
from .storage import Storage
from .travelpayouts_client import TravelpayoutsClient

logger = logging.getLogger(__name__)


@dataclass
class ChatSession:
    mode: str | None = None
    last_query: SearchQuery | None = None
    last_multicity_query: MultiCityQuery | None = None


sessions: dict[int, ChatSession] = {}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    settings = Settings.from_env()
    settings.validate_for_bot()

    directory = Directory()
    client = TravelpayoutsClient(
        token=settings.aviasales_token,
        marker=settings.travelpayouts_marker,
        timeout_seconds=settings.request_timeout_seconds,
    )
    storage = Storage(Path(__file__).resolve().parent.parent / "flight_finder.sqlite3")

    bot = telebot.TeleBot(settings.telegram_bot_token, parse_mode="HTML")

    @bot.message_handler(commands=["start"])
    def start(message: types.Message) -> None:
        sessions[message.chat.id] = ChatSession()
        bot.send_message(message.chat.id, welcome_text(), reply_markup=main_menu())

    @bot.message_handler(commands=["examples", "help"])
    def examples(message: types.Message) -> None:
        bot.send_message(message.chat.id, examples_text(), reply_markup=main_menu())

    @bot.message_handler(commands=["alerts"])
    def alerts(message: types.Message) -> None:
        rows = storage.list_alerts(message.chat.id)
        if not rows:
            bot.send_message(
                message.chat.id,
                "Пока нет активных уведомлений. Сделай поиск и нажми «Следить за ценой».",
                reply_markup=main_menu(),
            )
            return
        lines = ["🔔 <b>Твои price alerts</b>"]
        for row in rows:
            q = row["query"]
            threshold = row["threshold_price"]
            threshold_text = f"до {threshold:,} ₽".replace(",", " ") if threshold else "любой спад цены"
            lines.append(
                f"#{row['id']}: {q['origin_label']} → {q['destination']['label']}, "
                f"{q['date_from']}–{q['date_to']}, {threshold_text}"
            )
        bot.send_message(message.chat.id, "\n".join(lines), reply_markup=main_menu())

    @bot.callback_query_handler(func=lambda call: call.data in {"quick", "discovery", "ideas", "multi", "examples"})
    def menu_callback(call: types.CallbackQuery) -> None:
        chat_id = call.message.chat.id
        session = sessions.setdefault(chat_id, ChatSession())
        if call.data == "examples":
            bot.answer_callback_query(call.id)
            bot.send_message(chat_id, examples_text(), reply_markup=main_menu())
            return
        if call.data == "quick":
            session.mode = "quick"
            text = (
                "Напиши запрос одной фразой.\n\n"
                "Пример:\n"
                "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч</code>\n\n"
                "Туда-обратно:\n"
                "<code>из СПб в Китай и обратно 06.07-14.07 до 90000</code>"
            )
        elif call.data == "discovery":
            session.mode = "discovery"
            text = (
                "Режим «куда можно улететь». Укажи страну/регион вместо города.\n\n"
                "Пример:\n"
                "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки</code>\n\n"
                "Туда-обратно:\n"
                "<code>из СПб в Китай и обратно 06.07-14.07 до 90000</code>"
            )
        elif call.data == "ideas":
            session.mode = "ideas"
            text = ideas_help_text()
        else:
            session.mode = "multi"
            text = multicity_help_text()
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, text, reply_markup=restart_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "restart")
    def restart_callback(call: types.CallbackQuery) -> None:
        sessions[call.message.chat.id] = ChatSession()
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, welcome_text(), reply_markup=main_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "alert_current")
    def alert_current(call: types.CallbackQuery) -> None:
        session = sessions.setdefault(call.message.chat.id, ChatSession())
        if not session.last_query:
            bot.answer_callback_query(call.id, "Сначала сделай обычный поиск")
            return
        alert_id = storage.create_alert(call.message.chat.id, session.last_query)
        bot.answer_callback_query(call.id, "Уведомление создано")
        bot.send_message(
            call.message.chat.id,
            f"🔔 Создан price alert #{alert_id}\n{session.last_query.describe()}",
            reply_markup=main_menu(),
        )

    @bot.message_handler(func=lambda message: True, content_types=["text"])
    def text_handler(message: types.Message) -> None:
        chat_id = message.chat.id
        session = sessions.setdefault(chat_id, ChatSession())
        mode = session.mode or "multi"
        if mode == "multi":
            try:
                query = parse_multicity_query(
                    message.text,
                    directory=directory,
                    currency=settings.currency,
                    market=settings.market,
                )
            except Exception as exc:
                bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
                return
            session.last_multicity_query = query
            run_multicity_in_thread(bot, chat_id, query, client, directory)
            return

        if mode == "ideas":
            try:
                query = parse_ideas_query(
                    message.text,
                    directory=directory,
                    currency=settings.currency,
                    market=settings.market,
                )
            except Exception as exc:
                bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
                return
            session.last_query = query
            storage.save_search(chat_id, query)
            run_ideas_in_thread(bot, chat_id, query, client, directory, settings.top_limit)
            return

        search_mode = SearchMode.DISCOVERY if mode == "discovery" else SearchMode.QUICK
        try:
            query = parse_search_query(
                message.text,
                directory=directory,
                currency=settings.currency,
                market=settings.market,
                mode=search_mode,
            )
        except Exception as exc:
            bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
            return
        session.last_query = query
        storage.save_search(chat_id, query)
        if query.is_round_trip:
            run_roundtrip_in_thread(bot, chat_id, query, client, directory, settings.top_limit)
        else:
            run_search_in_thread(bot, chat_id, query, client, directory, settings.top_limit)

    logger.info("Bot started")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


def run_ideas_in_thread(
    bot: telebot.TeleBot,
    chat_id: int,
    query: SearchQuery,
    client: TravelpayoutsClient,
    directory: Directory,
    top_limit: int,
) -> None:
    def worker() -> None:
        bot.send_message(chat_id, ideas_started_text(query), reply_markup=restart_menu())
        try:
            offers = client.search_ideas(query, directory, limit_per_destination=3, max_results=max(top_limit, 8))
        except Exception as exc:
            logger.exception("Ideas search failed")
            bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
            return
        if not offers:
            bot.send_message(chat_id, no_ideas_results_text(query), reply_markup=main_menu())
            return
        offers = offers[:max(top_limit, 8)]
        bot.send_message(chat_id, ideas_summary_text(query, offers, directory), reply_markup=after_results_menu())
        for idx, offer in enumerate(offers, start=1):
            bot.send_message(chat_id, idea_card(offer, directory, idx), reply_markup=offer_menu(offer.link))

    threading.Thread(target=worker, daemon=True).start()


def run_search_in_thread(
    bot: telebot.TeleBot,
    chat_id: int,
    query: SearchQuery,
    client: TravelpayoutsClient,
    directory: Directory,
    top_limit: int,
) -> None:
    def worker() -> None:
        bot.send_message(chat_id, search_started_text(query), reply_markup=restart_menu())
        try:
            offers = client.search(query, directory, limit_per_destination=max(top_limit, 5))
        except Exception as exc:
            logger.exception("Search failed")
            bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
            return
        if not offers:
            bot.send_message(chat_id, no_results_text(query), reply_markup=main_menu())
            return
        offers = offers[:top_limit]
        bot.send_message(chat_id, summary_text(query, offers), reply_markup=after_results_menu())
        for idx, offer in enumerate(offers, start=1):
            bot.send_message(chat_id, offer_card(offer, directory, idx), reply_markup=offer_menu(offer.link))

    threading.Thread(target=worker, daemon=True).start()



def run_roundtrip_in_thread(
    bot: telebot.TeleBot,
    chat_id: int,
    query: SearchQuery,
    client: TravelpayoutsClient,
    directory: Directory,
    top_limit: int,
) -> None:
    def worker() -> None:
        bot.send_message(chat_id, search_started_text(query), reply_markup=restart_menu())
        try:
            offers = client.search_round_trip(query, directory, limit_per_destination=max(top_limit, 5))
        except Exception as exc:
            logger.exception("Round-trip search failed")
            bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
            return
        if not offers:
            bot.send_message(chat_id, no_roundtrip_results_text(query), reply_markup=main_menu())
            return
        offers = offers[:top_limit]
        bot.send_message(chat_id, roundtrip_summary_text(query, offers), reply_markup=after_results_menu())
        for idx, offer in enumerate(offers, start=1):
            bot.send_message(chat_id, roundtrip_offer_card(offer, directory, idx), reply_markup=roundtrip_menu(offer))

    threading.Thread(target=worker, daemon=True).start()


def run_multicity_in_thread(
    bot: telebot.TeleBot,
    chat_id: int,
    query: MultiCityQuery,
    client: TravelpayoutsClient,
    directory: Directory,
) -> None:
    def worker() -> None:
        bot.send_message(chat_id, multicity_started_text(query), reply_markup=restart_menu())
        try:
            routes = client.optimize_multicity(query, directory, max_routes=5)
        except Exception as exc:
            logger.exception("Multi-city optimization failed")
            bot.send_message(chat_id, error_text(exc), reply_markup=main_menu())
            return
        if not routes:
            bot.send_message(chat_id, no_multicity_results_text(query), reply_markup=main_menu())
            return
        bot.send_message(chat_id, multicity_summary_text(query, routes), reply_markup=main_menu())
        for idx, route in enumerate(routes, start=1):
            bot.send_message(chat_id, multicity_route_card(route, directory, idx), reply_markup=route_menu(route))

    threading.Thread(target=worker, daemon=True).start()


def main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧭 Multi-city: найди порядок городов", callback_data="multi"),
        types.InlineKeyboardButton("🎲 Идеи в бюджет: куда угодно", callback_data="ideas"),
        types.InlineKeyboardButton("🌏 Куда можно улететь в страну/регион", callback_data="discovery"),
        types.InlineKeyboardButton("🚀 Быстрый поиск одной фразой", callback_data="quick"),
        types.InlineKeyboardButton("💡 Примеры", callback_data="examples"),
    )
    return markup


def restart_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("↩️ Начать заново", callback_data="restart"))
    return markup


def after_results_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔔 Следить за ценой этого запроса", callback_data="alert_current"),
        types.InlineKeyboardButton("🔎 Новый поиск", callback_data="restart"),
    )
    return markup


def offer_menu(link: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Открыть билет", url=link))
    return markup



def roundtrip_menu(offer) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Открыть билет туда", url=offer.outbound.link))
    markup.add(types.InlineKeyboardButton("Открыть обратный билет", url=offer.inbound.link))
    return markup


def route_menu(route) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for idx, leg in enumerate(route.legs, start=1):
        markup.add(
            types.InlineKeyboardButton(
                f"Открыть плечо {idx}: {leg.origin.label} → {leg.destination.label}",
                url=leg.offer.link,
            )
        )
    markup.add(types.InlineKeyboardButton("🔎 Новый поиск", callback_data="restart"))
    return markup
