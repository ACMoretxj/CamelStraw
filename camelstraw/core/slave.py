from camelstraw.core.job import Job
from camelstraw.core.worker import WorkerManager
from camelstraw.util import uid


class Slave:

    def __init__(self):
        self.__id: str = uid(__class__.__name__)
        self.__worker_manager: WorkerManager = WorkerManager()

    @property
    def id(self):
        return self.__id

    def dispatch(self, job: Job):
        self.__worker_manager.dispatch(job)
