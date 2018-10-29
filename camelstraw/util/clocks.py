import time


class Stopwatch:

    def __init__(self):
        self.__start_time: float = None
        # milliseconds
        self.start_time = property(lambda: int(self.__start_time * 1000))

    def start(self):
        self.__start_time = time.time()
        return self

    @property
    def elapsed_time(self) -> int:
        if not self.__start_time:
            return 0
        return int((time.time() - self.__start_time) * 1000)


class TimeFormat:

    @staticmethod
    def from_millisecond(milli: int, fmt='%Y-%m-%d %H:%M:%S') -> str:
        stamp = time.localtime(milli / 1000)
        return time.strftime(fmt, stamp)
