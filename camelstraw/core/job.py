from typing import List

from camelstraw.core.session import SessionManager
from camelstraw.util import IAnalysable, Stopwatch, uid


class Job(IAnalysable):

    def __init__(self, job_id='Job-%s' % uid):
        super().__init__(_id=job_id)
        self.__session_manager: SessionManager = SessionManager()
        self.__stopwatch: Stopwatch = Stopwatch().start()

    def analyse(self) -> None:
        self._latency = self.__stopwatch.elapsed_time
        self._total_request = self.__session_manager.total_request
        self._success_request = self.__session_manager.success_request


class JobManager(IAnalysable):

    def __init__(self):
        super().__init__(uid(__class__.__name__))
        self.__jobs: List = []
        self.__stopwatch: Stopwatch = Stopwatch().start()

    def add(self, job: Job):
        self.__jobs.append(job)

    def analyse(self) -> None:
        self._latency = self.__stopwatch.elapsed_time
        for job in self.__jobs:
            self._total_request += job.total_request
            self._success_request += job.success_request
