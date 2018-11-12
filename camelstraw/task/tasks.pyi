import datetime
from abc import ABCMeta, abstractmethod
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler


class Task(metaclass=ABCMeta):
    @abstractmethod
    def start(self, *args, **kwargs) -> None: pass
    @abstractmethod
    def stop(self, *args, **kwargs) -> None: pass


class PeriodTask(Task):
    __scheduler: BackgroundScheduler
    time_start: str
    time_end: str
    interval: int
    def __init__(self, interval: int, time_start: datetime=None, time_end: datetime=None): pass
    def start(self, func: Callable, *args, **kwargs) -> None: pass
    def stop(self) -> None: pass
