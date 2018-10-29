from ..util import uid, singleton
from .job import JobContainer
from .worker import WorkerManager


@singleton
class Slave:

    def __init__(self, _id=uid(__class__.__name__)):
        self.__worker_manager: WorkerManager = WorkerManager()
        # properties
        self.id = property(lambda: self._id)
        self.result = property(lambda: self.__worker_manager.result)

    def dispatch(self, *jobs: JobContainer):
        [self.__worker_manager.dispatch(job) for job in jobs]

    def start(self):
        self.__worker_manager.start()

    def stop(self):
        self.__worker_manager.stop()
