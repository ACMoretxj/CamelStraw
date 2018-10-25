import asyncio
import multiprocessing
import sys
import time
from multiprocessing import Process, cpu_count, Lock as ProcessLock, Queue
from queue import Empty
from typing import TypeVar

from ..settings import WORKER_TIMEOUT, WORKER_CHECK_INTERVAL
from ..exception import WrongStatusException, WorkerExecuteException
from .job import JobManager, Job, JobContainer
from .interfaces import IAnalysable, IManager, CoreStatus
from ..task import RoundRobin, IDispatchable
from ..util import uid
AllJobTypeHint = TypeVar('AllJobTypeHint', Job, JobContainer)


def __try_stop_and_analyse(worker):
    """
    try to stop a worker and analyse result, then report the result
    to manager by queue
    :param worker: 
    :return: 
    """
    # use lock to perform stop & analyse safely
    with worker.lock:
        try:
            # stop the worker
            worker.stop()
            worker.analyse()
            # send compute result to worker manager
            with worker.queue_lock:
                worker.queue.put(('result', worker.json_result))
        except WrongStatusException:
            pass


async def __work_timeout(worker, timeout=WORKER_TIMEOUT):
    """
    worker's stop trigger for timeout mechanism
    :param worker:
    :param timeout: seconds
    :return:
    """
    if timeout is None or timeout <= 0:
        timeout = sys.maxsize
    timeout = int(timeout)
    while timeout > 0 and worker.status == CoreStatus.STARTED:
        # take a nap and check the worker status
        await asyncio.sleep(1)
    __try_stop_and_analyse(worker)


async def __worker_notice(worker):
    """
    worker's stop trigger for message queue mechanism
    :param worker:
    :return:
    """
    interval = max(1, int(WORKER_CHECK_INTERVAL))
    while worker.status == CoreStatus.STARTED:
        with worker.queue_lock:
            try:
                message = worker.queue.get_nowait()
                if message[0] == 'stop':
                    # it's a stop command from manager, stop self
                    break
                else:
                    # it's a result message from worker, put it back
                    worker.queue.put(message)
            except Empty:
                pass
        # wait several seconds and go on getting
        await asyncio.sleep(interval)
    __try_stop_and_analyse(worker)


async def __stop_work(worker, timeout=None) -> asyncio.Future:
    """
    all worker's stop triggers
    :param worker:
    :param timeout: seconds
    :return:
    """
    tasks = (
        __worker_notice(worker),
        __work_timeout(worker, timeout),
    )
    return asyncio.gather(*tasks)


def start_work(jobs, worker, timeout=None) -> None:
    """
    :param jobs:
    :param worker
    :param timeout:
    :return:
    """
    if multiprocessing.current_process().name == 'MainProcess':
        raise WorkerExecuteException('worker can only run at child process')
    tasks = [job.start() for job in jobs]
    tasks.append(__stop_work(worker, timeout))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()


class Worker(IAnalysable, IDispatchable):
    """
    worker process response for executing several jobs,
    every worker's data is exist in an independent process
    so that all the communication with main process should
    be done in a message queue
    """
    def __init__(self, queue_lock: ProcessLock, queue: Queue, weight=1):
        self.__job_manager: JobManager = JobManager()
        # the worker itself has an another lock for correctly perform stop & analyse action
        # ThreadLock(Lock in asyncio) can't be pickled, so using
        # ProcessLock(Lock in multiprocessing) instead of ThreadLock
        self.__lock = ProcessLock()
        # all workers use the same queue lock to get content from queue
        self.__queue_lock = queue_lock
        # all workers user the same queue to communicate with manager
        self.__queue = queue
        self.__weight: int = weight
        super().__init__(uid(__class__.__name__), self.__job_manager)

    @property
    def lock(self):
        return self.__lock

    @property
    def queue_lock(self):
        return self.__queue_lock

    @property
    def queue(self):
        return self.__queue

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
        # all workers communicate safely by this lock
        self.__queue_lock = ProcessLock()
        # all workers communicate through this queue
        self.__queue = Queue()
        if worker_num is None:
            self.__worker_num = cpu_count()
        else:
            self.__worker_num: int = min(max(worker_num, 1), cpu_count() * 2)
        [self.add(Worker(queue_lock=self.__queue_lock, queue=self.__queue)) for _ in range(self.__worker_num)]

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

    def stop(self):
        # send stop signals
        with self.__queue_lock:
            for i in range(self.__worker_num):
                self.__queue.put(('stop', None))
        # gather results
        time.sleep(15)
        results = []
        for i in range(self.__worker_num):
            results.append(self.__queue.get())
        print(results)
