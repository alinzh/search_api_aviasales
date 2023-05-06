import copy
import json
from datetime import datetime, timedelta
from itertools import combinations
from typing import List, Dict, Union, Any
import networkx as nx
import numpy as np
import pandas as pd
import requests

token = f"191827beb804bd4d4025b75737717e18"


class ConvertDateTime:
    def convert_period_for_dates(self, start_date, end_date):
        '''
        start_date is date in format: %Y-%m-%d
        Covert period in many dates.
        :return: list with dates.
        '''
        arr_period_dates = pd.date_range(
            min(start_date, end_date),
            max(start_date, end_date)
        ).strftime('%Y-%m-%d').tolist()
        return arr_period_dates

    def format_big_to_small(self, date_x):
        '''
        convert format "%Y-%m-%dT%H:%M:%S%z" to "%Y-%m-%d"
        :param date:
        :return: date in format "%Y-%m-%d"
        '''
        source_format = "%Y-%m-%dT%H:%M:%S%z"
        dt = datetime.strptime(date_x, source_format)
        result_date = dt.strftime("%Y-%m-%d")
        return result_date

    def convert_day_to_month(self, date_x):
        '''
        convert format "%Y-%m-%d" to "%Y-%m"
        :return: date in "%Y-%m"
        '''
        source_format = "%Y-%m-%d"
        new_dates = []
        for i in range(len(date_x)):
            dt = datetime.strptime(date_x[i], source_format)
            result_date = dt.strftime("%Y-%m")
            new_dates.append(result_date)
        return new_dates

    def period_for_month(self, start_date, end_date):
        a_lot_dates = self.convert_period_for_dates(start_date, end_date)
        format_years_month = self.convert_day_to_month(a_lot_dates)
        months = list(set(format_years_month))
        return months
class Route:
    def __init__(self, start: str, finish: str, tranzit=None):
        self.start = start
        self.finish = finish
        self.tranzit = tranzit
        self.storage = []

    def len_tranzit(self, city: str):
        '''

        :param tranzit: list with tenzors in format arrival_city+time_tranzit
        :return:
        '''
        if self.tranzit != None:
            for pair in self.tranzit:
                if pair[0] == city:
                    return pair[1]
        return 60

    def append(self, x, tranzit=60) -> bool:
        # Проверить даейттайм добавлемоего edge (он же х тут), чтобы он был больше, чем у storage[-1]. Если ок - добавить х в self.storeage и вернуть True.
        if len(self.storage) >= 1:
            dict_atrr_2 = x[2]
            second_date = dict_atrr_2['time']
            date_format = '%Y-%m-%dT%H:%M:%S%z'
            date_2 = datetime.strptime(second_date, date_format)  # дата вылета рейса x
            y = self.storage[-1]
            dict_atrr_1 = y[2]
            first_data = dict_atrr_1['time']
            data_1 = datetime.strptime(first_data, date_format)  # дата вылета рейса storage[-1]
            flight_duration = dict_atrr_1['time_in_sky']  # время полета рейса storage[-1], т.е. У
            tranzit = self.len_tranzit(x[0])
            if date_2 > data_1:
                delta = date_2 - (data_1 + timedelta(minutes=flight_duration) + timedelta(minutes=tranzit))
                if delta >= timedelta(0):
                    self.storage.append(x)
                    return True
                else:
                    return False
            else:
                return False
        else:
            self.storage.append(x)
            return True

    def period_for_first_departure(self, x, start_time, end_time):
        necessary_date = ConvertDateTime().convert_period_for_dates(start_date, end_date)
        dict_atrr_2 = x[2]
        date_of_flight = dict_atrr_2['time']
        date_format = '%Y-%m-%dT%H:%M:%S%z'
        date = datetime.strptime(date_of_flight, date_format)
        for idx, i in enumerate(necessary_date):
            if i == date:
                return True
            elif idx == len(necessary_date):
                return False
            else:
                continue

    def __len__(self):
        return len(self.storage)

    def __getitem__(self, index: Any) -> Any:
        raise NotImplementedError

    def total_price(self) -> float:
        # Метод возвращает сумму стоимостей всех билетов в этом маршруте
        price = 0
        for idx, route in enumerate(self.storage):
            flight = route[2]
            price += flight['weight']
        return price
        raise NotImplementedError

    def total_time(self) -> float:
        duration = 0
        for idx, time in enumerate(self.storage):
            flight = time[2]
            duration += flight['time_in_sky']
        return duration


class Search():

    def __init__(self, token="191827beb804bd4d4025b75737717e18"):
        self.token = token

    def find_flights_fo_period(self, airports, start_date, end_date, s_period, e_period, home, finish):
        '''To covert period for many separate dates.
           To call request.
           To save arr with dates of flights for all period.
        '''

        cv = ConvertDateTime()
        different_month = cv.period_for_month(start_date, end_date)
        flights_on_data = []
        for i in range(len(different_month)):
            data = (different_month)[i]
            flights = self.offers(origin=airports[0], destination=airports[1], departure_at=data,
                                              return_at='',
                                              market="ru", limit=1000, sorting="price")
            if i == 0:
                flights_on_data = flights
            else:
                flights_on_data.update(flights)
        if airports[0] == home:
            start_period = s_period[0]
            end_period = s_period[1]
        elif airports[1] == finish:
            start_period = e_period[0]
            end_period = e_period[1]
        else:
            start_period = start_date
            end_period = end_date
        # ниже отсекаем ненужные даты: смотрим на ограничения по вылету из 1-ого аэропорта и последнего и,
        # по периоду указанному при запросе (до этого кидали запросы на сервер на месяца)
        period_in_dates = cv.convert_period_for_dates(start_period, end_period)
        necessary_flight = {}
        for idx, data in enumerate(period_in_dates):
            if data not in flights_on_data:
                necessary_flight[data] = None
            else:
                necessary_flight[data] = flights_on_data[data]
        return necessary_flight
    def neccesary_flight_for_period(self):
        NotImplementedError

    def find_paths_of_length(self, graph, node, path_len, finish, tranzit):
        paths = []
        visited = {node: True}
        def dfs_circle(G, airport: Any, path: Route):
            for neighbor in graph.neighbors(airport):

                flights = []  # TODO: забрать edges между airport и neighbor из графа
                # flights = G.get_edge_data(airport, neighbor, data=True)
                for u, v, d in G.edges(data=True):
                    if u == airport and v == neighbor:
                        flights.append([airport, neighbor, d])
                for flight in flights:
                    path_copy = copy.deepcopy(path)
                    success = path_copy.append(flight)
                    if success:
                        if len(path_copy) == path_len - 1 and path_copy.start == neighbor:
                            paths.append(path_copy)
                        elif neighbor not in visited:
                            visited[neighbor] = True
                            dfs_circle(G, neighbor, path_copy)
                            visited.pop(neighbor)

        def dfs_not_circle(G, airport, finish, path: Route):
            for neighbor in graph.neighbors(airport):
                if len(path) != path_len - 3 and neighbor == finish:
                    continue
                flights = []  # TODO: забрать edges между airport и neighbor из графа
                # flights = G.get_edge_data(airport, neighbor, data=True)
                for u, v, d in G.edges(data=True):
                    if u == airport and v == neighbor:
                        flights.append([airport, neighbor, d])
                for flight in flights:
                    path_copy = copy.deepcopy(path)
                    success = path_copy.append(flight)
                    if success:
                        if len(path_copy) == path_len - 2 and path_copy.finish == neighbor:
                            paths.append(path_copy)
                        elif neighbor not in visited:
                            visited[neighbor] = True
                            dfs_not_circle(G, neighbor, finish, path_copy)
                            visited.pop(neighbor)

            return paths

        r = Route(node, finish, tranzit)
        if r.start == r.finish:
            dfs_circle(graph, node, r)
        elif r.start != r.finish:
            dfs_not_circle(graph, node, finish, r)
        return paths

    def compute_all_routes(self, dict_r, combinations_airports, arr_period_date, home, finish, tranzit, hate_airl):
        '''
        Input: dict with all possible flights between all selected airports.
        To compute all possible routes from all flights.
        Return: Graf and array with routes.
        '''

        G = nx.MultiDiGraph()
        airports = []
        for idx, i in enumerate(combinations_airports):
            airports.append(i[0])
            airports.append(i[1])
        airports = set(airports)
        G.add_nodes_from(airports)
        for idx, i in enumerate(combinations_airports):
            time_data = dict_r[i]
            for j in range(len(arr_period_date)):
                if len(time_data) < len(arr_period_date):
                    keys_list = list(time_data.keys())
                    if arr_period_date[j] not in time_data:
                        continue
                    elif time_data[arr_period_date[j]] == None:
                        continue
                    else:
                         data_for_one_flight = time_data[arr_period_date[j]]
                         if len(hate_airl) > 0:
                             for airline in hate_airl:
                                 if data_for_one_flight['airline'] == airline:
                                     continue
                                 else:
                                     G.add_edge(i[0], i[1], weight=data_for_one_flight['price'],
                                                time=data_for_one_flight['departure_at'],
                                                time_in_sky=data_for_one_flight['duration'],
                                                airlines=data_for_one_flight['airline'],
                                                link=data_for_one_flight['link'])
                         else:
                             G.add_edge(i[0], i[1], weight=data_for_one_flight['price'],
                                       time=data_for_one_flight['departure_at'], time_in_sky=data_for_one_flight['duration'],airlines = data_for_one_flight['airline'], link = data_for_one_flight['link'])
                elif time_data[arr_period_date[j]] == None:
                    continue
                else:
                     data_for_one_flight = time_data[arr_period_date[j]]
                     if len(hate_airl) > 0:
                         for airline in hate_airl:
                             if data_for_one_flight['airline'] == airline:
                                 continue
                             else:
                                 G.add_edge(i[0], i[1], weight=data_for_one_flight['price'],
                                            time=data_for_one_flight['departure_at'],
                                            time_in_sky=data_for_one_flight['duration'],
                                            airlines=data_for_one_flight['airline'],
                                            link=data_for_one_flight['link'])
                     else:
                         G.add_edge(i[0], i[1], weight=data_for_one_flight['price'],
                                    time=data_for_one_flight['departure_at'],
                                    time_in_sky=data_for_one_flight['duration'],
                                    airlines=data_for_one_flight['airline'], link=data_for_one_flight['link'])

        all_routes = self.find_paths_of_length(G, home, path_len=(len(airports) + 1), finish=finish, tranzit=tranzit)
        return G, all_routes
        raise NotImplementedError

    def find_cheapest_route(self, routes: List[Route]):
        '''
        Calling func total_price, which is implements price for all route (not just flight)
        :return: list with sorted routes for price (from cheapest) and list with price
        '''
        price_for_routes = [route.total_price() for route in routes]
        sorted_indexes = np.argsort(price_for_routes)
        sorted_price = np.sort(price_for_routes)
        new_arr_r = []  # список экзмпляров класса route, отсортированный по возрастанию стоимости маршрута
        for i in sorted_indexes:
            new_arr_r.append(routes[i])
        return new_arr_r, sorted_price

    def find_short_in_time_route(self, routes: List[Route]):
        '''
        Calling func total_time, which is implements time in sky for all flights
        :return: list with sorted routes for shortest duration and list with time in sky (duration)
        '''
        time_for_routes = [route.total_time() for route in routes]
        sorted_indexes = np.argsort(time_for_routes)
        sorted_time = np.sort(time_for_routes)
        new_arr_t = []  # список экзмпляров класса route, отсортированный по возрастанию времени на рейсы
        for i in sorted_indexes:
            new_arr_t.append(routes[i])
        return new_arr_t, sorted_time

    def collects_all_flights_for_all_routes(self, start_date, end_date, airports, start_period, end_period, home,
                                            finish):
        '''
        To call find_flights_fo_period and
        to append all arrays with flights on different routes
        in dict
        :return: dict, key = route, value = arr with all flights
        '''
        combinations_airports = []
        temp = combinations(airports, 2)

        # Создаем комбинации из двух аэропортов, где ([)n, m) и (m, n) считается =
        for i in list(temp):
            combinations_airports.append(i)

        # создаем кортеж с обратными напрвлениями
        return_combinations = combinations_airports.copy()

        # создаем новый кортеж с элементами в обратном порядке
        for idx, i in enumerate(return_combinations):
            i = (*i[::-1],)
            return_combinations[idx] = i

        # совмещаем кортеж с обратными и необратными направлениями
        for idx, i in enumerate(return_combinations):
            combinations_airports.append(i)
        # вызвать функцию со всеми возможными парами аэропортов
        dict = {}
        for idx, pair_air in enumerate(combinations_airports):
            req_for_period = self.find_flights_fo_period(pair_air, start_date, end_date, start_period, end_period, home,
                                                         finish)
            dict[pair_air] = req_for_period

        arr_period_dates = ConvertDateTime().convert_period_for_dates(start_date, end_date)
        return dict, combinations_airports, arr_period_dates
        raise NotImplementedError

    def patricular_url_for_req(self, *args, **kwargs):
        return self.url_for_req(feature="v3/prices_for_dates?", *args, **kwargs)

    def url_for_req(self, origin, destination, departure_at, feature, market="ru", limit=1000, sorting="price",
                    return_at=''):
        url = f'https://api.travelpayouts.com/aviasales/{feature}' \
              f'origin={origin}' \
              f'&destination={destination}' \
              f'&departure_at={departure_at}' \
              f'&return_at={return_at}' \
              f'&sorting={sorting}' \
              f'&limit={limit}&token={self.token}'
        return url

    def request(self, url: str) -> Dict[str, Union[bool, List[Dict[str, Any]], str]]:
        """THis function makes a request."""
        headers = {'Accept-Encoding': 'gzip, deflate'}
        res = requests.get(url, headers=headers)
        json_data = res.text
        py_data = json.loads(json_data)
        return py_data

    def flight_for_month(self, py_data):
        prices = []
        d_time = []
        duration = []
        airline = []
        link = []
        transfers = []
        for idx in py_data:
            prices.append(idx["price"])
            d_time.append(idx["departure_at"])
            duration.append(idx["duration"])
            airline.append(idx["airline"])
            link.append(idx["link"])
            transfers.append(idx['transfers'])

        flight_for_month = {}
        for i in range(len(prices)):
            flight = {}
            flight['price'] = prices[i]
            flight['departure_at'] = d_time[i]
            flight['duration'] = duration[i]
            flight['airline'] = airline[i]
            flight['link'] = link[i]
            flight['transfers'] = transfers[i]
            date_flight = ConvertDateTime().format_big_to_small(d_time[i])
            flight_for_month[str(date_flight)] = flight
        return flight_for_month

    def offers(self, **kwargs):
        url = self.patricular_url_for_req(**kwargs)
        py_data = self.request(url)
        if py_data['data'] == []:
            return
        else:
            flight_for_month = self.flight_for_month(py_data['data'])
            return flight_for_month


ser = Search()
start_time = datetime.now()
dict, airport, arr_period_dates = ser.collects_all_flights_for_all_routes(start_date='2023.06.20',
                                                                          end_date='2023.07.20',
                                                                          airports=['LED', 'MOW', 'TOF'],
                                                                          start_period=['2023.06.20', '2023.06.30'],
                                                                          end_period=['2023.07.10', '2023.07.20'],
                                                                          home='LED', finish='LED')
end_time = datetime.now()
delta_time = end_time - start_time
print(f"Requests and collects all routes {delta_time}")
start_time = datetime.now()
G, all_routes = ser.compute_all_routes(dict, airport, arr_period_dates, home='LED', finish='LED',
                                       tranzit=[('TOF', 30160)], hate_airl=['5N'])
end_time = datetime.now()
delta_time = end_time - start_time
print(f"DFS {delta_time}")
start_time = datetime.now()

best_routes, price = ser.find_cheapest_route(all_routes)
best_routes, sorted_time = ser.find_short_in_time_route(all_routes)



# возможность фиксировать дату вылета(диапазон) и дату прилета (интерфейс) (готово),
# возможность задавать для пересадки доп. время, например - больше суток или от m до k суток (сделала пересадку от n времени)
# возможность сортировки по времени в полете(готово),
# возможность исключать конкретные авиакомпании, напрмиер - Победу,
# задавать город старта! Сейчас не реализовано, костыль.
# find_short_in_time_route - допиши (готово)
# сделать проверку на существование аэропорта
# path len!

# транзит - город+минимальное время прибывания в нем(сейчас в минутах)
