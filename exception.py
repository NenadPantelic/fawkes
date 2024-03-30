class HogwartsException(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self._message = message
        self._status = status

    @property
    def status(self):
        return self._status

    @property
    def message(self):
        return self._message


UNAUTHORIZED = HogwartsException("Unauthorized.", 401)
NOT_FOUND = HogwartsException("Not found.", 404)
