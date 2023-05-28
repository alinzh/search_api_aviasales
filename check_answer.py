import json
class CheckData:
    def check_city(self, city):
        with open(r"C:\Users\Пользователь\PycharmProjects\pythonProject_avia\city2code.json", encoding="utf-8") as f:
            data2 = json.load(f)
            if city in data2:
                return True
    def check_if_city_in_route(self, city, airports_done):
        if city in airports_done:
            return False
        else:
            return True