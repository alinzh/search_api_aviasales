import re
from search import Search


class SearchRequestData:
    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.airports = []
        self.start_period = None
        self.end_period = None
        self.home = None
        self.finish = None
        self.tranzit = []
        self.hate_airl = []

    def append_airport(self, airport: str):
        self.airports.append(airport)

    def set_start_date(self, value: str):
        date_pattern = r'\d{4}.\d{2}.\d{2}'
        # Паттерн для проверки периода в формате DD/MM/YYYY - DD/MM/YYYY
        period_pattern = r'\d{4}.\d{2}.\d{2}\s*-\s*(\d{4}.\d{2}.\d{2})'
        if re.fullmatch(date_pattern, value):
            self.start_date = value
            self.start_period = [value, value]
            return True
        elif re.fullmatch(period_pattern, value):
            period_pattern = r'(\d{4}.\d{2}.\d{2})\s*-\s*(\d{4}.\d{2}.\d{2})'
            match = re.search(period_pattern, value)
            if match:
                first_date = match.group(1)
                second_date = match.group(2)
                self.start_date = first_date
                self.start_period = [first_date, second_date]
                return True
        else:
            return False
        # Проверка, что формат даты `DD/MM/YYYY - DD/MM/YYYY` или `DD/MM/YYYY`. Смотри regular expressions (библиотека re)
        # И потом разобрать строку на даты и вставить в нужные поля.

    def append_time_tranzit(self, value: str):
        '''
        tranzit is str in format days or hours. Check is it contain 'д' or 'ч'
        :return:
        '''
        tranzit_pattern_days = r'^(\d+)[д]$'
        tranzit_pattern_hours = r'^(\d+)[ч]$'
        match_d = re.match(tranzit_pattern_days, value)
        match_h = re.match(tranzit_pattern_hours, value)
        if match_d:
            days_for_tranzit = match_d.group(1)
            air = self.airports[-1]
            self.tranzit.append((air, int(days_for_tranzit) * 24 * 60))
            return True
        elif match_h:
            hours_for_tranzit = match_h.group(1)
            air = self.airports[-1]
            self.tranzit.append((air, int(hours_for_tranzit) * 60))
            return True
        else:
            return False

    def append_hate_airl(self, airl: str):
        None

    def append_home(self, home):
        self.home = str(home)
        self.airports.append(home)

    def append_circle(self, fact: bool):
        if fact == True:
            self.finish = self.home

    def append_finish_airport(self, airport):
        self.finish = str(airport)
        self.airports.append(airport)

    def append_date_or_period_to_finish(self, value):
        date_pattern = r'\d{4}.\d{2}.\d{2}'
        # Паттерн для проверки периода в формате DD/MM/YYYY - DD/MM/YYYY
        period_pattern = r'\d{4}.\d{2}.\d{2}\s*-\s*\d{4}.\d{2}.\d{2}'
        if re.fullmatch(date_pattern, value):
            self.end_date = value
            self.end_period = [value, value]
            return True
        elif re.fullmatch(period_pattern, value):
            match = re.search(r"(\d{4}.\d{2}.\d{2})\s*-\s*(\d{4}.\d{2}.\d{2})", value)
            if match:
                first_date = match.group(1)
                second_date = match.group(2)
                self.end_date = second_date
                self.end_period = [first_date, second_date]
                return True
        else:
            return False

    def start(self):
        '''
        Is calling to search tickets
        :return:
        '''
        print(self.start_date, #период а не дата
              self.end_date,
              self.airports,
              self.start_period,#['2023.06.01 - 2023.06.02', '2023.06.02']
              self.end_period,
              self.home,
              self.finish,
              self.tranzit)

        sr = Search()
        self.airports = sr.convert_city_to_air(self.airports)
        self.home = sr.convert_city_to_air(self.home)
        self.finish = sr.convert_city_to_air(self.finish)
        self.tranzit = sr.convert_tranzit_city_to_air(self.tranzit)
        flights, air, arr_period_dates = sr.collects_all_flights_for_all_routes(start_date=self.start_date,
                                                                                end_date=self.end_date,
                                                                                airports=self.airports,
                                                                                start_period=self.start_period,
                                                                                end_period=self.end_period,
                                                                                home=self.home, finish=self.finish)
        G, all_routes = sr.compute_all_routes(flights, air, arr_period_dates, home=self.home, finish=self.finish,
                                              tranzit=self.tranzit, hate_airl=self.hate_airl)
        best_routes_price, price = sr.find_cheapest_route(all_routes)
        best_routes_time, sorted_time = sr.find_short_in_time_route(all_routes)
        return [best_routes_price[0].storage, price[0]], [[best_routes_time[0].storage], sorted_time[0]]
