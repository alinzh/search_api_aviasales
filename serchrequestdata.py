import re
from search import Search
import air_iata
import datetime
import sql_users

class SearchRequestData:
    """
    Here is stores all data about users input for search tickets in the future. Instance class separate created
    for every user. All that func is stores will be options (filter) for search thickets.

    Every func from this class does some processing of data, checking for correctly form and added to storage (__init__).

    Data also added to SQL(it is important because might happen with bot and bot will be falling down,
    or will download updates)
    """
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
        self.chronological = False
        self.circle_or_not = False

    def append_airport(self, airport: str):
        """
        Added not first and not last airport
        """
        self.airports.append(airport)
        sql_users.append_airports(self.user_id, airport)

    def set_start_date(self, value: str):
        """
        :param first_value: date of first departure or first date from period of first departure
        :param second_value: second date from period of first departure
        """
        date_pattern = r'\d{4}.\d{2}.\d{2}'
        # Паттерн для проверки периода в формате DD/MM/YYYY - DD/MM/YYYY
        period_pattern = r'\d{4}.\d{2}.\d{2}\s*-\s*(\d{4}.\d{2}.\d{2})'
        if re.fullmatch(date_pattern, value):
            if '-' not in str(value):
                self.start_date = value
                self.start_period = [value, value]
                sql_users.append_start_date(self.user_id, value)
                sql_users.append_start_period(self.user_id, [value, value])
                return True
            else:
                return False
        elif re.fullmatch(period_pattern, value):
            period_pattern = r'(\d{4}.\d{2}.\d{2})\s*-\s*(\d{4}.\d{2}.\d{2})'
            match = re.search(period_pattern, value)
            if match:
                if '-' in match.group(1):  # Если в формате есть точка, возвращаем False
                    return False
                if '-' in match.group(2):  # Если в формате есть точка, возвращаем False
                    return False
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
        """
        Added time for tranzit in city,
        tranzit is str in format days or hours. Checking is it contain 'д' or 'ч'
        """
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
        if fact:
            self.finish = self.home
            sql_users.append_finish(self.user_id, self.home)
            self.circle_or_not = True
            sql_users.append_circle(self.user_id, fact)

    def append_chronological(self, fact: bool):
        if fact:
            self.chronological = fact
            sql_users.append_chronological(self.user_id, fact)

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
    def append_circle_or_not_exception_sql(self, value):
        self.circle_or_not = value
    def append_chronological_exception_sql(self, value):
        self.chronological = value

    def start(self):
        """This func is called last, is return all data"""

        if self.chronological:
            if not self.circle_or_not:
                if len(self.airports) == 2:
                    self.finish = self.airports[-1]
                    self.end_date = self.start_date
                    if self.start_period == None:
                        self.start_period = [self.start_date, self.start_date]
                    if self.end_period == None:
                        self.end_period = self.start_period
                else:
                    self.finish = self.airports[-1]

        return self.start_date, self.end_date, self.airports, self.start_period, self.end_period, \
            self.home, self.finish, self.tranzit, self.hate_airl, self.chronological