"""
Here is stores large texts for message to user.
"""


def message_hello():
    mes = "Привет!👋 \
        \nЯ — бот, поисковик авиабилетов✈️, который умеет искать с более гибкими фильтрами чем aviasales.\
 Я умею строить сложные маршруты с 2 - 6 городами или странами, а также гибкими датами вылета и прилёта.\
        \n\nЯ могу тебе помочь👇\
        \n<b>— найти оптимальный маршрут из выбранных городов, исходя из цен на билеты и времени в полёте</b>\
        \n— построить маршрут из большого кол-ва городов\
        \n— учесть пожелание по времени в любом городе\
        \n— исключить из поиска конкретные авиакомпании\
        \n\nЯ найду всё и сразу! В ответ направлю маршруты с ценами и ссылками на билеты."
    return mes

def message_chronological_search_or_not():
    mes = "🔎Выбери способ поиска:\
        \n\n- составить маршрут из городов идущих в хронологическом порядке\
        \n- использовать оптимальную последовательность (первый и последний города останутся фиксированными)"
    return mes

def message_end_date_for_chronological_route():
    mes = f'<i>Сейчас начнем, уточню только один нюанс👇</i>\n\nНапиши дату последнего вылета в формате '\
          f'`YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD '
    return mes

def message_not_found():
    mes = f'Ого!😳 С такими жесткими фильтрами не нашлось ни одного маршрута...\n\nПопробуем что-то поменять?'
    return mes

def message_something_went_wrong():
    mes = "⚠️Упс, что-то пошло не так. Начни поиск заново командой /start"
    return mes

def message_write_last_city_in_route():
    mes = "Напиши крайний город в твоём маршруте. \n\n<i>Модель сама определит " \
          "доступные аэропорта для него.</i>"
    return mes
def message_write_first_city_in_route():
    mes = "Напиши название города отправления. \n\n<i>Например - Москва или "\
          "Санкт-Петербург</i>."
    return mes
def message_write_last_in_route_chronological():
    mes = "Напиши название города, который хочешь посетить.\n\n<i>☝️Города идут " \
          "в хронологическом порядке.</i>"
    return mes
def message_write_last_in_route_not_chronological():
    mes = "Напиши название города, который хочешь посетить.\n\n<i>☝️Города НЕ идут в " \
          "хронологическом порядке. Модель определяет лучшую комбинацию " \
          "исходя из фильтров, цены или времени в полёте.</i>"
    return mes
def message_write_last_date():
    mes = "Напиши дату или период последнего возвратного вылета. " \
          "Пиши дату в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD`"
    return mes
def message_tranzit_in_wrong_format():
    mes = "⚠️Транзит в неверном формате.\nВведи еще раз, либо в днях - число с буквой 'д', ибо в часах - число " \
          "с буквой 'ч'.\n<b>Например '7д' или '12ч'.</b>"
    return mes
def message_write_tranzit():
    mes = "🕘Напиши минимальный период транзита через этот город. \n\n<i>Пиши в формате дней, например - '5д', " \
          "либо в формате часов, например - '10ч'.</i>"
    return mes
def message_write_date():
    mes = "Напиши дату вылета в формате `YYYY.MM.DD` или период в формате `YYYY.MM.DD - YYYY.MM.DD`"
    return mes
def message_tickets_finish():
    mes = f'Увы, вы просмотрели все билеты.\nПродолжим поиск с другими фильтрами?'
    return mes
def message_date_in_wrong_format():
    mes = "⚠️Дата или период в неверном формате, напиши ее, как в " \
          "примере:\n- точная дата `YYYY.MM.DD` \n- период `YYYY.MM.DD - YYYY.MM.DD`"
    return mes
def message_circle_or_not():
    mes = "Выбери, какой у тебя маршрут.\n\n<i>Кольцевой - с возвращением в первый пункт вылета. \nВ один " \
          "конец - аэропорт вылета не совпадает с с аэропортом прилета.</i>"
    return mes
def message_period_longer_than_allowed():
    mes = "⚠️Указан недопустимый период, от начала до завершения маршрута должно быть не более 31 дня. \n\nУкажите " \
          "дату или период, чтобы диапазон от даты первого вылета был не более 3 недель."
    return mes
def message_name_of_company_is_wrong():
    mes = "⚠️Название авиакомпании написано некорректно. Попробуй еще раз, пиши с заглавной буквы.\nЕсли " \
          "сомневаешься - посмотри официальное название авиакомпании, например:\n'Ред Вингс' или " \
          "'Северный Ветер (Nordwind Airlines)'"
    return mes
def message_write_name_of_company():
    mes = "Напиши название авиакомпании, которую не стоит добавлять в подборку. \n\n<i>Пиши " \
          "с заглавной буквы, например - Победа или Азимут.</i>"
    return mes
def message_city_of_departure_and_arrival_same():
    mes = "⚠️Название города прилета совпадает с городом вылета, такой фильтр невозможен для маршрута в одну сторону. " \
          "Если ты хочешь найти кольцевой маршрут, нажми на кнопку Кольцевой."
    return mes
def message_name_of_city_is_wrong():
    mes = "⚠️Название города указано с ошибками, проверь правописание и напиши еще раз в И.П. с заглавной буквы"
    return mes
def message_city_alredy_in_route():
    mes = "⚠️Этот город уже добавлен в маршрут. Выбери другой."
    return mes
def message_no_more_cities():
    mes = "⚠️Лимит на количество городов исчерпан. \nНачнем поиск?"
    return mes
def message_search_began_wait(home, finish, start_period, end_period, citys, tranzit, hate_air):
    if end_period[0] == end_period[1]:
        end_period = end_period[0]
    else:
        end_p = end_period.copy()
        end_period = str(end_p[0]) + ' - ' + str(end_p[1])
    if start_period[0] == start_period[1]:
        start_period = start_period[0]
    else:
        start_p = start_period.copy()
        start_period = str(start_p[0]) + ' - ' + str(start_p[1])
    citys_str = ''
    for city in citys:
        citys_str += city + ', '
    if tranzit == []:
        tranzit = 'нет фильтра'
    elif tranzit != []:
        tranz = tranzit.copy()
        tranzit = ''
        for one_tranzit in tranz:
            tranzit += one_tranzit[0] + ' - ' + str(one_tranzit[1]) + ' мин, '
    if hate_air == []:
        hate_air = 'нет фильтра'
    else:
        hate_air = hate_air[0]
    mes = f'<b>Осуществляю поиск билетов по таким параметрам</b>👇 \
\n🌇Первый город вылета:\n{home} \
\n📅Период или дата вылета:\n{start_period} \
\n\n🌃Крайний город прилета:\n{finish} \
\n📅Период или дата вылета:\n{end_period} \
\n\nГорода на маршруте: <i>{citys_str}</i> \
\nТранзит: <i>{tranzit}</i> \
\nИсключения из авиакомпаний: <i>{hate_air}</i>\n\n<i>Никуда не нажимай! \
Процесс идет, но может занять какое-то время. <b>В течении минуты</b> я дам тебе обратную связь😉</i>'
    return mes

def message_timeout_for_waiting():
    mes = f'Ого!😳\n Количество маршрутов оказалось настолько объемным, что их подбор превысил время допустимое для операции.\n \
    Давай подберем другой, немногим легче?\n \
    Я рекомендую использовать не более 4-5 городов‼️ для маршрута, период всего путешествия не более 3-4 недель и более \
    точные даты вылета и прилета(чем конкретнее - тем лучше).'
    return mes

def answer_with_tickets_for_user(suggested_by_price, suggested_by_time):
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

    mes = f'💰<b>Самый дешевый</b>\n💸Цена за все перелёты: {suggested_by_price.total_price()}₽\n\n{all_route_cheap}\n\n⚡️<b>Самый быстрый</b>\n⏳Продолжительность всех рейсов: {suggested_by_time.total_time()} мин\n\n{all_route_fast}'
    return mes

def message_answer_tickets_more_cheap(suggested_by_price):
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

        mes = f'💰<b>Самый дешевый</b>\n💸Цена за все перелёты: {suggested_by_price.total_price()}₽\n\n{all_route_cheap}\n'
    return mes

def message_answer_tickets_more_short(suggested_by_time):
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
        mes = f'⚡️<b>Самый быстрый</b>\n⏳Продолжительность всех рейсов: {suggested_by_time.total_time()}мин\n\n{all_route_fast}'
    return mes