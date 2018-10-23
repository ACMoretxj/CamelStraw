from time import time


class Stopwatch:

    def __init__(self):
        self.__start_time: float = None

    def start(self):
        self.__start_time = time()
        return self

    @property
    def elapsed_time(self) -> int:
        if not self.__start_time:
            return 0
        return int((time() - self.__start_time) * 1000)
