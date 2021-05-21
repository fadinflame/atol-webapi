import requests
import random
import string
from exceptions import *
import time
import logging


class AtolAPI:
    def __init__(self, host, port, cashier_name):
        """
        Инициализация экземпляра Atol API

        :param host: хост сервера
        :param port: порт сервера
        :param cashier_name: (Опционально) Кассир
        """
        self.host = host
        self.port = port
        self.web_url = f"http://{host}:{port}/"
        self.cashier_name = cashier_name
        logging.basicConfig(filename="atol-webapi.log", format='[%(asctime)s] - %(message)s', level=logging.INFO)
        logging.info(f"Инициализация Atol API...")
        if not self.__ping_webserver():
            raise AtolInitError(f"Couldn't connect to Atol Web Server on '{self.web_url}'")

    def __str__(self):
        return f"AtolAPI Instance<{self.web_url}>"

    def __ping_webserver(self):
        """ Проверка соединения с Atol сервером """
        try:
            return requests.get(self.web_url, timeout=3).status_code == 200
        except requests.exceptions.ConnectTimeout:
            return False

    def __gen_uuid(self, length=8):
        """
        Генерация уникального ID для задачи

        :param length Длина генерируемого ID
        """
        return "".join(random.choice(string.ascii_letters) for i in range(length))

    def __call_api(self, method, data=None, url="requests/"):
        """
        API запрос на сервер

        :param method: GET или POST
        :param data: json для POST запроса, пуст если метод GET
        :param url: (Опционально) адрес до корня API, может модифицироваться для GET запросов
        :return: Экземпляр класса Response
        """
        if method.lower() not in ("get", 'post'):
            raise AtolRequestError("Calling API with a non-existent method")
        if data is None and method.lower() == "post":
            raise AtolRequestError("Calling API on POST method when data is None")
        elif data is not None and method.lower() == "get":
            data = {}
        request = requests.request(method, self.web_url + url, json=data)
        return request

    def __get_request_result(self, uuid):
        """
        Получение результата исполненной задачи
        :param uuid: идентификатор отправленной задачи
        :return: JSON ответ от сервера
        """
        return self.__call_api("GET", url=f"requests/{uuid}").json()["results"][0]

    def __add_task(self, dict_data):
        """
        Добавляет задачу для Веб-сервера

        :param dict_data: JSON с аргументами для сервера
        :return: JSON результат задачи, либо исключение
        """
        json_data = {
            "uuid": self.__gen_uuid(),
            "request": [
                dict_data
            ]
        }
        request = self.__call_api("POST", data=json_data)
        logging.info(f"Добавление задания...\nJSON: {json_data}")
        if request.status_code == 201:
            logging.info(f"Задание создано. Ожидаем 5 секунд...")
            time.sleep(5)
            return self.__get_request_result(json_data["uuid"])
        else:
            raise AtolRequestError(f"Unsuccessful add task request: {request.text}")

    def get_shift_status(self):
        """
        Получение состояния смены

        :return: возможные варианты - 'opened', 'closed', 'expired'
        """
        dict_data = {"type": "getShiftStatus"}
        task = self.__add_task(dict_data)
        return task["result"]["shiftStatus"]["state"]

    def close_shift(self):
        """
        Закрытие смены

        :return: Если статус смены подходит - JSON ответ, если нет - строка состояния
        """
        shift_status = self.get_shift_status()
        if shift_status == "closed":
            return "Смена уже закрыта"

        return self.__add_task({
            "type": "closeShift",
            "operator": {
                "name": self.cashier_name
            }
        })

    def open_shift(self):
        """
        Открытие смены

        :return: Если статус смены подходит - JSON ответ, если нет - строка состояния
        """
        shift_status = self.get_shift_status()
        if shift_status == "opened":
            return "Смена уже открыта"
        elif shift_status == "expired":
            self.close_shift()
            return "Смена истекла и была принудительно закрыта"

        return self.__add_task({
            "type": "openShift",
            "operator": {
                "name": self.cashier_name
            }
        })

    def print_previous(self):
        """
        Печать копии последнего чека

        :return: JSON результат
        """
        return self.__add_task({
            "type": "printLastReceiptCopy",
        })
