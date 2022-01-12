class AtolInitError(Exception):
    def __init__(self, message="Couldn't connect to Atol Web Server"):
        super().__init__(message)


class AtolRequestError(Exception):
    def __init__(self, message="Request error"):
        super().__init__(message)


class AtolNewDocError(Exception):
    def __init__(self, message="Error on create new fiscal document", errors=None):
        super().__init__(message)
        self.error = errors
        if type(self.error) == list:
            print("Errors:")
            for error in errors:
                print(f"- {error}")
