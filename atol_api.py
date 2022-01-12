import requests
import random
import string
from exceptions import *
import time


class AtolAPI:
    def __init__(self, host, port, cashier_name=""):
        """
        Инициализация экземпляра Atol API

        :param host: хост сервера
        :param port: порт сервера
        :param cashier_name: (Опционально) Кассир
        """
        self.__web_url = f"http://{host}:{port}/"
        self.__cashier_name = {"name": cashier_name} if cashier_name else ""
        if not self.__ping_webserver():
            raise AtolInitError(f"Couldn't connect to Atol Web Server on '{self.__web_url}'")

    def __str__(self):
        return f"AtolAPI Instance<{self.__web_url}>"

    def __ping_webserver(self):
        """ Проверка соединения с Atol сервером """
        try:
            return requests.get(self.__web_url, timeout=3).status_code == 200
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
        request = requests.request(method, self.__web_url + url, json=data)
        return request

    def __get_request_result(self, uuid: str) -> dict:
        """
        Получение результата исполненной задачи
        :param uuid: идентификатор отправленной задачи
        :return: JSON ответ от сервера
        """
        return self.__call_api("GET", url=f"requests/{uuid}").json()["results"][0]

    def __add_task(self, dict_data: dict) -> dict:
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
        if request.status_code == 201:
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

    def close_shift(self, is_web=False):
        """
        Закрытие смены

        :return: Если статус смены подходит - JSON ответ, если нет - строка состояния
        """
        shift_status = self.get_shift_status()
        if shift_status == "closed":
            return "Смена уже закрыта"

        dict_data = {
            "type": "closeShift",
            "electronically": is_web
        }

        if self.__cashier_name:
            dict_data["operator"] = self.__cashier_name

        return self.__add_task(dict_data)

    def open_shift(self, is_web=False):
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

        dict_data = {
            "type": "openShift",
            "electronically": is_web
        }

        if self.__cashier_name:
            dict_data["operator"] = self.__cashier_name

        return self.__add_task(dict_data)

    def print_previous(self):
        """
        Печать копии последнего чека

        :return: JSON результат
        """
        return self.__add_task({
            "type": "printLastReceiptCopy",
        })

    def new_fiscal_doc(self, tp: str, items: list, tax_type: str, payment_type="cash", payment_sum=0.00, client="",
                       is_web=False, use_separator=True):
        """
        Создать новый фискальный документ


        :param tp: Тип документа
        :param items: Элементы документа
        :param tax_type: Вид налогообложения
        :param payment_type: Тип оплаты (cash, electronically)
        :param payment_sum: Оплата от клиента
        :param client: Номер телефона или email клиента
        :param is_web: Электронный ли чек
        :param use_separator: Использовать разделитель между позициями
        :return: JSON результат
        """
        types = ("sell", "buy", "sellReturn", "buyReturn")
        if tp not in types:
            raise AtolNewDocError(errors=[f"The type must be one of the values: {types}"])
        # подготавливаем запрос к кассе с параметрами
        json_data = {
            "type": tp,
            "taxationType": tax_type,
            "electronically": is_web,
            "ignoreNonFiscalPrintErrors": False,
            "items": [],
            "payments": [
                {
                    "type": payment_type,
                    "sum": payment_sum
                }
            ],
            "total": 0.00
        }

        if client:
            json_data["clientInfo"] = {"emailOrPhone": client}

        if self.__cashier_name:
            json_data["operator"] = self.__cashier_name

        # Добавляем позиции товаров/услуг в чек
        for product in items:
            keys = ('price', 'quantity', 'amount', 'tax', 'type', 'paymentObject', 'paymentMethod')
            for key in keys:
                if key not in product:
                    raise AtolNewDocError(
                        message=f"'{key}' key is required. Read more at https://integration.atol.ru/api")

            # считаем сумму позиции по кол-ву и стоимости, если не указано
            if product["amount"] == 0 or product["amount"] is None:
                product["amount"] = product["price"] * product["quantity"]

            json_data["items"].append(product)
            json_data["total"] += product["amount"]

            # добавляем разделитель между позициями
            if use_separator:
                json_data["items"].append({
                    "type": "text",
                    "text": "--------------------------------",
                    "alignment": "left",
                    "font": 0,
                    "doubleWidth": False,
                    "doubleHeight": False
                })

        # Если не не указано итого, то записываем, то что посчитали
        if json_data["payments"][0]["sum"] < json_data["total"]:
            json_data["payments"][0]["sum"] = json_data["total"]

        task = self.__add_task(json_data)
        return task
