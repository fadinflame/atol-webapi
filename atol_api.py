import requests
import random
import string
from exceptions import *


class AtolAPI:
    def __init__(self, host, port, cashier_name=""):
        self.host = host
        self.port = port
        self.web_url = f"http://{host}:{port}/"
        self.cashier_name = cashier_name
        if not self.__ping_webserver():
            raise AtolInitError(f"Couldn't connect to Atol Web Server on '{self.web_url}'")

    def __str__(self):
        return f"AtolAPI Instance<{self.web_url}>"

    def __ping_webserver(self):
        """ Check connection to the server """
        try:
            return requests.get(self.web_url, timeout=3).status_code == 200
        except requests.exceptions.ConnectTimeout:
            return False

    def __gen_uuid(self, length=8):
        """ Generate unique uuid for a task """
        return "".join(random.choice(string.ascii_letters) for i in range(length))

    def __call_api(self, method, data=None, url="requests/"):
        if method.lower() not in ("get", 'post'):
            raise AtolRequestError("Calling API with a non-existent method")
        if data is None and method.lower() == "post":
            raise AtolRequestError("Calling API on POST method when data is None")
        elif data is not None and method.lower() == "get":
            data = {}
        request = requests.request(method, self.web_url + url, data=data)
        return request

    def __get_request_result(self, uuid):
        return self.__call_api("GET", url=f"requests/{uuid}").text
