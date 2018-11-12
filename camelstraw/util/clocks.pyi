from datetime import datetime


class Stopwatch:
    __start_time: int
    start_time: int
    elapsed_time: int
    def start(self) -> None: pass

class TimeFormat:
    @staticmethod
    def from_millisecond(milli: int, fmt='%Y-%m-%d %H:%M:%S') -> str: pass
    @staticmethod
    def from_datetime(dtm: datetime, fmt='%Y-%m-%d %H:%M:%S') -> str: pass
