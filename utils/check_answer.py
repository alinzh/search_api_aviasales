import json
from datetime import datetime


class CheckData:
    """
    Func from this class checking users answer for incorrect.
    """

    def check_city(self, city):
        """
        Check name of city for spelling mistakes.
        """
        with open(r"../data/city2code.json", encoding="utf-8") as f:
            data2 = json.load(f)
            if city in data2:
                return True

    def check_if_city_in_route(self, city, airports_done):
        """
        Check repeat name of city or not.
        """
        if city in airports_done:
            return False
        else:
            return True

    def check_quantity_of_citys(self, airports_done, home, finish):
        """
        Check: if number of airports in one way route more the 5, return False.
        Check: if number of airports in circle route more the 4, return False.
        """
        if len(airports_done) > 4:
            if home == finish:
                return False
            elif len(airports_done) > 5:
                return False
            else:
                return True
        else:
            return True

    def check_period_duration(self, start, end):
        start = datetime.strptime(start, "%Y.%m.%d")
        end = datetime.strptime(str(end), "%Y.%m.%d")
        delta = end - start
        days = delta.days
        if days > 31:
            return False
        else:
            return True
