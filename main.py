import copy
import json
from datetime import datetime, timedelta
from itertools import combinations
from typing import List, Dict, Union, Any
import networkx as nx
import numpy as np
import pandas as pd
import requests
import re
import datetime_utils
from route import Route
from search import Search
from serchrequestdata import SearchRequestData
# token = f"191827beb804bd4d4025b75737717e18"

# ser = Search()
# start_time = datetime.now()
# dict, airport, arr_period_dates = ser.collects_all_flights_for_all_routes(start_date='2023.06.20',
#                                                                           end_date='2023.07.20',
#                                                                           airports=['LED', 'MOW', 'TOF'],
#                                                                           start_period=['2023.06.20', '2023.06.20'],
#                                                                           end_period=['2023.07.10', '2023.07.20'],
#                                                                           home='LED', finish='LED')
# end_time = datetime.now()
# delta_time = end_time - start_time
# print(f"Requests and collects all routes {delta_time}")
# start_time = datetime.now()
# G, all_routes = ser.compute_all_routes(dict, airport, arr_period_dates, home='LED', finish='LED',
#                                        tranzit=[('TOF', 30160)], hate_airl=['5N'])
# end_time = datetime.now()
# delta_time = end_time - start_time
# print(f"DFS {delta_time}")
# start_time = datetime.now()
#
# best_routes, price = ser.find_cheapest_route(all_routes)
# best_routes, sorted_time = ser.find_short_in_time_route(all_routes)

# class User:
#     def analyzer(self, which_answer, answer):
#         NotImplementedError
#
#     def jopa(self):
#         NotImplementedError

# возможность фиксировать дату вылета(диапазон) и дату прилета (интерфейс) (готово),
# возможность задавать для пересадки доп. время, например - больше суток или от m до k суток (сделала пересадку от n времени)
# возможность сортировки по времени в полете(готово),
# возможность исключать конкретные авиакомпании, напрмиер - Победу,
# задавать город старта! Сейчас не реализовано, костыль.
# find_short_in_time_route - допиши (готово)
# сделать проверку на существование аэропорта
# path len!

# транзит - город+минимальное время прибывания в нем(сейчас в минутах)
