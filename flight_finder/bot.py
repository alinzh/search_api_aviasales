from __future__ import annotations

import logging
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import telebot
from telebot import types

from .config import Settings
from .directories import Directory
from .formatters import (
    error_text,
    examples_text,
    no_results_text,
    offer_card,
    search_started_text,
    summary_text,
    welcome_text,
)
from .models import SearchMode, SearchQuery
from .quick_parser import ParseError, parse_multicity_points, parse_search_query
from .storage import Storage
from .travelpayouts_client import TravelpayoutsClient

logger = logging.getLogger(__name__)


@dataclass
class ChatSession:
    mode: str | None = None
    last_query: SearchQuery | None = None


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

    @bot.callback_query_handler(func=lambda call: call.data in {"quick", "discovery", "multi", "examples"})
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
                "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч</code>"
            )
        elif call.data == "discovery":
            session.mode = "discovery"
            text = (
                "Режим «куда можно улететь». Укажи страну/регион вместо города.\n\n"
                "Пример:\n"
                "<code>из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки</code>"
            )
        else:
            session.mode = "multi"
            text = (
                "Multi-city UX пока сделан как заготовка: я распознаю цепочку городов и подскажу следующий шаг.\n\n"
                "Пример:\n"
                "<code>СПб -> Стамбул -> Шанхай -> СПб</code>\n\n"
                "Для монетизируемого MVP основной поток — быстрый поиск и discovery по стране."
            )
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
            bot.answer_callback_query(call.id, "Сначала сделай поиск")
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
        mode = session.mode or "quick"
        if mode == "multi":
            points = parse_multicity_points(message.text, directory)
            if len(points) >= 2:
                human = " → ".join(label for label, _ in points)
                bot.send_message(
                    chat_id,
                    "🧭 Распознал маршрут:\n"
                    f"<b>{human}</b>\n\n"
                    "Следующий продуктовый шаг: для каждого плеча задать окно дат и собрать карточки. "
                    "В архиве оставил это как отдельную точку расширения, чтобы не ломать MVP поиска по стране.",
                    reply_markup=main_menu(),
                )
            else:
                bot.send_message(chat_id, "Не распознал цепочку городов. Пример: <code>СПб -> Стамбул -> Шанхай</code>")
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
        run_search_in_thread(bot, chat_id, query, client, directory, settings.top_limit)

    logger.info("Bot started")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


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


def main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚀 Быстрый поиск одной фразой", callback_data="quick"),
        types.InlineKeyboardButton("🌏 Куда можно улететь в страну/регион", callback_data="discovery"),
        types.InlineKeyboardButton("🧭 Multi-city маршрут", callback_data="multi"),
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
