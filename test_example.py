# from bot import compute_route_handler, home_handler
# from random import randint
# class ChatMockup:
#     def __init__(self, id):
#         self.id = id
#
# class MessageMockup:
#     """Это типа сообщение из чата, но не оно.
#     Тут прописаны нужные для работы кода элементы
#     """
#     def __init__(self, chat_id: int, message_text: str):
#         self.chat = ChatMockup(chat_id)
#         self.text = message_text
#         self.message_id = randint(0, 100)
#
# class CallbackQueryMockup:
#     def __init__(self, chat_id: int, data: str):
#         self.message = MessageMockup(chat_id, message_text="")
#         self.data = data
#
#
#
# def test_select_first_city():
#     CHAT_ID = 1
#
#     compute_route_callback_query = CallbackQueryMockup(CHAT_ID, data="compute_route")
#     compute_route_handler(compute_route_callback_query)
#     city_name_message = MessageMockup(CHAT_ID, message_text="Санкт-Петербург")
#     home_handler(city_name_message)
#
# if __name__ == "__main__":
#     test_select_first_city()