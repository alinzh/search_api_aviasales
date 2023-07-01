import telebot
from telebot import types
from route import Route
from search import Search
from serchrequestdata import SearchRequestData
from check_answer import CheckData
import sql_users
from enum import IntEnum
import text_for_send_message_bot as t_mesg

if __name__ == "__main__":
        telebot.apihelper.ENABLE_MIDDLEWARE = True
        telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60
        bot = telebot.TeleBot("6182172702:AAE-aoQSvCTuyIWKv6zCrXMDM4CB6sYbJtY", parse_mode=None)


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
            WAIT_FOR_FINISH_DEPARTURE = 7
            WAIT_FOR_CHOOSE = 8
            WAIT_FOR_HATE_AIRL = 9
            WAIT_FOR_END = 10
            WAIT_FOR_FINISH_AIRPORT = 11
            WAIT_FOR_MORE_TICKETS = 12
            WAIT_FOR_FINISH_DEPARTURE_NOT_CRONOLOGICAL_ROUTE = 13
            WAIT_FOR_END_CRONOLOGICAL = 14

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

        # sql_users.create_table_in_database()
        sql_users.add_column_chronological_and_circle()
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
                    users_state[user_id].search_request_data.append_start_date_exception_sql(i[4])
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_end_date_exception_sql(i[5])
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_start_period_exception_sql(eval(i[6]))
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_end_period_exception_sql(eval(i[7]))
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_home_exception_sql(i[8])
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_finish_exception_sql(i[9])
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_hate_airl_exception_sql(eval(i[10]))
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_chronological_exception_sql(i[11])
                except:
                    pass
                try:
                    users_state[user_id].search_request_data.append_circle_or_not_exception_sql(i[12])
                except:
                    pass

        for string in date_from_sql_users_airport:
            user_id = string[0]
            users_state[user_id].search_request_data.append_airport(string[1])
        for string in date_from_sql_users_tranzit:
            user_id = string[0]
            users_state[user_id].search_request_data.append_time_tranzit_exception_sql((string[1], int(string[2])))

        @bot.message_handler(commands=['start'])
        def send_welcome(message):
            """
            Sending hello-message to user.
            Added to SQL user_id, username, full_name (if not hidden), data about route is empty on start.
            """
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Начать поиск', callback_data='choose_chronological_or_not_route'))
            bot.reply_to(
                message, text=t_mesg.message_hello(), reply_markup=markup, parse_mode="HTML"
            )
            sql_users.add_users_to_sql(
                [(message.from_user.id, message.from_user.username, message.from_user.full_name,
                  0, '', '', '', '', '', '', '[]', 0, 0)]
            )
            sql_users.users_all_the_time(
                message.from_user.id, message.from_user.username, message.from_user.full_name)


        @bot.callback_query_handler(lambda callback_query: callback_query.data == "choose_chronological_or_not_route")
        def choose_chronological_or_not_route_handler(callback_query):
            """
            Sending message with two options for selecting the type of search.
            The user chooses between searching by entering cities in chronological order and
            searching by the optimal sequence of cities.
            Here is created instance class of UserState where will stores all data about user.
            """
            users_state[callback_query.message.chat.id] = UserState(callback_query.message.chat.id)
            # экземпляр класса UserState() создается тут!!
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                'Учитывать последовательность городов', callback_data='chronological')
            )
            markup.add(types.InlineKeyboardButton('Найти оптимальную', callback_data='not_chronological'))
            bot.reply_to(
                callback_query.message, text=t_mesg.message_chronological_search_or_not(),
                reply_markup=markup, parse_mode="HTML"
            )

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "chronological")
        def compute_chronological_route_handler(callback_query):
            """
            Calling when user selects a route in chronological order.
            This information is added to the database.
            Assigned status WAIT_FOR_HOME, it means that after this func will waiting func home_handler.
            """
            users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HOME
            users_state[callback_query.message.chat.id].search_request_data.append_chronological(True)
            sql_users.add_users_to_sql(
                [(callback_query.from_user.id, callback_query.from_user.username, callback_query.from_user.full_name,
                  0, '', '', '', '', '', '', '[]', 1, 0)]
            )
            sql_users.update_user_state(
                callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
            )
            bot.reply_to(
                callback_query.message,
                text=t_mesg.message_write_first_city_in_route(), parse_mode="HTML"
            )


        @bot.callback_query_handler(lambda callback_query: callback_query.data == "not_chronological")
        def compute_not_chronological_route_handler(callback_query):
            """
            Calling when user selects a route in chronological order.
            """
            users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HOME
            sql_users.add_users_to_sql(
                [(callback_query.from_user.id, callback_query.from_user.username, callback_query.from_user.full_name,
                  0, '', '', '', '', '', '', '[]', 0, 0)]
            )
            sql_users.update_user_state(
                callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
            )
            bot.reply_to(
                callback_query.message, text=t_mesg.message_write_first_city_in_route(), parse_mode="HTML"
            )

        @bot.message_handler(func=lambda message: message.chat.id in users_state and
                                                  users_state[message.chat.id].state == UserStates.WAIT_FOR_AIRPORT)
        def airport_handler(message):
            """
            This function is called when user input data about not first and not last airport in route. Data is getting from
            message and passed to function append_airport which in the case of positive data processing
            return True, users state is change on next and send message with asked to choising time of tranzit.

            Also here is checking spelling of city and checking city does not repeat.
            """
            airport = message.text
            answer = CheckData().check_city(airport)
            answer_2 = \
                CheckData().check_if_city_in_route(airport, users_state[message.chat.id].search_request_data.airports)
            check_on_len_route = \
                CheckData().check_quantity_of_citys(
                    users_state[message.chat.id].search_request_data.airports,
                    users_state[message.chat.id].search_request_data.home,
                    users_state[message.chat.id].search_request_data.finish
                )
            if (answer == True) and (answer_2 == True) and (check_on_len_route == True):
                users_state[message.chat.id].search_request_data.append_airport(airport)
                users_state[message.chat.id].state = UserStates.WAIT_FOR_TRANSIT_PERIOD
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Пропустить', callback_data='skeep_tranzit'))
                bot.send_message(
                    message.chat.id, text=t_mesg.message_write_tranzit(), reply_markup=markup, parse_mode="HTML"
                )
            elif answer != True:
                bot.send_message(message.chat.id, text=t_mesg.message_name_of_city_is_wrong())
            elif check_on_len_route != True:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
                bot.send_message(message.chat.id, text=t_mesg.message_no_more_cities(), reply_markup=markup)
            else:
                bot.send_message(message.chat.id, text=t_mesg.message_city_alredy_in_route())
        @bot.callback_query_handler(lambda callback_query: callback_query.data == "skeep_tranzit")
        def skeep_tranzit_handler(callback_query):
            """
            This func is calling when user to clicks on "Пропустить" button in airport_handler where asked user
            to select tranzit time or not
            """
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
            except KeyError:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            else:
                sql_users.update_user_state(
                    callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
                markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                bot.reply_to(callback_query.message, text="Супер! Что делаем дальше?", reply_markup=markup)

        @bot.message_handler(
            func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state ==
                                 UserStates.WAIT_FOR_TRANSIT_PERIOD)
        def transit_period_handler(message):
            """
            Waiting data of time tranzit in city, whose name was entered last. User writhing time of tranzit in days
            or in hours, for example '5д' or '12ч'.
            This filter is optional, default time for tranzit is 60 min.
            """
            time_tranzit = message.text
            answer = users_state[message.chat.id].search_request_data.append_time_tranzit(time_tranzit)
            if answer:
                users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
                markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                bot.send_message(message.chat.id, text="Супер! Что делаем дальше?", reply_markup=markup)
            elif not answer:
                bot.send_message(message.chat.id, text=t_mesg.message_tranzit_in_wrong_format(), parse_mode='HTML')

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "add_airport")
        def add_air_handler(callback_query):
            """
            This function is called when user presses on 'Добавить аэропорт'.
            The user is asked to write the name of the airport.
            """
            try:
                if users_state[callback_query.message.chat.id].state != UserStates.WAIT_FOR_END_CRONOLOGICAL and \
                    users_state[callback_query.message.chat.id].state != UserStates.WAIT_FOR_END and \
                        users_state[callback_query.message.chat.id].state != \
                        UserStates.WAIT_FOR_FINISH_DEPARTURE_NOT_CRONOLOGICAL_ROUTE:

                    try:
                        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
                        sql_users.update_user_state(
                            callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
                        )
                    except KeyError:
                        bot.send_message(
                            callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
                    else:
                        chronological = users_state[callback_query.message.chat.id].search_request_data.chronological
                        if chronological:
                            bot.reply_to(
                                callback_query.message,
                                text=t_mesg.message_write_last_in_route_chronological(), parse_mode="HTML"
                            )
                        else:
                            bot.reply_to(
                                callback_query.message, text=t_mesg.message_write_last_in_route_not_chronological(),
                                parse_mode="HTML")
                else:
                    bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            except:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "hate_airl")
        def choose_hate_airl_handler(callback_query):
            """
            One of possible choose in func transit_period_handler, calling when user select
            button 'Выбрать нежеланные авиакомпании'. Sending message with asked to input name of company.
            """
            try:
                if users_state[callback_query.message.chat.id].state != UserStates.WAIT_FOR_END_CRONOLOGICAL and \
                    users_state[callback_query.message.chat.id].state != UserStates.WAIT_FOR_END and \
                        users_state[callback_query.message.chat.id].state != \
                        UserStates.WAIT_FOR_FINISH_DEPARTURE_NOT_CRONOLOGICAL_ROUTE:
                    try:
                        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HATE_AIRL
                        sql_users.update_user_state(callback_query.message.chat.id,
                                                    users_state[callback_query.message.chat.id].state)
                    except KeyError:
                        bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
                    else:
                        bot.reply_to(
                            callback_query.message, text=t_mesg.message_write_name_of_company(), parse_mode="HTML"
                        )
                else:
                    bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            except:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
        @bot.message_handler(func=lambda message: message.chat.id in users_state and
                                                  users_state[message.chat.id].state == UserStates.WAIT_FOR_HATE_AIRL)
        def hate_airl_handler(message):
            hate_airl = message.text
            answer = users_state[message.chat.id].search_request_data.append_hate_airl(hate_airl)
            if answer:
                users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                markup.add(types.InlineKeyboardButton(
                    'Добавить еще исключение из авиакомпаний', callback_data='hate_airl')
                )
                bot.send_message(message.chat.id, text="Супер! Что делаем дальше?", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, text=t_mesg.message_name_of_company_is_wrong())

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "start_search")
        def start_search_handler(callback_query):
            """
            It is the main func of bot. It handles cases where the selected route is not in chronological order,
            or when the user has selected only one flight between two cities.

            Here is getting all date which user already input and passed to Search(). Search is return
            all created routes, which saved in UserStates storage  - best_in_time and best_in_price.

            Next: one of best_in_time (routes) and one of best_in_price (routes) are calculated and sending to user.
            """
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_END
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            else:
                flag_chronological = users_state[callback_query.message.chat.id].search_request_data.chronological
                air = users_state[callback_query.message.chat.id].search_request_data.airports
                circle = users_state[callback_query.message.chat.id].search_request_data.circle_or_not
                if not flag_chronological or \
                        (flag_chronological and (len(air) == 2)) or (circle and flag_chronological):
                    sr = Search()
                    start_date, end_date, airports, start_period, end_period, home, \
                        finish, tranzit, hate_airl, flag_chronological = \
                        users_state[callback_query.message.chat.id].search_request_data.start()
                    bot.send_message(
                        callback_query.message.chat.id, text=t_mesg.message_search_began_wait(
                            home, finish, start_period, end_period, airports, tranzit, hate_airl
                        ),
                        parse_mode="HTML"
                    )
                    _, all_routes = sr.compute_all_routes(
                        start_date, end_date, airports, start_period, end_period, home,
                        finish, tranzit, hate_airl, flag_chronological
                    )
                    best_routes_price, _ = sr.find_cheapest_route(all_routes)
                    best_routes_time, _ = sr.find_short_in_time_route(all_routes)
                    if best_routes_price == [] and best_routes_time == []:
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton(
                            'Попробовать другие параметры поиска!', callback_data='choose_chronological_or_not_route')
                        )
                        bot.reply_to(callback_query.message,
                                     text=t_mesg.message_not_found(), reply_markup=markup
                                     )
                        sql_users.delete_airports(callback_query.message.chat.id)
                        sql_users.delete_tranzit(callback_query.message.chat.id)
                        sql_users.delete_user(callback_query.message.chat.id)
                    else:
                        users_state[callback_query.message.chat.id].best_in_price = iter(best_routes_price)
                        users_state[callback_query.message.chat.id].best_in_time = iter(best_routes_time)
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                        markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                        markup.add(types.InlineKeyboardButton(
                            'Начать новый поиск!', callback_data='choose_chronological_or_not_route')
                        )
                        suggested_by_price = next(users_state[callback_query.message.chat.id].best_in_price)
                        suggested_by_time = next(users_state[callback_query.message.chat.id].best_in_time)
                        bot.reply_to(callback_query.message,
                                     text=t_mesg.answer_with_tickets_for_user(
                                         suggested_by_price, suggested_by_time
                                     ),
                                     reply_markup=markup, parse_mode="HTML")
                        sql_users.delete_airports(callback_query.message.chat.id)
                        sql_users.delete_tranzit(callback_query.message.chat.id)
                        sql_users.delete_user(callback_query.message.chat.id)
                else:
                    users_state[callback_query.message.chat.id].state = \
                        UserStates.WAIT_FOR_FINISH_DEPARTURE_NOT_CRONOLOGICAL_ROUTE
                    sql_users.update_user_state(callback_query.message.chat.id,
                                                users_state[callback_query.message.chat.id].state)
                    bot.reply_to(
                        callback_query.message, text=t_mesg.message_end_date_for_chronological_route(),
                        parse_mode="HTML"
                    )

        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[
            message.chat.id].state == UserStates.WAIT_FOR_FINISH_DEPARTURE_NOT_CRONOLOGICAL_ROUTE)
        def start_search_for_chronological_route_handler(message):
            """
            The function works in the same way as 'start_search_handler', but for searches in chronological order.
            """
            date_or_period = message.text
            answer = users_state[message.chat.id].search_request_data.append_date_or_period_to_finish(date_or_period)
            check_duration = None
            if answer:
                check_duration = CheckData().check_period_duration(
                    users_state[message.chat.id].search_request_data.start_date,
                    users_state[message.chat.id].search_request_data.end_date)
            if (answer == True) and (check_duration == True):
                users_state[message.chat.id].state = UserStates.WAIT_FOR_END_CRONOLOGICAL
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                # тут считать маршрут для хронологического маршрута, состоящего более чем из одного перелета.
                sr = Search()
                start_date, end_date, airports, start_period, end_period, home, finish, tranzit, hate_airl, flag_chronological = \
                    users_state[message.chat.id].search_request_data.start()
                bot.send_message(
                    message.chat.id, text=t_mesg.message_search_began_wait(
                        home, finish, start_period, end_period, airports, tranzit, hate_airl
                    ), parse_mode="HTML")
                _, all_routes = sr.compute_all_routes(start_date, end_date, airports, start_period, end_period, home,
                                                      finish, tranzit, hate_airl, flag_chronological)
                best_routes_price, _ = sr.find_cheapest_route(all_routes)
                best_routes_time, _ = sr.find_short_in_time_route(all_routes)
                if best_routes_price == [] and best_routes_time == []:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton('Попробовать другие параметры поиска!',
                        callback_data='choose_chronological_or_not_route')
                    )
                    bot.reply_to(
                        message, text=t_mesg.message_not_found(), reply_markup=markup)
                    sql_users.delete_airports(message.chat.id)
                    sql_users.delete_tranzit(message.chat.id)
                    sql_users.delete_user(message.chat.id)
                else:
                    users_state[message.chat.id].best_in_price = iter(best_routes_price)
                    users_state[message.chat.id].best_in_time = iter(best_routes_time)
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                    markup.add(types.InlineKeyboardButton(
                        'Начать новый поиск!', callback_data='choose_chronological_or_not_route')
                    )
                    suggested_by_price = next(users_state[message.chat.id].best_in_price)
                    suggested_by_time = next(users_state[message.chat.id].best_in_time)
                    bot.reply_to(
                        message, text=t_mesg.answer_with_tickets_for_user(suggested_by_price, suggested_by_time),
                        reply_markup=markup, parse_mode="HTML"
                    )
                    sql_users.delete_airports(message.chat.id)
                    sql_users.delete_tranzit(message.chat.id)
                    sql_users.delete_user(message.chat.id)
            elif not check_duration:
                bot.send_message(
                    message.chat.id, text=t_mesg.message_period_longer_than_allowed())
            else:
                bot.send_message(
                    message.chat.id, text=t_mesg.message_date_in_wrong_format())

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "show_next_cheap_flight")
        def start_search_handler(callback_query):
            """
            This func is sending next best route by time (total flights time for all rote). It is getting data from
            instance of class UserState and sending to user.
            """
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_MORE_TICKETS
                sql_users.update_user_state(
                    callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
                )
            except:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            else:
                try:
                    suggested_by_price = next(users_state[callback_query.message.chat.id].best_in_price)
                except:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(
                        'Продолжить поиск!', callback_data='choose_chronological_or_not_route')
                    )
                    bot.reply_to(callback_query.message,
                                 f'Увы, вы просмотрели все билеты.\nПродолжим поиск с другими фильтрами?',
                                 reply_markup=markup)
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                    markup.add(types.InlineKeyboardButton(
                        'Начать новый поиск!', callback_data='choose_chronological_or_not_route')
                    )
                    bot.reply_to(
                        callback_query.message, text=t_mesg.message_answer_tickets_more_cheap(suggested_by_price),
                        reply_markup=markup, parse_mode="HTML"
                    )

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "show_next_fast_flight")
        def start_search_handler(callback_query):
            """
            This func is sending next best route by time (total flights time for all rote). It is getting data from
            instance of class UserState and sending to user.
            """
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_MORE_TICKETS
                sql_users.update_user_state(
                    callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
                )
            except:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            else:
                try:
                    suggested_by_time = next(users_state[callback_query.message.chat.id].best_in_time)
                except:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(
                        'Продолжить поиск!', callback_data='choose_chronological_or_not_route')
                    )
                    bot.reply_to(callback_query.message, text=t_mesg.message_tickets_finish(), reply_markup=markup)
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                    markup.add(types.InlineKeyboardButton(
                        'Начать новый поиск!', callback_data='choose_chronological_or_not_route')
                    )
                    bot.reply_to(
                        callback_query.message, text=t_mesg.message_answer_tickets_more_short(suggested_by_time),
                        reply_markup=markup, parse_mode="HTML"
                    )

        @bot.message_handler(func=lambda message: message.chat.id in users_state and
                                                  users_state[message.chat.id].state == UserStates.WAIT_FOR_HOME)
        def home_handler(message):
            """
            Waiting in message text the name of city. Checking is name writing correctly or not.
            If not - send message with asked to input again, if yes - send message with asked to select date of departure.
            """
            home = message.text
            answer = CheckData().check_city(home)
            if answer:
                users_state[message.chat.id].search_request_data.append_home(home)
                users_state[message.chat.id].state = UserStates.WAIT_FOR_DATA_HOME_DEPARTURE
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                bot.send_message(message.chat.id, text=t_mesg.message_write_date())
            else:
                bot.send_message(message.chat.id, text=t_mesg.message_name_of_city_is_wrong())

        @bot.message_handler(
            func=lambda message: message.chat.id in users_state and
                                 users_state[message.chat.id].state == UserStates.WAIT_FOR_DATA_HOME_DEPARTURE)
        def period_for_home_departure_handler(message):
            """
            Send message for allows to choose circle route or not.
            """
            period_or_date = message.text
            answer_bool = users_state[message.chat.id].search_request_data.set_start_date(period_or_date)
            if answer_bool:
                users_state[message.chat.id].state = UserStates.WAIT_FOR_CIRCLE_OR_NOT
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Кольцевой', callback_data='circle'))
                markup.add(types.InlineKeyboardButton('В один конец', callback_data='one_way'))
                bot.send_message(
                    message.chat.id, text=t_mesg.message_circle_or_not(), reply_markup=markup, parse_mode="HTML"
                )
            elif not answer_bool:
                bot.send_message(message.chat.id,
                                 text=t_mesg.message_date_in_wrong_format())


        @bot.callback_query_handler(lambda callback_query: callback_query.data == "circle")
        def circle_handler(callback_query):
            """
            Func is called when user pressed on "Кольцевой" button.
            """
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
                sql_users.update_user_state(
                    callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
                )
            except KeyError:
                bot.send_message(callback_query.message.chat.id, text=t_mesg.message_something_went_wrong())
            else:
                users_state[callback_query.message.chat.id].search_request_data.append_circle(True)
                bot.reply_to(callback_query.message, text=t_mesg.message_write_last_date())

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "one_way")
        def one_way_handler(callback_query):
            if not users_state[callback_query.message.chat.id].search_request_data.chronological:
                try:
                    users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_AIRPORT
                    sql_users.update_user_state(callback_query.message.chat.id,
                                                users_state[callback_query.message.chat.id].state)
                except KeyError:
                    bot.send_message(
                        callback_query.message.chat.id, text=t_mesg.message_something_went_wrong()
                    )
                else:
                    bot.reply_to(
                        callback_query.message, text=t_mesg.message_write_last_city_in_route(), parse_mode="HTML"
                    )
            else:
                try:
                    users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
                    sql_users.update_user_state(
                        callback_query.message.chat.id, users_state[callback_query.message.chat.id].state
                    )
                except KeyError:
                    bot.send_message(
                        callback_query.message.chat.id, text=t_mesg.message_something_went_wrong(),  parse_mode="HTML"
                    )
                else:
                    bot.reply_to(
                        callback_query.message, text=t_mesg.message_write_last_in_route_chronological(),
                        parse_mode="HTML"
                    )
        @bot.message_handler(func=lambda message: message.chat.id in users_state and
                                                  users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_AIRPORT)
        def finish_airport_handler(message):
            """
            The function processes the user's message with the name of the last airport in the route.
            If the name is in the correct form, then the date for the last departure is expected.
            """
            airport = message.text
            answer = CheckData().check_city(airport)
            if answer == True:
                answer = users_state[message.chat.id].search_request_data.append_finish_airport(airport)
                if answer == True:
                    users_state[message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
                    sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                    bot.send_message(message.chat.id, text=t_mesg.message_write_last_date())
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Кольцевой', callback_data='circle'))
                    bot.send_message(message.chat.id,
                                 text=t_mesg.message_city_of_departure_and_arrival_same(), reply_markup=markup)

            else:
                bot.send_message(message.chat.id, text=t_mesg.message_name_of_city_is_wrong())

        @bot.message_handler(
            func=lambda message: message.chat.id in users_state and
                                 users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_DEPARTURE)
        def finish_date_or_period_handler(message):
            """
            Here it is checked for correctness and data on the date of the last departure is processed.
            In response, the user is sent a message with a request to write the name
            of the city that will be on the route.
            """
            date_or_period = message.text
            answer = users_state[message.chat.id].search_request_data.append_date_or_period_to_finish(date_or_period)
            check_duration = None
            if answer:
                check_duration = CheckData().\
                    check_period_duration(
                    users_state[message.chat.id].search_request_data.start_date,
                    users_state[message.chat.id].search_request_data.end_date
                )
            if (answer == True) and (check_duration == True):
                users_state[message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                chronological = users_state[message.chat.id].search_request_data.chronological
                if not chronological:
                    bot.send_message(
                        message.chat.id, text=t_mesg.message_write_last_in_route_not_chronological(), parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        message.chat.id, text=t_mesg.message_write_last_in_route_chronological(), parse_mode="HTML"
                    )
            elif not check_duration:
                bot.send_message(message.chat.id,
                                 text=t_mesg.message_period_longer_than_allowed())
            else:
                bot.send_message(message.chat.id,
                                 text=t_mesg.message_date_in_wrong_format())
        @bot.message_handler(commands=['request_to_sql'])
        def send_welcome(message):
            document_send = sql_users.convert_to_excel()
            bot.send_document(message.chat.id, document_send)

        while True:
            try:
                bot.polling(none_stop=True, interval=0)
            except:
                continue

