import datetime
import logging
import os
import sys
from enum import IntEnum

from dotenv import load_dotenv

import telebot
import text_for_send_message_bot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar

from db_handler import sql_users
from search import Search
from search.serchrequestdata import SearchRequestData
from utils.check_answer import CheckData

if __name__ == "__main__":
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger("bot")
    logging.getLogger("telebot").setLevel(logging.INFO)
    telebot.apihelper.ENABLE_MIDDLEWARE = True
    telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60
    bot = telebot.TeleBot(os.environ["TELEGRAM_BOT_TOKEN"], parse_mode=None)
    logger.info("Бот запущен, token=%s...%s", os.environ["TELEGRAM_BOT_TOKEN"][:8], os.environ["TELEGRAM_BOT_TOKEN"][-4:])

    # Storage of flag that users enter (here is all users, who is typing something at the moment).
    # Here is stored instance of class that can be accesed by user id

    users_state = {}

    class UserStates(IntEnum):
        """
        Class in which all possible status for user state are created.
        """

        WAIT_FOR_TRANSIT_PERIOD = 1
        WAIT_FOR_AIRPORT = 2
        WAIT_FOR_START = 3
        WAIT_FOR_HOME = 4
        WAIT_FOR_DATA_HOME_DEPARTURE = 5
        WAIT_FOR_CIRCLE_OR_NOT = 6
        WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD = 7
        WAIT_FOR_CHOOSE = 8
        WAIT_FOR_HATE_AIRL = 9
        WAIT_FOR_END = 10
        WAIT_FOR_FINISH_AIRPORT = 11
        WAIT_FOR_MORE_TICKETS = 12
        WAIT_FOR_SECOND_DATE_FROM_PERIOD_HOME = 13
        WAIT_FOR_FIRST_DATE_FROM_PERIOD_HOME = 14
        WAIT_FOR_DATE_OR_PERIOD_FROM_HOME = 15
        WAIT_FOR_DATE_OR_PERIOD_TO_FINISH = 16
        WAIT_FOR_SECOND_DATE_FROM_PERIOD_FINISH = 17

    class UserState:
        """
        Class which created for every user. Here is stored information about users state/status.
        Status is using for sequential function calls.
        Also here is created  class instance of SearchRequestData
        """

        def __init__(self, user_id):
            self.state = None
            self.user_id = user_id
            self.search_request_data = SearchRequestData(user_id=self.user_id)
            self.best_in_price = None
            self.best_in_time = None

    # Here is created sql database and exported date which was in tables for some reasons,
    # for example - download updates or bot falling

    sql_users.create_table_in_database()
    date_from_sql_users = sql_users.get_all_data_from_table()
    date_from_sql_users_airport = sql_users.get_all_data_from_users_airport()
    date_from_sql_users_tranzit = sql_users.get_all_data_from_users_tranzit()

    for i in date_from_sql_users:
        if (date_from_sql_users != None) or (date_from_sql_users != []):
            user_id = i[0]
            state = i[3]
            users_state[user_id] = UserState(user_id=user_id)
            users_state[user_id].state = state
            try:
                users_state[
                    user_id
                ].search_request_data.append_start_date_exception_sql(i[4])
            except:
                pass
            try:
                users_state[user_id].search_request_data.append_end_date_exception_sql(
                    i[5]
                )
            except:
                pass
            try:
                users_state[
                    user_id
                ].search_request_data.append_start_period_exception_sql(eval(i[6]))
            except:
                pass
            try:
                users_state[
                    user_id
                ].search_request_data.append_end_period_exception_sql(eval(i[7]))
            except:
                pass
            try:
                users_state[user_id].search_request_data.append_home_exception_sql(i[8])
            except:
                pass
            try:
                users_state[user_id].search_request_data.append_finish_exception_sql(
                    i[9]
                )
            except:
                pass
            try:
                users_state[user_id].search_request_data.append_hate_airl_exception_sql(
                    eval(i[10])
                )
            except:
                pass
    for string in date_from_sql_users_airport:
        user_id = string[0]
        users_state[user_id].search_request_data.append_airport(string[1])
    for string in date_from_sql_users_tranzit:
        user_id = string[0]
        users_state[user_id].search_request_data.append_time_tranzit_exception_sql(
            (string[1], int(string[2]))
        )

    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        """
        Sending hello-message to user.
        Added to SQL user_id, username, full_name (if not hidden), data about route is empty on start.
        """
        logger.info("user=%s @%s /start", message.from_user.id, message.from_user.username)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Начать поиск", callback_data="compute_route")
        )
        bot.reply_to(
            message,
            text=text_for_send_message_bot.message_hello(),
            reply_markup=markup,
            parse_mode="HTML",
        )
        sql_users.add_users_to_sql(
            [
                (
                    message.from_user.id,
                    message.from_user.username,
                    message.from_user.full_name,
                    0,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "[]",
                )
            ]
        )
        sql_users.users_all_the_time(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "compute_route"
    )
    def compute_route_handler(callback_query):
        """
        Here is created instance class of UserState where will stores all data about user.
        Assigned status WAIT_FOR_HOME, it means that after this func will waiting func home_handler.

        Also here is rest data abot route users, how already used bot, but decide to start new search
        """
        logger.info("user=%s начал подбор маршрута", callback_query.from_user.id)
        users_state[callback_query.message.chat.id] = UserState(
            callback_query.message.chat.id
        )
        # экземпляр класса UserState() создается тут!!
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HOME
        sql_users.add_users_to_sql(
            [
                (
                    callback_query.from_user.id,
                    callback_query.from_user.username,
                    callback_query.from_user.full_name,
                    0,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "[]",
                )
            ]
        )
        sql_users.update_user_state(
            callback_query.message.chat.id,
            users_state[callback_query.message.chat.id].state,
        )
        bot.reply_to(
            callback_query.message,
            "Напиши название города отправления. \n\n<i>Например - Москва или "
            "Санкт-Петербург</i>.",
            parse_mode="HTML",
        )

    @bot.message_handler(
        func=lambda message: message.chat.id in users_state
        and users_state[message.chat.id].state == UserStates.WAIT_FOR_AIRPORT
    )
    def airport_handler(message):
        """
        This function is called when user input data about not first and not last airport in route. Data is getting from
        message and passed to function append_airport which in the case of positive data processing
        return True, users state is change on next and send message with asked to choising time of tranzit.

        Also here is checking spelling of city and checking city does not repeat.
        """
        airport = message.text
        logger.info("user=%s ввёл промежуточный город: %s", message.from_user.id, airport)
        answer = CheckData().check_city(airport)
        answer_2 = CheckData().check_if_city_in_route(
            airport, users_state[message.chat.id].search_request_data.airports
        )
        check_on_len_route = CheckData().check_quantity_of_citys(
            users_state[message.chat.id].search_request_data.airports,
            users_state[message.chat.id].search_request_data.home,
            users_state[message.chat.id].search_request_data.finish,
        )
        if (answer == True) and (answer_2 == True) and (check_on_len_route == True):
            users_state[message.chat.id].search_request_data.append_airport(airport)
            users_state[message.chat.id].state = UserStates.WAIT_FOR_TRANSIT_PERIOD
            sql_users.update_user_state(
                message.chat.id, users_state[message.chat.id].state
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Пропустить", callback_data="skeep_tranzit")
            )
            bot.send_message(
                message.chat.id,
                text="🕘Напиши минимальный период транзита через этот город. \n\n<i>Пиши в "
                "формате дней, например - '5д', либо в формате часов, например - '10ч'.</i>",
                reply_markup=markup,
                parse_mode="HTML",
            )
        elif answer != True:
            bot.send_message(
                message.chat.id,
                text="⚠️Название города указано с ошибками, проверь правописание и напиши еще "
                "раз в И.П. с заглавной буквы.",
            )
        elif check_on_len_route != True:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "Начать поиск!", callback_data="start_search"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Выбрать нежеланные авиакомпании", callback_data="hate_airl"
                )
            )
            bot.send_message(
                message.chat.id,
                text="⚠️Лимит на количество городов исчерпан. \nНачнем поиск?",
                reply_markup=markup,
            )
        else:
            bot.send_message(
                message.chat.id,
                text="⚠️Этот город уже добавлен в маршрут. Выбери другой.",
            )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "skeep_tranzit"
    )
    def skeep_tranzit_handler(callback_query):
        """
        This func is calling when user to clicks on "Пропустить" button in airport_handler where asked user
        to select tranzit time or not
        """
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_CHOOSE
            )
        except KeyError:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "Добавить город", callback_data="add_airport"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Выбрать нежеланные авиакомпании", callback_data="hate_airl"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Начать поиск!", callback_data="start_search"
                )
            )
            bot.reply_to(
                callback_query.message,
                text="Супер! Что делаем дальше?",
                reply_markup=markup,
            )

    @bot.message_handler(
        func=lambda message: message.chat.id in users_state
        and users_state[message.chat.id].state == UserStates.WAIT_FOR_TRANSIT_PERIOD
    )
    def transit_period_handler(message):
        """
        Waiting data of time tranzit in city, whose name was entered last. User writhing time of tranzit in days
        or in hours, for example '5д' or '12ч'.
        This filter is optional, default time for tranzit is 60 min.
        """
        time_tranzit = message.text
        logger.info("user=%s ввёл транзит: %s", message.from_user.id, time_tranzit)
        answer = users_state[message.chat.id].search_request_data.append_time_tranzit(
            time_tranzit
        )
        if answer == True:
            users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
            sql_users.update_user_state(
                message.chat.id, users_state[message.chat.id].state
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "Добавить город", callback_data="add_airport"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Выбрать нежеланные авиакомпании", callback_data="hate_airl"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Начать поиск!", callback_data="start_search"
                )
            )
            bot.send_message(
                message.chat.id, text="Супер! Что делаем дальше?", reply_markup=markup
            )
        elif answer == False:
            bot.send_message(
                message.chat.id,
                text="⚠️Транзит в неверном формате.\nВведи еще раз, либо в днях - число с буквой "
                "'д', ибо в часах - число с буквой 'ч'.\n<b>Например '7д' или '12ч'.</b>",
                parse_mode="HTML",
            )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "add_airport"
    )
    def add_air_handler(callback_query):
        """
        One of possible choose in func transit_period_handler, calling when user select
        button 'Добавить город'. Changes status on WAIT_FOR_AIRPORT.
        Sending message with asked to input name of city.
        """
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_AIRPORT
            )
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
        except KeyError:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            bot.reply_to(
                callback_query.message,
                "Напиши название города, который хочешь посетить.\n\n<i>☝️Города НЕ идут "
                "в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени "
                "в полёте.</i>",
                parse_mode="HTML",
            )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "hate_airl"
    )
    def choose_hate_airl_handler(callback_query):
        """
        One of possible choose in func transit_period_handler, calling when user select
        button 'Выбрать нежеланные авиакомпании'. Sending message with asked to input name of company.
        """
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_HATE_AIRL
            )
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
        except KeyError:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            bot.reply_to(
                callback_query.message,
                "Напиши название авиакомпании, которую не стоит добавлять в подборку. "
                "\n\n<i>Пиши с заглавной буквы, например - Победа или Азимут.</i>",
                parse_mode="HTML",
            )

    @bot.message_handler(
        func=lambda message: message.chat.id in users_state
        and users_state[message.chat.id].state == UserStates.WAIT_FOR_HATE_AIRL
    )
    def hate_airl_handler(message):
        """
        Waiting message with name of airlines company which will be excluded for search.
        Spelling is checking immediately.
        """
        hate_airl = message.text
        logger.info("user=%s исключил авиакомпанию: %s", message.from_user.id, hate_airl)
        answer = users_state[message.chat.id].search_request_data.append_hate_airl(
            hate_airl
        )
        if answer == True:
            users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
            sql_users.update_user_state(
                message.chat.id, users_state[message.chat.id].state
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "Добавить город", callback_data="add_airport"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Начать поиск!", callback_data="start_search"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "Добавить еще исключение из авиакомпаний", callback_data="hate_airl"
                )
            )
            bot.send_message(
                message.chat.id, text="Супер! Что делаем дальше?", reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                text="⚠️Название авиакомпании написано некорректно. Попробуй еще раз, пиши с "
                "заглавной буквы.\nЕсли сомневаешься - посмотри официальное название авиакомпании, например:"
                "\n'Ред Вингс' или 'Северный Ветер (Nordwind Airlines)'",
            )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "start_search"
    )
    def start_search_handler(callback_query):
        """
        It is the main func of bot.

        Here is getting all date which user already input and passed to Search(). Search is return
        all created routes, which saved in UserStates storage  - best_in_time and best_in_price.

        Next: one of best_in_time (routes) and one of best_in_price (routes) are calculated and sending to user.
        """
        user_id = callback_query.from_user.id
        try:
            users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_END
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
        except:
            logger.exception("user=%s ошибка в start_search_handler", user_id)
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            sr = Search()
            (
                start_date,
                end_date,
                airports,
                start_period,
                end_period,
                home,
                finish,
                tranzit,
                hate_airl,
            ) = users_state[callback_query.message.chat.id].search_request_data.start()
            logger.info(
                "user=%s ЗАПУСК ПОИСКА: %s→%s, период вылета %s-%s, города=%s, транзит=%s, исключения=%s",
                user_id, home, finish, start_period, end_period, airports, tranzit, hate_airl,
            )
            bot.send_message(
                callback_query.message.chat.id,
                text=text_for_send_message_bot.message_search_began_wait(
                    home, finish, start_period, end_period, airports, tranzit, hate_airl
                ),
                parse_mode="HTML",
            )
            _, all_routes = sr.compute_all_routes(
                start_date,
                end_date,
                airports,
                start_period,
                end_period,
                home,
                finish,
                tranzit,
                hate_airl,
            )
            best_routes_price, _ = sr.find_cheapest_route(all_routes)
            best_routes_time, _ = sr.find_short_in_time_route(all_routes)
            logger.info(
                "user=%s ПОИСК ЗАВЕРШЁН: найдено %d маршрутов", user_id, len(all_routes)
            )
            if best_routes_price == [] and best_routes_time == []:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Попробовать другие параметры поиска!",
                        callback_data="compute_route",
                    )
                )
                bot.reply_to(
                    callback_query.message,
                    f"Ого!😳 С такими жесткими фильтрами не нашлось ни одного маршрута...\n\nПопробуем что-то поменять?",
                    reply_markup=markup,
                )
                sql_users.delete_airports(callback_query.message.chat.id)
                sql_users.delete_tranzit(callback_query.message.chat.id)
                sql_users.delete_user(callback_query.message.chat.id)
            else:
                users_state[callback_query.message.chat.id].best_in_price = iter(
                    best_routes_price
                )
                users_state[callback_query.message.chat.id].best_in_time = iter(
                    best_routes_time
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Еще дешевых", callback_data="show_next_cheap_flight"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Еще быстрых", callback_data="show_next_fast_flight"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Начать новый поиск!", callback_data="compute_route"
                    )
                )
                suggested_by_price = next(
                    users_state[callback_query.message.chat.id].best_in_price
                )
                suggested_by_time = next(
                    users_state[callback_query.message.chat.id].best_in_time
                )
                bot.reply_to(
                    callback_query.message,
                    text=text_for_send_message_bot.answer_with_tickets_for_user(
                        suggested_by_price, suggested_by_time
                    ),
                    reply_markup=markup,
                    parse_mode="HTML",
                )
                sql_users.delete_airports(callback_query.message.chat.id)
                sql_users.delete_tranzit(callback_query.message.chat.id)
                sql_users.delete_user(callback_query.message.chat.id)

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "show_next_cheap_flight"
    )
    def start_search_handler(callback_query):
        """
        This func is sending next best route by time (total flights time for all rote). It is getting data from
        instance of class UserState and sending to user.
        """
        logger.info("user=%s запросил следующий дешёвый вариант", callback_query.from_user.id)
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_MORE_TICKETS
            )
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
        except:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            try:
                suggested_by_price = next(
                    users_state[callback_query.message.chat.id].best_in_price
                )
            except:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Продолжить поиск!", callback_data="compute_route"
                    )
                )
                bot.reply_to(
                    callback_query.message,
                    f"Увы, вы просмотрели все билеты.\nПродолжим поиск с другими фильтрами?",
                    reply_markup=markup,
                )
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Еще дешевых", callback_data="show_next_cheap_flight"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Еще быстрых", callback_data="show_next_fast_flight"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Начать новый поиск!", callback_data="compute_route"
                    )
                )
                bot.reply_to(
                    callback_query.message,
                    text=text_for_send_message_bot.message_answer_tickets_more_cheap(
                        suggested_by_price
                    ),
                    reply_markup=markup,
                    parse_mode="HTML",
                )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "show_next_fast_flight"
    )
    def start_search_handler(callback_query):
        """
        This func is sending next best route by time (total flights time for all rote). It is getting data from
        instance of class UserState and sending to user.
        """
        logger.info("user=%s запросил следующий быстрый вариант", callback_query.from_user.id)
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_MORE_TICKETS
            )
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
        except:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            try:
                suggested_by_time = next(
                    users_state[callback_query.message.chat.id].best_in_time
                )
            except:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Продолжить поиск!", callback_data="compute_route"
                    )
                )
                bot.reply_to(
                    callback_query.message,
                    f"Увы, вы просмотрели все билеты.\nПродолжим поиск с другими фильтрами?",
                    reply_markup=markup,
                )
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Еще дешевых", callback_data="show_next_cheap_flight"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Еще быстрых", callback_data="show_next_fast_flight"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Начать новый поиск!", callback_data="compute_route"
                    )
                )
                bot.reply_to(
                    callback_query.message,
                    text=text_for_send_message_bot.message_answer_tickets_more_short(
                        suggested_by_time
                    ),
                    reply_markup=markup,
                    parse_mode="HTML",
                )

    @bot.message_handler(
        func=lambda message: message.chat.id in users_state
        and users_state[message.chat.id].state == UserStates.WAIT_FOR_HOME
    )
    def home_handler(message):
        """
        Waiting in message text the name of city. Checking is name writing correctly or not.
        If not - send message with asked to input again, if yes - send message with asked to select date of departure.
        """
        home = message.text
        logger.info("user=%s ввёл город отправления: %s", message.from_user.id, home)
        answer = CheckData().check_city(home)
        if answer == True:
            users_state[message.chat.id].search_request_data.append_home(home)
            users_state[message.chat.id].state = (
                UserStates.WAIT_FOR_FIRST_DATE_FROM_PERIOD_HOME
            )
            sql_users.update_user_state(
                message.chat.id, users_state[message.chat.id].state
            )
            calendar, step = DetailedTelegramCalendar(
                locale="ru",
                min_date=datetime.date.today(),
                max_date=datetime.datetime.strptime("2027.12.31", "%Y.%m.%d").date(),
            ).build()
            bot.send_message(
                message.chat.id,
                text=f"Выбери дату или период вылета.",
                reply_markup=calendar,
            )
        else:
            bot.send_message(
                message.chat.id,
                text="⚠️Название города указано с ошибками, проверь правописание и напиши "
                "еще раз в И.П. с заглавной буквы",
            )

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
    def call_handler(c):
        """
        This func is handles clicks on calendars button and edit message with calendar. It looks on result, if date
        is selected, it based on user state to send on next step - to chose leave a date or added period, to enter
        date again.
        """
        result, key, step = DetailedTelegramCalendar().process(c.data)
        if not result and key:
            logger.info("user=%s шаг календаря: %s", c.from_user.id, step)
            try:
                bot.edit_message_text(
                    f"Выбери:",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=key,
                )
            except:
                pass
        elif result and (
            users_state[c.message.chat.id].state
            == UserStates.WAIT_FOR_FIRST_DATE_FROM_PERIOD_HOME
        ):
            logger.info("user=%s выбрал дату вылета: %s", c.from_user.id, result)
            answer_bool = users_state[
                c.message.chat.id
            ].search_request_data.set_start_date(first_value=result, second_value=None)
            if answer_bool:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Оставить дату", callback_data="circle_or_not"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Добавить период", callback_data="add_period_calendar"
                    )
                )
                bot.edit_message_text(
                    f"📆Выбрано: {result}.\nТы можешь добавить период, выбрав вторую дату, тогда первая станет "
                    f"датой начала периода.",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=markup,
                )

        elif result and (
            users_state[c.message.chat.id].state
            == UserStates.WAIT_FOR_SECOND_DATE_FROM_PERIOD_HOME
        ):
            logger.info("user=%s выбрал вторую дату периода вылета: %s", c.from_user.id, result)
            answer_bool = users_state[
                c.message.chat.id
            ].search_request_data.set_start_date(
                first_value=None, second_value=str(result)
            )
            if answer_bool == False:
                users_state[
                    c.message.chat.id
                ].state == UserStates.WAIT_FOR_CIRCLE_OR_NOT
                sql_users.update_user_state(
                    c.message.chat.id, users_state[c.message.chat.id].state
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Оставить первую дату из периода", callback_data="circle_or_not"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Указать период заново", callback_data="calendar_input_again"
                    )
                )
                bot.edit_message_text(
                    f"⚠️Неверно указан период.\n\nМежду первой и второй датой должно быть от 1 до 21 дня.\n\n"
                    f"<i>Напиши период заново или оставь только первую дату для вылета.</i>",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=markup,
                    parse_mode="HTML",
                )
            else:
                users_state[
                    c.message.chat.id
                ].state == UserStates.WAIT_FOR_DATE_OR_PERIOD_FROM_HOME
                sql_users.update_user_state(
                    c.message.chat.id, users_state[c.message.chat.id].state
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("Кольцевой", callback_data="circle")
                )
                markup.add(
                    types.InlineKeyboardButton("В один конец", callback_data="one_way")
                )
                bot.edit_message_text(
                    f"📆Выбран период {users_state[c.message.chat.id].search_request_data.start_date} - {result}."
                    f"\n\nВыбери, какой у тебя маршрут.\n\n<i>Кольцевой - с возвращением в первый пункт вылета. "
                    f"\nВ один конец - аэропорт вылета не совпадает с с аэропортом прилета.</i>",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=markup,
                    parse_mode="HTML",
                )

        elif result and (
            users_state[c.message.chat.id].state
            == UserStates.WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD
        ):
            answer = users_state[
                c.message.chat.id
            ].search_request_data.append_date_or_period_to_finish(
                first_value=result, second_value=None
            )
            check_duration = None
            if answer == True:
                users_state[c.message.chat.id].state = (
                    UserStates.WAIT_FOR_DATE_OR_PERIOD_TO_FINISH
                )
                sql_users.update_user_state(
                    c.message.chat.id, users_state[c.message.chat.id].state
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "Оставить дату", callback_data="add_airport"
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "Добавить период", callback_data="add_period_calendar_to_finish"
                    )
                )
                bot.edit_message_text(
                    f"📆Выбрано: {result}.\nТы можешь добавить период, выбрав вторую дату, тогда первая станет "
                    f"датой начала периода.",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=markup,
                )
            else:
                users_state[c.message.chat.id].state = (
                    UserStates.WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD
                )
                sql_users.update_user_state(
                    c.message.chat.id, users_state[c.message.chat.id].state
                )
                calendar, step = DetailedTelegramCalendar(
                    locale="ru",
                    min_date=datetime.date.today(),
                    max_date=datetime.datetime.strptime(
                        "2027.12.31", "%Y.%m.%d"
                    ).date(),
                ).build()
                bot.edit_message_text(
                    f"⚠️Неверно указана дата.\n\nМежду первым и крайним вылетом должно быть не более 31 дня."
                    f"\n\n<i>Выбери дату или период заново</i>",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=calendar,
                    parse_mode="HTML",
                )

        elif result and (
            users_state[c.message.chat.id].state
            == UserStates.WAIT_FOR_SECOND_DATE_FROM_PERIOD_FINISH
        ):
            answer = users_state[
                c.message.chat.id
            ].search_request_data.append_date_or_period_to_finish(
                first_value=None, second_value=result
            )
            check_duration = None
            if answer == True:
                check_duration = CheckData().check_period_duration(
                    users_state[c.message.chat.id].search_request_data.start_date,
                    users_state[c.message.chat.id].search_request_data.end_date,
                )
                if (answer == True) and (check_duration == True):
                    bot.edit_message_text(
                        f"📆Выбран период {(users_state[c.message.chat.id].search_request_data.end_period)[0]} - "
                        f"{result}.\n\nНапиши название города, который хочешь посетить.\n\n<i>☝️Города НЕ идут в "
                        f"хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены "
                        f"или времени в полёте.</i>",
                        c.message.chat.id,
                        c.message.message_id,
                        parse_mode="HTML",
                    )
                    users_state[c.message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
                    sql_users.update_user_state(
                        c.message.chat.id, users_state[c.message.chat.id].state
                    )
                elif check_duration == False:
                    calendar, step = DetailedTelegramCalendar(
                        locale="ru",
                        min_date=datetime.date.today(),
                        max_date=datetime.datetime.strptime(
                            "2027.12.31", "%Y.%m.%d"
                        ).date(),
                    ).build()
                    users_state[c.message.chat.id].state = (
                        UserStates.WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD
                    )
                    sql_users.update_user_state(
                        c.message.chat.id, users_state[c.message.chat.id].state
                    )
                    bot.edit_message_text(
                        f"⚠️Указан недопустимый период, от начала до завершения маршрута должно быть не более "
                        f"31 дня. \n\nУкажите дату или период заново, чтобы диапазон от даты первого вылета в "
                        f"маршруте был не более 4 недель.",
                        c.message.chat.id,
                        c.message.message_id,
                        reply_markup=calendar,
                        parse_mode="HTML",
                    )
            else:
                users_state[c.message.chat.id].state = (
                    UserStates.WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD
                )
                sql_users.update_user_state(
                    c.message.chat.id, users_state[c.message.chat.id].state
                )
                calendar, step = DetailedTelegramCalendar(
                    locale="ru",
                    min_date=datetime.date.today(),
                    max_date=datetime.datetime.strptime(
                        "2027.12.31", "%Y.%m.%d"
                    ).date(),
                ).build()
                bot.edit_message_text(
                    f"⚠️Неверно указана дата.\n\nДата начала периода больше, чем дата окончания.\n\n"
                    f"<i>Выбери дату или период заново</i>",
                    c.message.chat.id,
                    c.message.message_id,
                    reply_markup=calendar,
                    parse_mode="HTML",
                )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "add_period_calendar_to_finish"
    )
    def first_period_calendar_handler(callback_query):
        """
        Called when user select period for LAST flight, not just one date and to send to user new message
        with calendar
        """
        users_state[callback_query.message.chat.id].state = (
            UserStates.WAIT_FOR_SECOND_DATE_FROM_PERIOD_FINISH
        )
        sql_users.update_user_state(
            callback_query.message.chat.id,
            users_state[callback_query.message.chat.id].state,
        )
        calendar, step = DetailedTelegramCalendar(
            locale="ru",
            min_date=datetime.date.today(),
            max_date=datetime.datetime.strptime("2027.12.31", "%Y.%m.%d").date(),
        ).build()
        bot.send_message(
            callback_query.message.chat.id,
            text=f"Выбери дату окончания периода.",
            reply_markup=calendar,
        )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "add_period_calendar"
    )
    def first_period_calendar_handler(callback_query):
        """
        Called when user select period for FIRST flight, not just one date and to send to user new message
        with calendar
        """
        users_state[callback_query.message.chat.id].state = (
            UserStates.WAIT_FOR_SECOND_DATE_FROM_PERIOD_HOME
        )
        sql_users.update_user_state(
            callback_query.message.chat.id,
            users_state[callback_query.message.chat.id].state,
        )
        calendar, step = DetailedTelegramCalendar(
            locale="ru",
            min_date=datetime.date.today(),
            max_date=datetime.datetime.strptime("2027.12.31", "%Y.%m.%d").date(),
        ).build()
        bot.send_message(
            callback_query.message.chat.id,
            text=f"Выбери дату окончания периода.",
            reply_markup=calendar,
        )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "calendar_input_again"
    )
    def period_calendar_handler(callback_query):
        """
        Called when user to make mistake in choosing period.
        Here is sending new calendar for select date of first flight
        """
        users_state[callback_query.message.chat.id].state = (
            UserStates.WAIT_FOR_FIRST_DATE_FROM_PERIOD_HOME
        )
        sql_users.update_user_state(
            callback_query.message.chat.id,
            users_state[callback_query.message.chat.id].state,
        )
        calendar, step = DetailedTelegramCalendar(
            locale="ru",
            min_date=datetime.date.today(),
            max_date=datetime.datetime.strptime("2027.12.31", "%Y.%m.%d").date(),
        ).build()
        bot.send_message(
            callback_query.message.chat.id,
            text=f"Выбери дату или период вылета.",
            reply_markup=calendar,
        )

    @bot.callback_query_handler(
        lambda callback_query: callback_query.data == "circle_or_not"
    )
    def choose_circle_or_not_handler(callback_query):
        """
        Send message for allows to choose circle route or not.
        """
        users_state[callback_query.message.chat.id].state = (
            UserStates.WAIT_FOR_CIRCLE_OR_NOT
        )
        sql_users.update_user_state(
            callback_query.message.chat.id,
            users_state[callback_query.message.chat.id].state,
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Кольцевой", callback_data="circle"))
        markup.add(types.InlineKeyboardButton("В один конец", callback_data="one_way"))
        bot.send_message(
            callback_query.message.chat.id,
            text="Выбери, какой у тебя маршрут.\n\n<i>Кольцевой - с возвращением в первый пункт вылета. \nВ один "
            "конец - аэропорт вылета не совпадает с с аэропортом прилета.</i>",
            reply_markup=markup,
            parse_mode="HTML",
        )

    @bot.callback_query_handler(lambda callback_query: callback_query.data == "circle")
    def circle_handler(callback_query):
        """
        Func is called when user pressed on "Кольцевой" button. Inside passed True to func append_circle
        and created calendar to select the date of last flight.
        """
        logger.info("user=%s выбрал кольцевой маршрут", callback_query.from_user.id)
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD
            )
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )

        except KeyError:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            users_state[
                callback_query.message.chat.id
            ].search_request_data.append_circle(True)
            calendar, step = DetailedTelegramCalendar(
                locale="ru",
                min_date=datetime.date.today(),
                max_date=datetime.datetime.strptime("2027.12.31", "%Y.%m.%d").date(),
            ).build()
            bot.reply_to(
                callback_query.message,
                "Выбери дату последнего возвратного вылета.",
                reply_markup=calendar,
            )

    @bot.callback_query_handler(lambda callback_query: callback_query.data == "one_way")
    def one_way_handler(callback_query):
        # users_state[callback_query.message.chat_id].search_request_data.append_circle(False)
        logger.info("user=%s выбрал маршрут в один конец", callback_query.from_user.id)
        try:
            users_state[callback_query.message.chat.id].state = (
                UserStates.WAIT_FOR_FINISH_AIRPORT
            )
            sql_users.update_user_state(
                callback_query.message.chat.id,
                users_state[callback_query.message.chat.id].state,
            )
        except KeyError:
            bot.send_message(
                callback_query.message.chat.id,
                "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start",
            )
        else:
            bot.reply_to(
                callback_query.message,
                "Напиши крайний город в твоём маршруте. \n\n<i>Модель сама определит "
                "доступные аэропорта для него.</i>",
                parse_mode="HTML",
            )

    @bot.message_handler(
        func=lambda message: message.chat.id in users_state
        and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_AIRPORT
    )
    def finish_airport_handler(message):
        """
        This function is called when user input data about last airport. Data is getting from
        message and passed to function append_finish_airport which in the case of positive data processing
        return True, users state is change on next and send message with asked to choose date for departure
        """
        airport = message.text
        logger.info("user=%s ввёл конечный город: %s", message.from_user.id, airport)
        answer = CheckData().check_city(airport)
        if answer == True:
            answer = users_state[
                message.chat.id
            ].search_request_data.append_finish_airport(airport)
            if answer == True:
                users_state[message.chat.id].state = (
                    UserStates.WAIT_FOR_FINISH_DEPARTURE_FIRST_FROM_PERIOD
                )
                sql_users.update_user_state(
                    message.chat.id, users_state[message.chat.id].state
                )
                calendar, step = DetailedTelegramCalendar(
                    locale="ru",
                    min_date=datetime.date.today(),
                    max_date=datetime.datetime.strptime(
                        "2027.12.31", "%Y.%m.%d"
                    ).date(),
                ).build()
                bot.send_message(
                    message.chat.id,
                    text="Выбери дату вылета последнего полёта в маршруте",
                    reply_markup=calendar,
                )
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("Кольцевой", callback_data="circle")
                )
                bot.send_message(
                    message.chat.id,
                    text="⚠️Название города прилета совпадает с городом вылета, такой фильтр "
                    "невозможен для маршрута в одну сторону. Если ты хочешь найти кольцевой маршрут, нажми на "
                    "кнопку Кольцевой.",
                    reply_markup=markup,
                )

        else:
            bot.send_message(
                message.chat.id,
                text="⚠️Название города указано с ошибками, проверь правописание "
                "и напиши еще раз в И.П. с заглавной буквы",
            )

    @bot.message_handler(commands=["request_to_sql"])
    def send_welcome(message):
        """
        Function send SQL database in Excel format.
        """
        document_send = sql_users.convert_to_excel()
        bot.send_document(message.chat.id, document_send)

    bot.polling(none_stop=True, interval=0)
