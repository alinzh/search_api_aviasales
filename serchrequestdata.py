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

    def append_airport(self, airport: str):
        """
        Added not first and not last airport
        """
        self.airports.append(airport)
        sql_users.append_airports(self.user_id, airport)

    def set_start_date(self, first_value: str, second_value: str):
        """
        :param first_value: date of first departure or first date from period of first departure
        :param second_value: second date from period of first departure
        """
        date_pattern = r'\d{4}-\d{2}-\d{2}'

        if second_value == None:
            if re.fullmatch(date_pattern, str(first_value)):
                first_value = (str(first_value)).replace('-', '.')
                self.start_date = first_value
                self.start_period = [first_value, first_value]
                sql_users.append_start_date(self.user_id, first_value)
                sql_users.append_start_period(self.user_id, [first_value, first_value])
            return True
        
        elif first_value == None:
            if re.fullmatch(date_pattern, second_value):
                second_value = (str(second_value)).replace('-', '.')
                first_date = datetime.datetime.strptime(self.start_date, '%Y.%m.%d')
                second_date = datetime.datetime.strptime(second_value, '%Y.%m.%d')
                if second_date < first_date or (second_date - first_date).days >= 21:
                    return False
                else:
                    self.start_period = [self.start_date, second_value]
                    sql_users.append_start_period(self.user_id, [self.start_date, second_value])
                    return True

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

    def append_date_or_period_to_finish(self, first_value: str, second_value: str):
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        if second_value == None:
            if re.fullmatch(date_pattern, str(first_value)):
                first_value = (str(first_value)).replace('-', '.')
                first_date = datetime.datetime.strptime(self.start_date, '%Y.%m.%d')
                second_date = datetime.datetime.strptime(first_value, '%Y.%m.%d')
                if second_date < first_date:
                    return False
                if (second_date - first_date).days >= 31:
                    return False
                else:
                    first_value = str(first_value)
                    self.end_date = first_value
                    sql_users.append_end_date(self.user_id, first_value)
                    self.end_period = [first_value, first_value]
                    sql_users.append_end_period(self.user_id, [first_value, first_value])
                return True

        elif first_value == None:
            if re.fullmatch(date_pattern, str(second_value)):
                second_value = (str(second_value)).replace('-', '.')
                first_date = datetime.datetime.strptime(self.end_date, '%Y.%m.%d')
                second_date = datetime.datetime.strptime(second_value, '%Y.%m.%d')
                second_value = (str(second_value)).replace('-', '.')
                if second_date < first_date:
                    return False

                else:
                   self.end_period = [self.end_date, second_value]
                   sql_users.append_end_period(self.user_id, [self.end_date, second_value])
                   self.end_date = second_value
                   sql_users.append_end_date(self.user_id, second_value)
                return True

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
        """This func is called last, is return all data"""
        return self.start_date, self.end_date, self.airports, self.start_period, self.end_period, \
               self.home, self.finish, self.tranzit, self.hate_airl
