import telebot
from telebot import types
from route import Route
from search import Search
from serchrequestdata import SearchRequestData
from check_answer import CheckData


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



class UserState:
    def __init__(self):
        self.state = None
        self.search_request_data = SearchRequestData()
        self.best_in_price = None
        self.best_in_time = None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Начать поиск', callback_data='compute_route'))
    bot.reply_to(message, "Приветственное сообщение, рассказ о возможностях бота", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_AIRPORT)
def airport_handler(message):
    airport = message.text
    answer = CheckData().check_city(airport)
    if answer == True:
    # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
        users_state[message.chat.id].search_request_data.append_airport(airport)
        users_state[message.chat.id].state = UserStates.WAIT_FOR_TRANSIT_PERIOD
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Пропустить', callback_data='skeep_tranzit'))
        bot.send_message(message.chat.id, text="Напиши минимальный период транзита через этот город, либо в формате дней, например '5д', либо в формате часов, например '10ч'. Обязательно укажи, в чем ты измеряешь длительность переасадки ;)\nЛибо ты можешь пропустить этот момент - если тебе неважно.",reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, text="Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "skeep_tranzit")
def skeep_tranzit_handler(callback_query):
    users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
    markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
    markup.add(types.InlineKeyboardButton('*Начать поиск!*', callback_data='start_search'))
    bot.reply_to(callback_query.message, text="Супер! Что делаем дальше?", reply_markup = markup)
@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_TRANSIT_PERIOD)
def transit_period_handler(message):
    time_tranzit = message.text
    answer = users_state[message.chat.id].search_request_data.append_time_tranzit(time_tranzit)
    if answer == True:
        users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
        markup.add(types.InlineKeyboardButton('Выбрать нежеланные авиакомпании', callback_data='hate_airl'))
        markup.add(types.InlineKeyboardButton('*Начать поиск!*', callback_data='start_search'))
        bot.send_message(message.chat.id, text="Супер! Что делаем дальше?", reply_markup = markup)
    elif answer == False:
        bot.send_message(message.chat.id, text="Транзит в неверном формате.\nВведи, пожалуйста, еще раз, либо в днях - число с буквой 'д', ибо в часах - число с буквой 'ч'.\nНапример '7д' или '12ч'.")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "add_airport")
def add_air_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        bot.reply_to(callback_query.message, "Напиши город, который хочешь посетить.\nНапоминаю:\nГорода НЕ идут в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени в полёте.")
@bot.callback_query_handler(lambda callback_query: callback_query.data == "hate_airl")
def choose_hate_airl_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HATE_AIRL
    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        itembtn1 = types.KeyboardButton('Победа')
        itembtn2 = types.KeyboardButton('Azur Air')
        itembtn3 = types.KeyboardButton('Smartavia')
        itembtn4 = types.KeyboardButton('Ямал')
        itembtn5 = types.KeyboardButton('Azimut')
        itembtn6 = types.KeyboardButton('Уральские авиалинии')
        markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
        bot.reply_to(callback_query.message, "Выбери авиакомпанию, которую не стоит добавлять в подборку. Если передумал - нажми в предыдущем сообщении другой вариант продолжения!")
@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_HATE_AIRL)
def hate_airl_handler(message):
    hate_airl = message.text
    users_state[message.chat.id].search_request_data.append_hate_airl(hate_airl)
    users_state[message.chat.id].state = UserStates.WAIT_FOR_CHOOSE
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Добавить город', callback_data='add_airport'))
    markup.add(types.InlineKeyboardButton('*Начать поиск!*', callback_data='start_search'))
    bot.send_message(message.chat.id, text="Супер! Что делаем дальше?", reply_markup=markup)

@bot.callback_query_handler(lambda callback_query: callback_query.data == "start_search")
def start_search_handler(callback_query):
    # TODO
    # TODO: тут получаешь список самых дешевых и список самых быстрых
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_END
    except:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        best_in_price, best_in_time = users_state[callback_query.message.chat.id].search_request_data.start()
    # Сделать в этом методе
    # Затем перегоняешь их в итератор как `best_in_price = iter(best_in_price)`
    # Затем в состояние юзера users_state[callback_query.message.chat.id] кладешь получнные итераторы best_in_price и best_in_time
    # Затем в реплай кидаешь next(best_in_price) и next(best_in_time)


    # Методы кнопок вне этой функции.
    # Колбэк кнопки "больше дешевых" или "больше быстрых" идет в состояние юзера и делает next(users_state[callback_query.message.chat.id].best_in_price) или next(users_state[callback_query.message.chat.id].best_in_time)
    # Сделай обработку на случай StopIteration - это значит, что ты показала всё, что есть и больше нет смысла показывать кнопки "показать еще"


    # users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_END
    # date = users_state[callback_query.message.chat.id].search_request_data.constructor_answer()
    score = 0
    route_for_show = best_in_price[0]
    route_for_show_time = best_in_time[0]
    for score_t in route_for_show_time:
        for score_p in route_for_show:
            all_flight_p = f''
            all_flight_t = f''
            for flight_p in route_for_show:
                for flight_t in route_for_show_time[0]:
                    score += 1
                    data_for_show = flight_p[2]
                    data_for_show_time = flight_t[2]
                    one_flight_p = f'{score}) Из {score_p[0]} в {score_p[1]}\n\nЦена билета: {data_for_show["weight"]}\n\Отправление: {data_for_show["time"]}\nАвиакомпания: {data_for_show["airlines"]}\nСсылка на билет: aviasales.ru{data_for_show["link"]}'
                    one_flight_t = f'{score}) Из {score_t[0]} в {score_t[1]}\n\nЦена билета: {data_for_show_time["weight"]}\n\Отправление: {data_for_show_time["time"]}\nАвиакомпания: {data_for_show_time["airlines"]}\nСсылка на билет: aviasales.ru{data_for_show_time["link"]}'
                    all_flight_p += one_flight_p
                    all_flight_t += one_flight_t
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Еще дешевых', callback_data='show_next_cheap_flight'))
    markup.add(types.InlineKeyboardButton('Еще быстрых', callback_data='show_next_fast_flight'))
    bot.reply_to(callback_query.message,f'Самый дешевый. Цена: {best_in_price[1]}\nДанные о рейсах:\n\n{all_flight_p}\n\nСамый быстрый.\nВремя: {route_for_show_time[1]}\nДанные о рейсах:\n\n{all_flight_t}',
                 reply_markup=markup)

@bot.callback_query_handler(lambda callback_query: callback_query.data == "compute_route")
def compute_route_handler(callback_query):
    users_state[callback_query.message.chat.id] = UserState()
    users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_HOME
    bot.reply_to(callback_query.message, "Напиши название города отправления. Например - Москва или Санкт-Петербург.")

@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_HOME)
def home_handler(message):
    home = message.text
    answer = CheckData().check_city(home)
    if answer == True:
    # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
        users_state[message.chat.id].search_request_data.append_home(home)
        users_state[message.chat.id].state = UserStates.WAIT_FOR_DATA_HOME_DEPARTURE
        bot.send_message(message.chat.id, text="Напиши дату вылета в формате `DD/MM/YYYY` или период в формате `DD.MM.YYYY - DD.MM.YYYY`")
    else:
        bot.send_message(message.chat.id, text="Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_DATA_HOME_DEPARTURE)
def period_for_home_departure_handler(message):
    period_or_date = message.text
    answer_bool = users_state[message.chat.id].search_request_data.set_start_date(period_or_date)
    if answer_bool == True:
        users_state[message.chat.id].state = UserStates.WAIT_FOR_CIRCLE_OR_NOT
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Кольцевой', callback_data='circle'))
        markup.add(types.InlineKeyboardButton('В один конец', callback_data='one_way'))
        bot.send_message(message.chat.id, text="Выбери, твой маршрут кольцевой (с возвращением в первый пункт вылета) или одну сторону и аэропорт вылета не совпадает с с аэропортом прилета?", reply_markup=markup)
    elif answer_bool == False:
        bot.send_message(message.chat.id,
                         text="Дата или период в неверном формате, пожалуйста, напиши ее, как в примере:\nдату вылета в формате `DD.MM.YYYY` или период в формате `DD.MM.YYYY - DD/MM/YYYY` ")


@bot.callback_query_handler(lambda callback_query: callback_query.data == "circle")
def circle_handler(callback_query):
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        users_state[callback_query.message.chat.id].search_request_data.append_circle(True)
        bot.reply_to(callback_query.message, "Напиши дату или период последнего возвратного вылета. Пиши дату в формате `DD.MM.YYYY` или период в формате `DD.MM.YYYY - DD.MM.YYYY`")

@bot.callback_query_handler(lambda callback_query: callback_query.data == "one_way")
def one_way_handler(callback_query):
    # users_state[callback_query.message.chat_id].search_request_data.append_circle(False)
    try:
        users_state[callback_query.message.chat.id].state = UserStates.WAIT_FOR_FINISH_AIRPORT
    except KeyError:
        bot.send_message(callback_query.message.chat.id, "Упс, что-то пошло не так. Начни поиск заново командой /start")
    else:
        bot.reply_to(callback_query.message, "Напиши конечный город назначения. Модель сама определит доступные аэропорта для него.")

@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_AIRPORT)
def finish_airport_handler(message):
    airport = message.text
    answer = CheckData().check_city(airport)
    if answer == True:
    # TODO: Чекнуть, если дано название(город) аэропорта, то получить код аэропорта через API aviasales, чтобы Москва стала MOW, например.
        users_state[message.chat.id].search_request_data.append_finish_airport(airport)
        users_state[message.chat.id].state = UserStates.WAIT_FOR_FINISH_DEPARTURE
        bot.send_message(message.chat.id, text="Напиши дату последнего полета в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD`")
    else:
        bot.send_message(message.chat.id, text="Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы")

@bot.message_handler(func=lambda message: users_state[message.chat.id].state == UserStates.WAIT_FOR_FINISH_DEPARTURE)
def finish_date_or_period_handler(message):
    date_or_period = message.text
    answer = users_state[message.chat.id].search_request_data.append_date_or_period_to_finish(date_or_period)
    if answer == True:
        users_state[message.chat.id].state = UserStates.WAIT_FOR_AIRPORT
        bot.send_message(message.chat.id, text="Выбери город, который хочешь посетить.\nНапоминаю:\nГорода НЕ идут в хронологическом порядке. Модель определяет лучшую комбинацию исходя из фильтров, цены или времени в полёте")
    else:
        bot.send_message(message.chat.id,
                         text="Дата или период в неверном формате, пожалуйста, напиши ее, как в примере:\nдату вылета в формате `DD.MM.YYYY` или период в формате `DD.MM.YYYY - DD.MM.YYYY` ")


bot.polling(none_stop=True, interval=0)

#сделай проверку на дату, что первая не больше второй (при периоде) и что это реальная дата, а не число в формате (как сейчас)
#убери возможность регировать на сообщения или ломаться, если пользоват. пишет, не когда нужно
#убери или обдумай hate_airl
