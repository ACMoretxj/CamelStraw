from abc import ABCMeta, abstractmethod

from apscheduler.schedulers.background import BackgroundScheduler

from ..util import readonly, TimeFormat


class Task(metaclass=ABCMeta):

    @abstractmethod
    def start(self, *args, **kwargs): pass

    @abstractmethod
    def stop(self, *args, **kwargs): pass


class PeriodTask(Task):

    def __init__(self, interval, time_start=None, time_end=None):
        self.__scheduler = BackgroundScheduler()
        readonly(self, 'interval', lambda: interval)
        readonly(self, 'time_start', lambda: TimeFormat.from_datetime(time_start))
        readonly(self, 'time_end', lambda: TimeFormat.from_datetime(time_end))

    def start(self, func, *args, **kwargs):
        self.__scheduler.add_job(func, 'interval', args=args, kwargs=kwargs, seconds=self.interval // 1000,
                                 start_date=self.time_start, end_date=self.time_end)
        self.__scheduler.start()

    def stop(self):
        self.__scheduler.shutdown()
