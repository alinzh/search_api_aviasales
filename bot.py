import telebot
from telebot import types
from route import Route
from search import Search
from serchrequestdata import SearchRequestData
from check_answer import CheckData
import sql_users


bot = telebot.TeleBot("6182172702:AAE-aoQSvCTuyIWKv6zCrXMDM4CB6sYbJtY", parse_mode=None)

# Хранилище флагов, что вводят юзеры (тут все, кто в данный момент что-то вводит)
users_state = {}

from enum import IntEnum
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
date_from_sql = sql_users.get_all_data_from_table()
# TODO создай таблицу с транзитом в конкретном городе конкретного юзера.
# TODO Извлеки от туда всё и добавить в searchrequestdata конкретного юзера (через экз.класса UserState).
# TODO Извлеки из таблицы users_airport всё и также добавь.
# TODO Чекни, что произойдет, если у юзера будет состояние WAIT_FOR_CHOOSE (он должен нажать на кнопку)
# TODO Убери в хедере лишнюю проверку на состояние пользователя ->> or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_AIRPORT)

for i in date_from_sql:
    if (date_from_sql != None) or (date_from_sql != []):
        user_id = i[0]
        state = i[3]
        users_state[user_id] = UserState(user_id = user_id)
        users_state[user_id].state = state


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Начать поиск', callback_data='compute_route'))
    bot.reply_to(message, "Привет!👋\n\
Я — бот, поисковик авиабилетов, который умеет искать с более гибкими фильтрами чем aviasales. Я умею строить сложные маршруты с гибкими датами и находить оптимальную последовательность пунктов маршрута.\
\n\nЯ могу тебе помочь👇\
\n— построить маршрут из большого кол-ва городов\
\n— найти самую дешевую последовательность городов в маршруте\
\n— направить тебе самые быстрые или самые дешевые варианты маршрутов\n\n\
Ты можешь указать👇\
\n— возвратный или нет маршрут\
\n— города, которые будут использованы в построении маршрута\
\n— период вылета и прилета (плавающая дата или точная)\
\n— пересадку в конкретном городе (в днях или часах — на выбор), по умолчанию — от 60 мин\
\n— авиакомпании, которые не следует включать в маршрут\n\n\
🙏🏻Моя миссия:\n\
Помогать путешественникам находить самые оптимальные вариантов маршрута без долгого и утомительного поиска вручную. Со мной тебе достаточно единажды ввести все желаемые параметры и выбрать лучший маршрут из тех, что я предложу.\
\n\nP.S.\n\
Не переживай, если в случае большого диапазона дат или большого кол-ва городов я стану строить маршруты долго. Иногда, в особо объемных случаях, я могу работать больше 1 минуты. За это время ты можешь выйти и поскроллить ленту, а потом — вернуться. Главное, не выключай уведомления😉", reply_markup=markup, parse_mode="Markdown")
    sql_users.add_users_to_sql([(message.from_user.id, message.from_user.username, message.from_user.full_name, 0, '', '', '', '', '', '', '[]', '[]')])


@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_AIRPORT) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_AIRPORT))
# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_AIRPORT)
def airport_handler(message):
    airport = message.text
    answer = CheckData().check_city(airport)
    if answer == True:
    # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
        users_state[message.chat.id].search_request_data.append_airport(airport)
        users_state[message.chat.id].state = UserStates.WAIT_FOR_TRANSIT_PERIOD
        sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Пропустить', callback_data='skeep_tranzit'))
        markup.add(types.InlineKeyboardButton('Начать заново', callback_data='compute_route'))
        bot.send_message(message.chat.id, text="Напиши минимальный период транзита через этот город, либо в формате дней, например '5д', либо в формате часов, например '10ч'. Обязательно укажи, в чем ты измеряешь длительность переасадки ;)\nЛибо ты можешь пропустить этот момент - если тебе неважно.",reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, text="Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "skeep_tranzit")
def skeep_tranzit_handler(callback_query):
    users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
    sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
    markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
    markup.add(types.InlineKeyboardButton('Начать поиск!', callback_data='start_search'))
    bot.reply_to(callback_query.message, text="Супер! Что делаем дальше?", reply_markup = markup)
# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_TRANSIT_PERIOD)
@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_TRANSIT_PERIOD) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_TRANSIT_PERIOD))
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
        bot.send_message(message.chat.id, text="Транзит в неверном формате.\nВведи, пожалуйста, еще раз, либо в днях - число с буквой 'д', ибо в часах - число с буквой 'ч'.\nНапример '7д' или '12ч'.")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "add_airport")
def add_air_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
        sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        bot.reply_to(callback_query.message, "Напиши город, который хочешь посетить.\nНапоминаю:\nГорода НЕ идут в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени в полёте.")
@bot.callback_query_handler(lambda callback_query: callback_query.data == "hate_airl")
def choose_hate_airl_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HATE_AIRL
        sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        bot.reply_to(callback_query.message, "Напиши название авиакомпании, которую не стоит добавлять в подборку. Пиши с заглавной буквы.")
# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_HATE_AIRL)
@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_HATE_AIRL) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_HATE_AIRL))
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
        bot.send_message(message.chat.id, text="Название авиакомпании написано некорректно. Попробуй еще раз, пиши с заглавной буквы.\nЕсли сомневаешься - посмотри официальное название авиакомпании, например:\n'Ред Вингс' или 'Северный Ветер (Nordwind Airlines)'")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "start_search")
def start_search_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_END
        sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    except:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        sr = Search()
        start_date, end_date, airports,start_period, end_period, home, finish, tranzit, hate_airl = users_state[callback_query.message.chat.id].search_request_data.start()
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
        else:
            users_state[callback_query.message.chat.id].best_in_price = iter(best_routes_price)
            users_state[callback_query.message.chat.id].best_in_time = iter(best_routes_time)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
            markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
            markup.add(types.InlineKeyboardButton('Начать новый поиск!', callback_data='compute_route'))
            suggested_by_price = next(users_state[callback_query.message.chat.id].best_in_price)
            suggested_by_time = next(users_state[callback_query.message.chat.id].best_in_time)
            all_route_cheap = f''
            for idx, flight in enumerate(suggested_by_price.storage):
                number = (idx + 1)
                first_airport = flight[0]
                second_airport = flight[1]
                dict_with_data = flight[2]
                price = dict_with_data['weight']
                departure = dict_with_data['time']
                airline = dict_with_data['airlines']
                time_in_sky = dict_with_data['time_in_sky']
                link = f"https://www.aviasales.ru{dict_with_data['link']}"
                route = f'{number}) Из <b>{first_airport}🛫</b>\nВ <b>{second_airport}🛬</b>\nЦена рейса: {price}₽\nОтправление {departure}\nПродолжительность рейса: {time_in_sky}\'' \
                        f'\nАвиакомпания: {airline}\n<a href="{link}">✈️Ссылка на билет. Нажми!</a>\n'
                all_route_cheap += route
            all_route_fast = f''
            for idx, flight in enumerate(suggested_by_time.storage):
                number = (idx + 1)
                first_airport = flight[0]
                second_airport = flight[1]
                dict_with_data = flight[2]
                price = dict_with_data['weight']
                departure = dict_with_data['time']
                airline = dict_with_data['airlines']
                time_in_sky = dict_with_data['time_in_sky']
                link = f"https://www.aviasales.ru{dict_with_data['link']}"
                route = f'{number}) Из <b>{first_airport}🛫</b>\nВ <b>{second_airport}🛬</b>\nЦена рейса: {price}₽\nОтправление {departure}\nПродолжительность рейса: {time_in_sky}\'' \
                        f'\nАвиакомпания: {airline}\n<a href="{link}">✈️Ссылка на билет. Нажми!</a>\n'
                all_route_fast += route
            bot.reply_to(callback_query.message,
                         f'💰<b>Самый дешевый</b>\n💸Цена за все перелёты: {suggested_by_price.total_price()}₽\n\n{all_route_cheap}\n\n⚡️<b>Самый быстрый</b>\n⏳Продолжительность всех рейсов: {suggested_by_time.total_time()} мин\n\n{all_route_fast}',
                         reply_markup=markup, parse_mode="HTML")
            sql_users.delete_airports(callback_query.message.chat.id)


@bot.callback_query_handler(lambda callback_query: callback_query.data == "show_next_cheap_flight")
def start_search_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_MORE_TICKETS
        sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    except:
        bot.send_message(callback_query.message.chat.id,
                             "Упс, что-то пошло не так. Начни поиск заново командой /start")
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
            all_route_cheap = f''
            for idx, flight in enumerate(suggested_by_price.storage):
                number = (idx + 1)
                first_airport = flight[0]
                second_airport = flight[1]
                dict_with_data = flight[2]
                price = dict_with_data['weight']
                departure = dict_with_data['time']
                airline = dict_with_data['airlines']
                time_in_sky = dict_with_data['time_in_sky']
                link = f"https://www.aviasales.ru{dict_with_data['link']}"
                route = f'{number}) Из <b>{first_airport}🛫</b>\nВ <b>{second_airport}🛬</b>\nЦена рейса: {price}₽\nОтправление {departure}\nПродолжительность рейса: {time_in_sky}\'' \
                        f'\nАвиакомпания: {airline}\n<a href="{link}">✈️Ссылка на билет. Нажми!</a>\n'
                all_route_cheap += route
            bot.reply_to(callback_query.message,
                         f'💰<b>Самый дешевый</b>\n💸Цена за все перелёты: {suggested_by_price.total_price()}₽\n\n{all_route_cheap}\n',
                         reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(lambda callback_query: callback_query.data == "show_next_fast_flight")
def start_search_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_MORE_TICKETS
        sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    except:
        bot.send_message(callback_query.message.chat.id,
                                 "Упс, что-то пошло не так. Начни поиск заново командой /start")
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
            all_route_fast = f''
            for idx, flight in enumerate(suggested_by_time.storage):
                number = (idx + 1)
                first_airport = flight[0]
                second_airport = flight[1]
                dict_with_data = flight[2]
                price = dict_with_data['weight']
                departure = dict_with_data['time']
                airline = dict_with_data['airlines']
                time_in_sky = dict_with_data['time_in_sky']
                link = f"https://www.aviasales.ru{dict_with_data['link']}"
                route = f'{number}) Из <b>{first_airport}🛫</b>\nВ <b>{second_airport}🛬</b>\nЦена рейса: {price}₽\nОтправление {departure}\nПродолжительность рейса: {time_in_sky} мин\'' \
                        f'\nАвиакомпания: {airline}\n<a href="{link}">✈️Ссылка на билет. Нажми!</a>\n'
                all_route_fast += route
            bot.reply_to(callback_query.message,
                                 f'⚡️<b>Самый быстрый</b>\n⏳Продолжительность всех рейсов: {suggested_by_time.total_time()}мин\n\n{all_route_fast}',
                         reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "compute_route")
def compute_route_handler(callback_query):
    if callback_query.message.chat.id not in users_state:
        users_state[callback_query.message.chat.id] = UserState(callback_query.message.chat.id)
    users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HOME
    sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)
    bot.reply_to(callback_query.message, "Напиши название города отправления. Например - Москва или Санкт-Петербург.")

# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_HOME)
@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_HOME) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_HOME))
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
        bot.send_message(message.chat.id, text="Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_DATA_HOME_DEPARTURE)
@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_DATA_HOME_DEPARTURE) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_DATA_HOME_DEPARTURE))
def period_for_home_departure_handler(message):
    period_or_date = message.text
    answer_bool = users_state[message.chat.id].search_request_data.set_start_date(period_or_date)
    if answer_bool == True:
        users_state[message.chat.id].state = UserStates.WAIT_FOR_CIRCLE_OR_NOT
        sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Кольцевой', callback_data='circle'))
        markup.add(types.InlineKeyboardButton('В один конец', callback_data='one_way'))
        bot.send_message(message.chat.id, text="Выбери, твой маршрут кольцевой (с возвращением в первый пункт вылета) или одну сторону и аэропорт вылета не совпадает с с аэропортом прилета?", reply_markup=markup)
    elif answer_bool == False:
        bot.send_message(message.chat.id,
                         text="Дата или период в неверном формате, пожалуйста, напиши ее, как в примере:\nдату вылета в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD` ")


@bot.callback_query_handler(lambda callback_query: callback_query.data == "circle")
def circle_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
        sql_users.update_user_state(callback_query.message.chat.id, users_state[callback_query.message.chat.id].state)

    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
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
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        bot.reply_to(callback_query.message, "Напиши конечный город назначения. Модель сама определит доступные аэропорта для него.")

# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_AIRPORT)
@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_AIRPORT) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_FINISH_AIRPORT))
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
                         text="Название города прилета совпадает с городом вылета, такой фильтр невозможен для маршрута в одну сторону. Если ты хочешь найти кольцевой маршрут, нажми на кнопку Кольцевой.", reply_markup=markup)

    else:
        bot.send_message(message.chat.id, text="Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

# @bot.message_handler(func=lambda message: message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_DEPARTURE)
@bot.message_handler(func=lambda message: (message.chat.id in users_state and users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_DEPARTURE) or sql_users.get_user_state(message.from_user.id) == int(UserStates.WAIT_FOR_FINISH_DEPARTURE))
def finish_date_or_period_handler(message):
    date_or_period = message.text
    answer = users_state[message.chat.id].search_request_data.append_date_or_period_to_finish(date_or_period)
    if answer == True:
        users_state[message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
        sql_users.update_user_state(message.chat.id, users_state[message.chat.id].state)
        bot.send_message(message.chat.id, text="Выбери город, который хочешь посетить.\nНапоминаю:\nГорода НЕ идут в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени в полёте")
    else:
        bot.send_message(message.chat.id,
                         text="Дата или период в неверном формате, пожалуйста, напиши ее, как в примере:\nдату вылета в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD` ")
@bot.message_handler(commands=['request_to_sql'])
def send_welcome(message):
    document_send = sql_users.convert_to_excel()
    bot.send_document(message.chat.id, document_send)

bot.polling(none_stop=True, interval=0)

#TODO:
# сделай возможность писать города в хронологическом порядке
# добавь состояние пользователя в базу.
# может ли телега дать виджит календаря
# фиксить дфс
# глянь api