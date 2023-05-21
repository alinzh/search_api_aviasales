
def message_hello():
    mes = "Привет!👋 \
        \nЯ — бот, поисковик авиабилетов✈️, который умеет искать с более гибкими фильтрами чем aviasales. Я умею строить \
        сложные маршруты с гибкими датами и находить оптимальную последовательность пунктов маршрута.\
        \n\nЯ могу тебе помочь👇\
        \n— построить маршрут из большого кол-ва городов\
        \n— найти самую дешевую последовательность городов в маршруте\
        \n— направить тебе самые быстрые или самые дешевые варианты маршрутов \
        \n\nТы можешь указать👇\
        \n— возвратный или нет маршрут\
        \n— города, которые будут использованы в построении маршрута \
        \n— период вылета и прилета (плавающая дата или точная)\
        \n— пересадку в конкретном городе (в днях или часах — на выбор), по умолчанию — от 60 мин\
        \n— авиакомпании, которые не следует включать в маршрут \
        🙏\n\nМоя миссия: \
        \nПомогать путешественникам находить самые оптимальные вариантов маршрута без долгого и \
        утомительного поиска вручную. Со мной тебе достаточно единажды ввести все желаемые параметры и выбрать лучший \
        маршрут из тех, что я предложу.\
        \n\nP.S. \
        \nНе переживай, если в случае большого диапазона дат или большого кол-ва городов я стану строить маршруты долго.\
        Иногда, в особо объемных случаях, я могу работать больше 1 минуты. За это время ты можешь выйти и поскроллить\
        ленту, а потом — вернуться. Главное, не выключай уведомления😉"
    return mes
def message_search_began_wait(home, finish, start_period, end_period, citys, tranzit, hate_air):
    mes = f'<b>Осуществляю поиск билетов по таким параметрам</b>👇 \
\n🌇Первый город вылета:{home} \
\n📅Период или дата вылета:{start_period} \
\n\n🌃Крайний город прилета:{finish} \
\n📅Период или дата вылета:{end_period} \
\n\nГорода на маршруте: {[str(city) for city in citys]} \
\nТранзит: {[str(pair) for pair in tranzit]} \
\nИсключения из авиакомпаний: {hate_air}\n\nНикуда не нажимай! \
Процесс идет, но может занять какое-то время. <b>В течении минуты</b> я дам тебе обратную связь😉'
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