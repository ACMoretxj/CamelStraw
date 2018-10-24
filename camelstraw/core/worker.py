from camelstraw.core.job import JobManager, Job
from camelstraw.core.interfaces import IAnalysable, IManager
from camelstraw.task import RandomBalancer, IDispatchMixin
from camelstraw.util import uid


class Worker(IAnalysable, IDispatchMixin):

    def __init__(self, weight=1):
        self.__job_manager: JobManager = JobManager()
        self.__weight = weight
        super().__init__(uid(__class__.__name__), self.__job_manager)

    def dispatch(self, job: Job):
        self.__job_manager.add(job)

    def weight(self):
        return self.__weight


class WorkerManager(IManager):

    def __init__(self):
        super().__init__(uid(__class__.__name__))

    def dispatch(self, job: Job, worker: Worker=None) -> None:
        if worker is None:
            worker = RandomBalancer.choose(self._container)
        worker.dispatch(job)
