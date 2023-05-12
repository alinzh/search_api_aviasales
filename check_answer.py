import json
class CheckData:
    def check_city(self, city):
        with open(r"C:\Users\Пользователь\PycharmProjects\pythonProject_avia\city2code.json", encoding="utf-8") as f:
            data2 = json.load(f)
            print(data2)
            if city in data2:
                return True