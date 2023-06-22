import telebot
from telebot import types
from route import Route
from search import Search
from serchrequestdata import SearchRequestData
from check_answer import CheckData
import sql_users
from enum import IntEnum
import text_for_send_message_bot

if __name__ == "__main__":
        telebot.apihelper.ENABLE_MIDDLEWARE = True
        telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60
        bot = telebot.TeleBot("6182172702:AAE-aoQSvCTuyIWKv6zCrXMDM4CB6sYbJtY", parse_mode=None)

        # Хранилище флагов, что вводят юзеры (тут все, кто в данный момент что-то вводит)
        users_state = {}

        class UserStates(IntEnum):
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

        class UserState:
            def __init__(self, user_id):
                self.state = None
                self.user_id = user_id
                self.search_request_data = SearchRequestData(user_id=self.user_id)
                self.best_in_price = None
                self.best_in_time = None

        # sql_users.create_table_in_database()
        date_from_sql_users = sql_users.get_all_data_from_table()
        date_from_sql_users_airport = sql_users.get_all_data_from_users_airport()
        date_from_sql_users_tranzit = sql_users.get_all_data_from_users_tranzit()
        # TODO Чекни, что произойдет, если у юзера будет состояние WAIT_FOR_CHOOSE (он должен нажать на кнопку)

        for i in date_from_sql_users:
            if (date_from_sql_users != None) or (date_from_sql_users != []):
                user_id = i[0]
                state = i[3]
                users_state[user_id] = UserState(user_id = user_id)
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
        for string in date_from_sql_users_airport:
            user_id = string[0]
            users_state[user_id].search_request_data.append_airport(string[1])
        for string in date_from_sql_users_tranzit:
            user_id = string[0]
            users_state[user_id].search_request_data.append_time_tranzit_exception_sql((string[1], int(string[2])))

        @bot.message_handler(commands=['start'])
        def send_welcome(message):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Начать поиск', callback_data='compute_route'))
            bot.reply_to(message, text = text_for_send_message_bot.message_hello(), reply_markup=markup, parse_mode="HTML")
            sql_users.add_users_to_sql([(message.from_user.id, message.from_user.username, message.from_user.full_name, 0, '', '', '', '', '', '', '[]')])
            sql_users.users_all_the_time(message.from_user.id, message.from_user.username, message.from_user.full_name)
        @bot.callback_query_handler(lambda callback_query: callback_query.data == "compute_route")
        def compute_route_handler(callback_query):
            users_state[callback_query.message.chat.id] = UserState(callback_query.message.chat.id) #экземпляр класса UserState() создается тут!!
            users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HOME
            sql_users.add_users_to_sql([(callback_query.from_user.id, callback_query.from_user.username, callback_query.from_user.full_name, 0, '',
                                         '', '', '', '', '', '[]')])
            sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            bot.reply_to(callback_query.message, "Напиши название города отправления. \n\n<i>Например - Москва или Санкт-Петербург</i>.", parse_mode="HTML")

        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_AIRPORT)
        def airport_handler(message):
            airport = message.text
            answer = CheckData().check_city(airport)
            answer_2 = CheckData().check_if_city_in_route(airport, users_state[message.chat.id].search_request_data.airports)
            check_on_len_route = CheckData().check_quantity_of_citys(users_state[message.chat.id].search_request_data.airports, users_state[message.chat.id].search_request_data.home, users_state[message.chat.id].search_request_data.finish)
            if (answer == True) and (answer_2 == True) and (check_on_len_route == True):
            # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
                users_state[message.chat.id].search_request_data.append_airport(airport)
                users_state[message.chat.id].state = UserStates.WAIT_FOR_TRANSIT_PERIOD
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Пропустить', callback_data='skeep_tranzit'))
                bot.send_message(message.chat.id, text="🕘Напиши минимальный период транзита через этот город. \n\n<i>Пиши в формате дней, например - '5д', либо в формате часов, например - '10ч'.</i>",reply_markup=markup, parse_mode="HTML")
            elif answer != True:
                bot.send_message(message.chat.id, text="⚠️Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы.")
            elif check_on_len_route != True:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
                bot.send_message(message.chat.id, text="⚠️Лимит на количество городов исчерпан. \nНачнем поиск?", reply_markup = markup)
            else:
                bot.send_message(message.chat.id, text="⚠️Этот город уже добавлен в маршрут. Выбери другой.")
        @bot.callback_query_handler(lambda callback_query: callback_query.data == "skeep_tranzit")
        def skeep_tranzit_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
            except KeyError:
                bot.send_message(callback_query.message.chat.id, "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
                markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                bot.reply_to(callback_query.message, text="Супер! Что делаем дальше?", reply_markup = markup)
        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_TRANSIT_PERIOD)
        def transit_period_handler(message):
            time_tranzit = message.text
            answer = users_state[message.chat.id].search_request_data.append_time_tranzit(time_tranzit)
            if answer == True:
                users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
                markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                bot.send_message(message.chat.id, text="Супер! Что делаем дальше?", reply_markup = markup)
            elif answer == False:
                bot.send_message(message.chat.id, text="⚠️Транзит в неверном формате.\nВведи еще раз, либо в днях - число с буквой 'д', ибо в часах - число с буквой 'ч'.\n<b>Например '7д' или '12ч'.</b>", parse_mode='HTML')

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "add_airport")
        def add_air_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except KeyError:
                bot.send_message(callback_query.message.chat.id, "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                bot.reply_to(callback_query.message, "Напиши название города, который хочешь посетить.\n\n<i>☝️Города НЕ идут в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени в полёте.</i>", parse_mode="HTML")
        @bot.callback_query_handler(lambda callback_query: callback_query.data == "hate_airl")
        def choose_hate_airl_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HATE_AIRL
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except KeyError:
                bot.send_message(callback_query.message.chat.id, "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                bot.reply_to(callback_query.message, "Напиши название авиакомпании, которую не стоит добавлять в подборку. \n\n<i>Пиши с заглавной буквы, например - Победа или Азимут.</i>", parse_mode="HTML")
        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_HATE_AIRL)
        def hate_airl_handler(message):
            hate_airl = message.text
            answer = users_state[message.chat.id].search_request_data.append_hate_airl(hate_airl)
            if answer == True:
                users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
                markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
                markup.add(types.InlineKeyboardButton('Добавить еще исключение из авиакомпаний', callback_data='hate_airl'))
                bot.send_message(message.chat.id, text="Супер! Что делаем дальше?", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, text="⚠️Название авиакомпании написано некорректно. Попробуй еще раз, пиши с заглавной буквы.\nЕсли сомневаешься - посмотри официальное название авиакомпании, например:\n'Ред Вингс' или 'Северный Ветер (Nordwind Airlines)'")

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "start_search")
        def start_search_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_END
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except:
                bot.send_message(callback_query.message.chat.id, "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                sr = Search()
                start_date, end_date, airports,start_period, end_period, home, finish, tranzit, hate_airl = users_state[callback_query.message.chat.id].search_request_data.start()
                bot.send_message(callback_query.message.chat.id,
                                 text=text_for_send_message_bot.message_search_began_wait(home, finish, start_period,
                                                                                          end_period, airports, tranzit,
                                                                                          hate_airl), parse_mode="HTML")
                _, all_routes = sr.compute_all_routes(start_date, end_date, airports,start_period, end_period, home, finish, tranzit, hate_airl)
                best_routes_price, _ = sr.find_cheapest_route(all_routes)
                best_routes_time, _ = sr.find_short_in_time_route(all_routes)
                if best_routes_price == [] and best_routes_time == []:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Попробовать другие параметры поиска!', callback_data='compute_route'))
                    bot.reply_to(callback_query.message,
                                 f'Ого!😳 С такими жесткими фильтрами не нашлось ни одного маршрута...\n\nПопробуем что-то поменять?',
                                 reply_markup=markup)
                    sql_users.delete_airports(callback_query.message.chat.id)
                    sql_users.delete_tranzit(callback_query.message.chat.id)
                    sql_users.delete_user(callback_query.message.chat.id)
                else:
                    users_state[callback_query.message.chat.id].best_in_price = iter(best_routes_price)
                    users_state[callback_query.message.chat.id].best_in_time = iter(best_routes_time)
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                    markup.add(types.InlineKeyboardButton('Начать новый поиск!', callback_data='compute_route'))
                    suggested_by_price = next(users_state[callback_query.message.chat.id].best_in_price)
                    suggested_by_time = next(users_state[callback_query.message.chat.id].best_in_time)
                    bot.reply_to(callback_query.message,
                                  text=text_for_send_message_bot.answer_with_tickets_for_user(suggested_by_price, suggested_by_time),
                                 reply_markup=markup, parse_mode="HTML")
                    sql_users.delete_airports(callback_query.message.chat.id)
                    sql_users.delete_tranzit(callback_query.message.chat.id)
                    sql_users.delete_user(callback_query.message.chat.id)

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "show_next_cheap_flight")
        def start_search_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_MORE_TICKETS
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except:
                bot.send_message(callback_query.message.chat.id,
                                     "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                try:
                    suggested_by_price = next(users_state[callback_query.message.chat.id].best_in_price)
                except:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Продолжить поиск!', callback_data='compute_route'))
                    bot.reply_to(callback_query.message,
                                 f'Увы, вы просмотрели все билеты.\nПродолжим поиск с другими фильтрами?',
                                 reply_markup=markup)
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                    markup.add(types.InlineKeyboardButton('Начать новый поиск!', callback_data='compute_route'))
                    bot.reply_to(callback_query.message,
                                 text=text_for_send_message_bot.message_answer_tickets_more_cheap(suggested_by_price),
                                 reply_markup=markup, parse_mode="HTML")

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "show_next_fast_flight")
        def start_search_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_MORE_TICKETS
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except:
                bot.send_message(callback_query.message.chat.id,
                                         "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                try:
                    suggested_by_time = next(users_state[callback_query.message.chat.id].best_in_time)
                except:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Продолжить поиск!', callback_data='compute_route'))
                    bot.reply_to(callback_query.message,
                                         f'Увы, вы просмотрели все билеты.\nПродолжим поиск с другими фильтрами?',
                                         reply_markup=markup)
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
                    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
                    markup.add(types.InlineKeyboardButton('Начать новый поиск!', callback_data='compute_route'))
                    bot.reply_to(callback_query.message,
                                         text=text_for_send_message_bot.message_answer_tickets_more_short(suggested_by_time),
                                 reply_markup=markup, parse_mode="HTML")

        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_HOME)
        def home_handler(message):
            home = message.text
            answer = CheckData().check_city(home)
            if answer == True:
            # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
                users_state[message.chat.id].search_request_data.append_home(home)
                users_state[message.chat.id].state = UserStates.WAIT_FOR_DATA_HOME_DEPARTURE
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                bot.send_message(message.chat.id, text="Напиши дату вылета в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD`")
            else:
                bot.send_message(message.chat.id, text="⚠️Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_DATA_HOME_DEPARTURE)
        def period_for_home_departure_handler(message):
            period_or_date = message.text
            answer_bool = users_state[message.chat.id].search_request_data.set_start_date(period_or_date)
            if answer_bool == True:
                users_state[message.chat.id].state = UserStates.WAIT_FOR_CIRCLE_OR_NOT
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('Кольцевой', callback_data='circle'))
                markup.add(types.InlineKeyboardButton('В один конец', callback_data='one_way'))
                bot.send_message(message.chat.id, text="Выбери, какой у тебя маршрут.\n\n<i>Кольцевой - с возвращением в первый пункт вылета. \nВ один конец - аэропорт вылета не совпадает с с аэропортом прилета.</i>", reply_markup=markup, parse_mode="HTML")
            elif answer_bool == False:
                bot.send_message(message.chat.id,
                                 text="⚠️Дата или период в неверном формате, напиши ее, как в примере:\n- точная дата `YYYY.MM.DD` \n- период `YYYY.MM.DD - YYYY.MM.DD`")


        @bot.callback_query_handler(lambda callback_query: callback_query.data == "circle")
        def circle_handler(callback_query):
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)

            except KeyError:
                bot.send_message(callback_query.message.chat.id, "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                users_state[callback_query.message.chat.id].search_request_data.append_circle(True)
                bot.reply_to(callback_query.message, "Напиши дату или период последнего возвратного вылета. Пиши дату в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD`")

        @bot.callback_query_handler(lambda callback_query: callback_query.data == "one_way")
        def one_way_handler(callback_query):
            # users_state[callback_query.message.chat_id].search_request_data.append_circle(False)
            try:
                users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_AIRPORT
                sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
            except KeyError:
                bot.send_message(callback_query.message.chat.id, "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start")
            else:
                bot.reply_to(callback_query.message, "Напиши крайний город в твоём маршруте. \n\n<i>Модель сама определит доступные аэропорта для него.</i>", parse_mode="HTML")

        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_AIRPORT)
        def finish_airport_handler(message):
            airport = message.text
            answer = CheckData().check_city(airport)
            if answer == True:
            # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
                answer = users_state[message.chat.id].search_request_data.append_finish_airport(airport)
                if answer == True:
                    users_state[message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
                    sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                    bot.send_message(message.chat.id, text="Напиши дату последнего полета в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD`")
                else:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Кольцевой', callback_data='circle'))
                    bot.send_message(message.chat.id,
                                 text="⚠️Название города прилета совпадает с городом вылета, такой фильтр невозможен для маршрута в одну сторону. Если ты хочешь найти кольцевой маршрут, нажми на кнопку Кольцевой.", reply_markup=markup)

            else:
                bot.send_message(message.chat.id, text="⚠️Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

        @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_DEPARTURE)
        def finish_date_or_period_handler(message):
            date_or_period = message.text
            answer = users_state[message.chat.id].search_request_data.append_date_or_period_to_finish(date_or_period)
            check_duration = None
            if answer == True:
                check_duration = CheckData().check_period_duration(users_state[message.chat.id].search_request_data.start_date, users_state[message.chat.id].search_request_data.end_date)
            if (answer == True) and (check_duration == True):
                users_state[message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
                sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
                bot.send_message(message.chat.id, text="Напиши название города, который хочешь посетить.\n\n<i>☝️Города НЕ идут в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени в полёте.</i>", parse_mode="HTML")
            elif check_duration == False:
                bot.send_message(message.chat.id,
                                 text="⚠️Указан недопустимый период, от начала до завершения маршрута должно быть не более 31 дня. \n\nУкажите дату или период, чтобы диапазон от даты первого вылета был не более 3 недель.")
            else:
                bot.send_message(message.chat.id,
                                 text="⚠️Дата или период в неверном формате, напиши ее, как в примере:\n- точная дата `YYYY.MM.DD` \n- период `YYYY.MM.DD - YYYY.MM.DD`")
        @bot.message_handler(commands=['request_to_sql'])
        def send_welcome(message):
            document_send = sql_users.convert_to_excel()
            bot.send_document(message.chat.id, document_send)

        bot.polling(none_stop=True, interval=0)

