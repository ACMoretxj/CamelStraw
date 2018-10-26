from ..util import uid, singleton
from ..task import IDispatchable
from .job import JobContainer
from .worker import WorkerManager


@singleton
class Slave(IDispatchable):

    def __init__(self):
        self.__id: str = uid(__class__.__name__)
        self.__worker_manager: WorkerManager = WorkerManager()

    @property
    def id(self):
        return self.__id

    def weight(self):
        return self.__worker_manager.weight()

    def dispatch(self, *jobs: JobContainer):
        for job in jobs:
            self.__worker_manager.dispatch(job)

    def start(self):
        self.__worker_manager.start()

    def stop(self):
        self.__worker_manager.stop()
        print(self.__worker_manager.result)
