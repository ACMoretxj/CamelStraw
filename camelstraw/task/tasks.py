from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler


class PeriodTask:

    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, interval: int, time_start: datetime=None, time_end: datetime=None):
        self.interval: int = interval
        self.time_start: str = time_start.strftime(self.TIME_FORMAT) if time_start else None
        self.time_end: str = time_end.strftime(self.TIME_FORMAT) if time_end else None

    def start(self, func, args=None, kwargs=None) -> None:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func, 'interval', args=args, kwargs=kwargs, seconds=self.interval // 1000,
                          start_date=self.time_start, end_date=self.time_end)
        scheduler.start()
