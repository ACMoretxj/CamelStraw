import asyncio
from multiprocessing import Process

from camelstraw.exception import WrongStatusException
from .job import JobManager, Job
from .interfaces import IAnalysable, IManager, CoreStatus
from ..task import RandomBalancer, IDispatchMixin
from ..util import uid


async def stop_worker(worker):
    print('---------worker status---------%s' % worker.status)
    await asyncio.sleep(10)
    print('passed----------------')
    worker.stop()
    worker.analyse()
    print(worker)
    print('worker status: %s' % worker.status)


def do(jobs, worker):
    tasks = [job.start() for job in jobs]
    tasks.append(stop_worker(worker))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()


class Worker(IAnalysable, IDispatchMixin):
    """
    工作进程，负责执行一系列任务
    """
    def __init__(self, weight=None):
        self.__job_manager: JobManager = JobManager()
        self.__weight = weight
        super().__init__(uid(__class__.__name__), self.__job_manager)

    def start(self) -> None:
        super().start()
        process = Process(target=do, args=(list(self.__job_manager), self))
        process.start()
        process.join()

    def dispatch(self, job: Job) -> None:
        if self.status != CoreStatus.INIT:
            raise WrongStatusException('Worker can only be dispatched job at init status')
        self.__job_manager.add(job)

    def weight(self) -> int:
        return self.__weight or len(list(self.__job_manager))


class WorkerManager(IManager):
    """
    工作进程管理器，负责调度执行所管理的工作进程
    """
    def __init__(self):
        super().__init__(uid(__class__.__name__))

    def dispatch(self, job: Job, worker: Worker=None) -> None:
        if worker is None:
            worker = RandomBalancer.choose(self._container)
        worker.dispatch(job)
