
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
        end_period = str(start_p[0]) + ' - ' + str(start_p[1])
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