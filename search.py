import copy
import json
from itertools import combinations
from typing import List, Dict, Union, Any
import networkx as nx
import numpy as np
import requests
import datetime_utils
from route import Route
import air_iata
import time
from datetime import datetime, timedelta
from itertools import product
from multiprocessing import Process, Lock

class Search():

    def __init__(self, token="191827beb804bd4d4025b75737717e18"):
        self.token = token

    def find_flights_fo_period(self, airports, start_date, end_date, s_period, e_period, home, finish):
        '''To covert period for many separate dates.
           To call request.
           To save arr with dates of flights for all period.
        '''

        different_month = datetime_utils.period_for_month(start_date, end_date)
        flights_on_data = []
        for i in range(len(different_month)):
            data = (different_month)[i]
            flights = self.offers(origin=airports[0], destination=airports[1], departure_at=data,
                                              return_at='',
                                              market="ru", limit=1000, sorting="price")
            if i == 0 and flights != None:
                flights_on_data = flights
            elif flights == None:
                continue
            else:
                if flights_on_data == None:
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
        period_in_dates = datetime_utils.convert_period_for_dates(start_period, end_period)
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


    def compute_all_routes(self, start_date, end_date, airports, start_period, end_period, home, finish, tranzit, hate_airl):
        '''                      start_date, end_date, airports, start_period, end_period, home, finish, tranzit
        Input: dict with all possible flights between all selected airports.
        To compute all possible routes from all flights.
        Return: Graf and array with routes.
        '''
        airports = self.convert_city_to_air(airports)
        home = self.convert_city_to_air(home)
        finish = self.convert_city_to_air(finish)
        tranzit = self.convert_tranzit_city_to_air(tranzit)
        if hate_airl != [] and hate_airl != None:
            hate_airl = self.convert_name_airlines_to_iata(hate_airl)
        start_time = time.time()
        flights, combinations_airports, arr_period_date = self.collects_all_flights_for_all_routes(start_date=start_date,
                                                                                end_date=end_date,
                                                                                airports=airports,
                                                                                start_period=start_period,
                                                                                end_period=end_period,
                                                                                home=home, finish=finish)
        end_time = time.time()
        execution_time = end_time - start_time
        print("Время выполнения request:", execution_time, "секунд")
        start_time = time.time()
        G = nx.MultiDiGraph()
        airports = []
        for idx, i in enumerate(combinations_airports):
            airports.append(i[0])
            airports.append(i[1])
        airports = set(airports)
        G.add_nodes_from(airports)
        for idx, i in enumerate(combinations_airports):
            time_data = flights[i]
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
        end_time = time.time()
        execution_time = end_time - start_time
        print("Время выполнения dfs:", execution_time, "секунд")
        return G, all_routes

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

        arr_period_dates = datetime_utils.convert_period_for_dates(start_date, end_date)
        return dict, combinations_airports, arr_period_dates

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
              f'&limit={limit}&token={self.token}' \
              f'&campaign_id=100'
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
            date_flight = datetime_utils.format_big_to_small(d_time[i])
            flight_for_month[str(date_flight)] = flight
        return flight_for_month

    def offers(self, **kwargs):
        url = self.patricular_url_for_req(**kwargs)
        py_data = self.request(url)

        if py_data['data'] == [] or py_data['success'] == False:
            return
        else:
            flight_for_month = self.flight_for_month(py_data['data'])
            return flight_for_month
    def convert_city_to_air(self, citys):
        with open(r"city2code.json", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(citys, str):
                airports = data[citys]
                return airports
            airports = [data[key] for key in citys]
            return airports

    def convert_tranzit_city_to_air(self, citys):
        with open(r"city2code.json", encoding="utf-8") as f:
            data = json.load(f)
            if citys != []:
                new_tranzit_list = []
                airports = [data[tuple_city_and_time[0]] for tuple_city_and_time in citys]
                for idx, i in enumerate(citys):
                    new_tranzit_list.append((airports[idx], i[1]))
                return new_tranzit_list

    def convert_name_airlines_to_iata(self, airlines):
        dict_airlines = air_iata.air_iata()
        iata_airlines = []
        for name_company in airlines:
            iata_airlines.append(dict_airlines[name_company])
        return iata_airlines
