import signal

class TimeoutError(Exception):
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)
