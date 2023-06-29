import re
from search import Search
import air_iata
import datetime
import sql_users

class SearchRequestData:
    def __init__(self, user_id):
        self.start_date = None
        self.end_date = None
        self.airports = []
        self.start_period = None
        self.end_period = None
        self.home = None
        self.finish = None
        self.tranzit = []
        self.hate_airl = []
        self.user_id = user_id
        self.storage_of_route = []

    # @staticmethod
    def append_routes_to_storage(self, value):
        all_route = []
        for route in value:
            if route != []:
                all_route.append(route)
        if all_route == []:
            self.storage_of_route = [None]
        else:
            self.storage_of_route = all_route
        print(f''
              f'Данные добавлены в хранилище SearchRequestData'
              f'')
        print(
              f'Добавлено {self.storage_of_route}'
        )

    def append_airport(self, airport: str):
        self.airports.append(airport)
        sql_users.append_airports(self.user_id, airport)

    def set_start_date(self, value: str):
        date_pattern = r'\d{4}.\d{2}.\d{2}'
        # Паттерн для проверки периода в формате DD/MM/YYYY - DD/MM/YYYY
        period_pattern = r'\d{4}.\d{2}.\d{2}\s*-\s*(\d{4}.\d{2}.\d{2})'
        if re.fullmatch(date_pattern, value):
            self.start_date = value
            self.start_period = [value, value]
            sql_users.append_start_date(self.user_id, value)
            sql_users.append_start_period(self.user_id, [value, value])
            return True
        elif re.fullmatch(period_pattern, value):
            period_pattern = r'(\d{4}.\d{2}.\d{2})\s*-\s*(\d{4}.\d{2}.\d{2})'
            match = re.search(period_pattern, value)
            if match:
                first_date = datetime.datetime.strptime(match.group(1), '%Y.%m.%d')
                second_date = datetime.datetime.strptime(match.group(2), '%Y.%m.%d')
                if second_date < first_date:
                    return False
                first_date = match.group(1)
                second_date = match.group(2)
                self.start_date = first_date
                sql_users.append_start_date(self.user_id, first_date)
                self.start_period = [first_date, second_date]
                sql_users.append_start_period(self.user_id, [first_date, second_date])
                return True
        else:
            return False

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
            sql_users.append_tranzit(self.user_id, (air, int(days_for_tranzit) * 24 * 60))
            return True
        elif match_h:
            hours_for_tranzit = match_h.group(1)
            air = self.airports[-1]
            self.tranzit.append((air, int(hours_for_tranzit) * 60))
            sql_users.append_tranzit(self.user_id, (air, int(hours_for_tranzit) * 60))

            return True
        else:
            return False


    def append_hate_airl(self, airl: str):
        dict_airlines = air_iata.air_iata()
        if airl in dict_airlines:
            self.hate_airl.append(airl)
            sql_users.append_hate_airl(self.user_id, airl)
            return True
        else:
            return False

    def append_home(self, home):
        self.home = str(home)
        self.airports.append(home)
        sql_users.append_home(self.user_id, home)
        sql_users.append_airports(self.user_id, home)


    def append_circle(self, fact: bool):
        if fact == True:
            self.finish = self.home
            sql_users.append_finish(self.user_id, self.home)
    def append_finish_airport(self, airport):
        if airport != self.home:
            self.finish = str(airport)
            self.airports.append(airport)
            sql_users.append_finish(self.user_id, airport)
            sql_users.append_airports(self.user_id, airport)
            return True
        else:
            return False

    def append_date_or_period_to_finish(self, value):
        date_pattern = r'\d{4}.\d{2}.\d{2}'
        # Паттерн для проверки периода в формате DD/MM/YYYY - DD/MM/YYYY
        period_pattern = r'\d{4}.\d{2}.\d{2}\s*-\s*\d{4}.\d{2}.\d{2}'
        if re.fullmatch(date_pattern, value):
            first_date = datetime.datetime.strptime(self.start_date, '%Y.%m.%d')
            second_date = datetime.datetime.strptime(value, '%Y.%m.%d')
            if second_date < first_date:
                return False
            else:
                self.end_date = value
                sql_users.append_end_date(self.user_id, value)
                self.end_period = [value, value]
                sql_users.append_end_period(self.user_id, [value, value])

            return True
        elif re.fullmatch(period_pattern, value):
            match = re.search(r"(\d{4}.\d{2}.\d{2})\s*-\s*(\d{4}.\d{2}.\d{2})", value)
            if match:
                first_date = datetime.datetime.strptime(match.group(1), '%Y.%m.%d')
                second_date = datetime.datetime.strptime(match.group(2), '%Y.%m.%d')
                departure_from_home = datetime.datetime.strptime(self.start_date, '%Y.%m.%d')
                if second_date < first_date:
                    return False
                elif second_date < departure_from_home:
                    return False
                else:
                    first_date = match.group(1)
                    second_date = match.group(2)
                    self.end_date = second_date
                    sql_users.append_end_date(self.user_id, second_date)
                    self.end_period = [first_date, second_date]
                    sql_users.append_end_period(self.user_id, [first_date, second_date])
                return True
        else:
            return False

    def append_start_date_exception_sql(self, date):
        self.start_date = date
    def append_home_exception_sql(self, home):
        self.home = str(home)
    def append_time_tranzit_exception_sql(self, value):
        self.tranzit.append(value)
    def append_finish_exception_sql(self, value):
        self.finish = value

    def append_start_period_exception_sql(self, value):
        self.start_period = value

    def append_end_period_exception_sql(self, value):
        self.end_period = value
    def append_end_date_exception_sql(self, value):
        self.end_date = value
    def append_hate_airl_exception_sql(self, value):
        self.hate_airl = value

    def start(self):
        return self.start_date, self.end_date, self.airports, self.start_period, self.end_period, self.home, self.finish, self.tranzit, self.hate_airl