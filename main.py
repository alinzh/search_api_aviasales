import json

import numpy as np
import requests
from typing import List, Dict, Union, Any
from datetime import datetime, timedelta
# import datetime
# import time
import pandas as pd
from itertools import combinations
import networkx as nx
import itertools
import heapq
import copy


token = f"191827beb804bd4d4025b75737717e18"

# создать класс Route
# оздать метод добавлнеия edge (перелет из города А в город В), который возвращает True|False
# append сможет выполниться если дататайм добавляемого edge больше, чем дататайм предыдущего на n время (полет + пересадка)
# долж
# class MyList:
#     def __init__(self):
#         self.storage = []
#     def __getitem__(self, index):
#         return self.storage[index]
#     def append(self, x):
#         if x != "jopa":
#             self.storage.append(x)
#             return True
#         else:
#             return False
class Covert_date_time:
    def covert_period_for_dates(self, start_date, end_date):
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

class Route:
    def __init__(self, start : str):
        self.start = start
        self.storage = []

    def append(self, x, tranzit = 60) -> bool:
        # Проверить даейттайм добавлемоего edge (он же х тут), чтобы он был больше, чем у storage[-1]. Если ок - добавить х в self.storeage и вернуть True.
        if len(self.storage) >= 1:
            dict_atrr_2 = x[2]
            second_date = dict_atrr_2['time']
            date_format = '%Y-%m-%dT%H:%M:%S%z'
            date_2 = datetime.strptime(second_date, date_format) # дата вылета рейса x
            y = self.storage[-1]
            dict_atrr_1 = y[2]
            first_data = dict_atrr_1['time']
            data_1 = datetime.strptime(first_data, date_format) # дата вылета рейса storage[-1]
            flight_duration = dict_atrr_1['time_in_sky'] # время полета рейса storage[-1], т.е. У
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
        raise NotImplementedError

    def period_for_first_departure(self, x, start_time, end_time):
        necessary_date = Covert_date_time().covert_period_for_dates(start_date, end_date)
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

    def __init__(self, token = "191827beb804bd4d4025b75737717e18"):
        self.token = token

    def find_flights_fo_period(self, airports, start_date, end_date, s_period, e_period, home):
        '''To covert period for many separate dates.
           To call request.
           To save arr with dates of flights for all period.
        '''
        flights = {}
        if airports[0] == home:
            arr_period_dates = Covert_date_time().covert_period_for_dates(s_period[0], s_period[1])
            for idx, data in enumerate(arr_period_dates):
                flights_on_data = self.offers(origin=airports[0], destination=airports[1], departure_at=data,
                                              return_at='',
                                              market="ru", limit=1000, sorting="price")
                flights[data] = flights_on_data
        elif airports[1] == home:
            arr_period_dates = Covert_date_time().covert_period_for_dates(e_period[0], e_period[1])
            for idx, data in enumerate(arr_period_dates):
                flights_on_data = self.offers(origin=airports[0], destination=airports[1], departure_at=data,
                                          return_at='',
                                          market="ru", limit=1000, sorting="price")
                flights[data] = flights_on_data
        else:
            arr_period_dates = Covert_date_time().covert_period_for_dates(start_date, end_date)
            for idx, data in enumerate(arr_period_dates):
                flights_on_data = self.offers(origin=airports[0], destination=airports[1], departure_at=data, return_at='',
                                    market="ru", limit=1000, sorting="price")
                flights[data] = flights_on_data
        return flights, arr_period_dates
        raise NotImplementedError

    def time_for_transfer(self, *args, **kwargs):
        '''
        To select period between arrival and next flight
        To do: default value and selected time
        :return: ?

        '''
        return time_or_limitation
        raise NotImplementedError

    def find_paths_of_length(self, graph, node, path_len):
        paths = []
        visited = {node: True}

        def dfs(G, airport: Any, path: Route):
            for neighbor in graph.neighbors(airport):

                flights = [] #TODO: забрать edges между airport и neighbor из графа
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
                            dfs(G, neighbor, path_copy)
                            visited.pop(neighbor)

        dfs(graph, node, Route(node))
        return paths

    def compute_all_routes(self, dict_r, combinations_airports, arr_period_date, home = 'MOW'):
        '''
        Input: dict with all possible flights between all selected airports.
        To compute all possible routes from all flights.
        Return: Graf and array with routes.
        '''
        G = nx.MultiDiGraph()
        dict_routes = dict_r.copy()
        airports = []
        for idx, i in enumerate(combinations_airports):
            airports.append(i[0])
            airports.append(i[1])
        airports = set(airports)
        G.add_nodes_from(airports)
        edges = []
        for idx, i in enumerate(combinations_airports):
            time_data = dict_routes[i]
            key = 1
            for j in range(len(arr_period_date)):
                if len(time_data) < len(arr_period_date):
                    keys_list = list(time_data.keys())
                    if arr_period_date[j] not in time_data:
                        continue
                    elif time_data[arr_period_date[j]] == None:
                        continue
                    else:
                        for data_flight in time_data[arr_period_date[j]]:
                            G.add_edge(i[0], i[1], weight=data_flight[0], time=data_flight[1],
                                       time_in_sky=data_flight[2], airlines=data_flight[4], link=data_flight[5])
                elif time_data[arr_period_date[j]] == None:
                        continue
                else:
                    for data_flight in time_data[arr_period_date[j]]:
                        G.add_edge(i[0], i[1], weight=data_flight[0], time=data_flight[1], time_in_sky=data_flight[2], airlines=data_flight[4], link=data_flight[5])
        start = home
        all_routes = self.find_paths_of_length(G, start, path_len=(len(airports)+1))
        arr_with_routes = []
        for idx, route in enumerate(all_routes):
            arr_with_routes.append(route.storage)

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
        new_arr_r = [] #список экзмпляров класса route, отсортированный по возрастанию стоимости маршрута
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
        new_arr_t = [] #список экзмпляров класса route, отсортированный по возрастанию времени на рейсы
        for i in sorted_indexes:
            new_arr_t.append(routes[i])
        return new_arr_t, sorted_time

    def collects_all_flights_for_all_routes(self, start_date, end_date, airports, start_period, end_period, home):
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
            req_for_period, arr_period_dates = self.find_flights_fo_period(pair_air, start_date, end_date, start_period, end_period, home)
            dict[pair_air] = req_for_period
        print(dict)
        arr_period_dates = Covert_date_time().covert_period_for_dates(start_date, end_date)
        return dict, combinations_airports, arr_period_dates
        raise NotImplementedError

    def patricular_url_for_req(self, *args, **kwargs):
        return self.url_for_req(feature="v3/prices_for_dates?", *args, **kwargs)

    def  url_for_req(self, origin, destination, departure_at, feature, market="ru", limit=1000, sorting="price", return_at =''):
        url = f'https://api.travelpayouts.com/aviasales/{feature}' \
              f'origin={origin}' \
              f'&destination={destination}' \
              f'&departure_at={departure_at}' \
              f'&return_at={return_at}' \
              f'&sorting={sorting}' \
              f'&limit={limit}&token={self.token}'
        return url

    def  request(self, url: str) -> Dict[str, Union[bool, List[Dict[str, Any]], str]]:
        """THis function makes a request."""
        res = requests.get(url)
        json_data = res.text
        py_data = json.loads(json_data)
        return py_data

    def best_price(self, py_data):
        prices = []
        d_time = []
        duration = []
        airline = []
        link = []
        for idx in py_data:
            prices.append(idx["price"])
            d_time.append(idx["departure_at"])
            duration.append(idx["duration"])
            airline.append(idx["airline"])
            link.append(idx["link"])
        best_offers = []

        data = list(zip(prices, d_time, duration, airline, link))
        # Сортировка списка кортежей по первому элементу (цене)
        sorted_data = sorted(data, key=lambda x: x[0])
        # Распаковка отсортированного списка кортежей обратно в отдельные списки
        sorted_prices, sorted_d_time, sorted_duration, sorted_airline, sorted_link = zip(*sorted_data)

        for i in range(len(sorted_prices)):
            offer = []
            offer.append(sorted_prices[i])
            offer.append(sorted_d_time[i])
            offer.append(sorted_duration[i])
            offer.append(sorted_prices[i])
            offer.append(sorted_airline[i])
            offer.append(f'https://www.aviasales.ru{sorted_link[i]}')
            best_offers.append(offer)

        return best_offers

    def offers(self, **kwargs):
        url = self.patricular_url_for_req(**kwargs)
        py_data = self.request(url)
        if py_data['data'] == []:
            return
        else:
            best_price = self.best_price(py_data['data'])
            return best_price

ser = Search()

dict, airport, arr_period_dates = ser.collects_all_flights_for_all_routes(start_date = '2023.06.20', end_date = '2023.07.20', airports = ['LED', 'OVB', 'MOW'], start_period = ['2023.06.20', '2023.06.25'], end_period = ['2023.07.15', '2023.07.20'], home = 'LED')
G, all_routes = ser.compute_all_routes(dict, airport, arr_period_dates, home = 'LED')
best_routes, price = ser.find_cheapest_route(all_routes)
best_routes, time = ser.find_short_in_time_route(all_routes)
print(best_routes, price)


# TODO: возможность фиксировать дату вылета(диапазон) и дату прилета (интерфейс),
# возможность задавать для пересадки доп. время, например - больше суток или от m до k суток,
# возможность сортировки по времени в полете,
# возможность исключать конкретные авиакомпании, напрмиер - Победу,
# задавать город старта! Сейчас не реализовано, костыль.
# find_short_in_time_route - допиши (готово)
# сделать проверку на существование аэропорта


