from datetime import datetime, timedelta
from typing import Any
import datetime_utils
from datetime import datetime, timedelta
from typing import Any
import datetime_utils

class Route:
    """
    The instance of this class is stores one route (all data about them).

    Before flight will add to storage, check does is fit the timing - time for tranzit and time for last flight.
    """
    def __init__(self, start: str, finish: str, tranzit=None):
        self.start = start
        self.finish = finish
        self.tranzit = tranzit
        self.storage = []

    def len_tranzit(self, city: str):
        '''
        :param tranzit: list with tuple in format (arrival_city: str, time_tranzit: int):
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

    def period_for_first_departure(self, x, start_date, end_date):
        necessary_date = datetime_utils.convert_period_for_dates(start_date, end_date)
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

    def total_price(self) -> float:
        # Метод возвращает сумму стоимостей всех билетов в этом маршруте
        price = 0
        for idx, route in enumerate(self.storage):
            flight = route[2]
            price += flight['weight']
        return price

    def total_time(self) -> float:
        duration = 0
        for idx, time in enumerate(self.storage):
            flight = time[2]
            duration += flight['time_in_sky']
        return duration
