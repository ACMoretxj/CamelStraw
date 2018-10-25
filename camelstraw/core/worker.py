import asyncio
import multiprocessing
import sys
from multiprocessing import Process, cpu_count
from typing import TypeVar, Coroutine

from ..settings import WORKER_TIMEOUT
from ..exception import WrongStatusException, WorkerExecuteException
from .job import JobManager, Job, JobContainer
from .interfaces import IAnalysable, IManager, CoreStatus
from ..task import RoundRobin, IDispatchable
from ..util import uid
AllJobTypeHint = TypeVar('AllJobTypeHint', Job, JobContainer)


async def __work_timeout(worker, timeout=None):
    """
    worker's stop trigger for timeout mechanism
    :param worker:
    :param timeout: seconds
    :return:
    """
    timeout = WORKER_TIMEOUT if timeout is None else max(1, timeout)
    await asyncio.sleep(timeout)
    try:
        worker.stop()
        worker.analyse()
    except WrongStatusException:
        pass


async def __worker_notice(worker):
    """
    worker's stop trigger for message queue mechanism
    :param worker:
    :return:
    """
    pass


async def __stop_work(worker, timeout=None) -> asyncio.Future:
    """
    all worker's stop triggers
    :param worker:
    :param timeout: seconds
    :return:
    """
    tasks = (
        __work_timeout(worker, timeout),
        __worker_notice(worker)
    )
    return asyncio.gather(*tasks)


def start_work(jobs, worker, timeout=None) -> None:
    if multiprocessing.current_process().name == 'MainProcess':
        raise WorkerExecuteException('worker can only run at child process')
    tasks = [job.start() for job in jobs]
    tasks.append(__stop_work(worker, timeout))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
    print(worker)


class Worker(IAnalysable, IDispatchable):
    """
    worker process response for executing several jobs,
    every worker's data is exist in an independent process
    so that all the communication with main process should
    be done in a message queue
    """
    def __init__(self, weight=1):
        self.__job_manager: JobManager = JobManager()
        self.__weight: int = weight
        super().__init__(uid(__class__.__name__), self.__job_manager)

    def start(self) -> None:
        # not dispatched jobs, just return
        if len(list(self.__job_manager)) <= 0:
            return
        process = Process(target=start_work, args=(list(self.__job_manager), self))
        super().start()
        process.start()

    def dispatch(self, job: Job) -> None:
        if not isinstance(job, Job):
            raise TypeError('Worker.dispatch only accept Job type')
        if self.status != CoreStatus.INIT:
            raise WrongStatusException('Worker can only be dispatched job at init status')
        self.__job_manager.add(job)

    def weight(self) -> int:
        return self.__weight


class WorkerManager(IManager, IDispatchable):
    """
    initialize workers and dispatch jobs for them
    """
    def __init__(self, worker_num: int=None):
        super().__init__(uid(__class__.__name__))
        self.__balancer = RoundRobin()
        if worker_num is None:
            self.__worker_num = cpu_count()
        else:
            self.__worker_num: int = min(max(worker_num, 1), cpu_count() * 2)
        [self.add(Worker()) for _ in range(self.__worker_num)]

    def dispatch(self, job: AllJobTypeHint, worker: Worker=None) -> None:
        if worker is None:
            worker = self.__balancer.choose(self._container)
        if isinstance(job, JobContainer):
            job = job.job()
        elif isinstance(job, Job):
            pass
        worker.dispatch(job)

    def weight(self) -> int:
        return self.__worker_num

    def start(self):
        [worker.start() for worker in self._container]
