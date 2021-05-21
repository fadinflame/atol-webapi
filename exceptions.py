class AtolInitError(Exception):
    def __init__(self, message="Couldn't connect to Atol Web Server"):
        super().__init__(message)


class AtolRequestError(Exception):
    def __init__(self, message="Request error"):
        super().__init__(message)
