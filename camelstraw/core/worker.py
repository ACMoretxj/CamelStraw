import asyncio
import multiprocessing
import sys
from multiprocessing import Process, cpu_count, Lock as ProcessLock, Queue
from queue import Empty
from typing import TypeVar, List

from ..settings import WORKER_TIMEOUT, WORKER_CHECK_INTERVAL
from ..exception import WrongStatusException, WorkerExecuteException
from .job import JobManager, Job, JobContainer
from .interfaces import IAnalysable, IManager, CoreStatus, AnalyseResult
from ..task import RoundRobin, IDispatchable
from ..util import uid, singleton
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
            worker.queue.put(('result', worker.result))
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


async def __work_notice(worker):
    """
    worker's stop trigger for message queue mechanism
    :param worker:
    :return:
    """
    interval = max(1, int(WORKER_CHECK_INTERVAL))
    while worker.status == CoreStatus.STARTED:
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
        __work_notice(worker),
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
    def __init__(self, queue: Queue, weight=1):
        self.__job_manager: JobManager = JobManager()
        # the worker itself has an another lock for correctly perform stop & analyse action
        # ThreadLock(Lock in asyncio) can't be pickled, so using
        # ProcessLock(Lock in multiprocessing) instead of ThreadLock
        self.__lock = ProcessLock()
        # all workers user the same queue to communicate with manager
        self.__queue = queue
        self.__weight: int = weight
        super().__init__(uid(__class__.__name__), self.__job_manager)

    @property
    def lock(self):
        return self.__lock

    @property
    def queue(self):
        return self.__queue

    @property
    def job_num(self):
        return len(list(self.__job_manager))

    def start(self) -> None:
        # not dispatched jobs, just return
        if self.job_num <= 0:
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


@singleton
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
        # all workers communicate through this queue
        self.__queue = Queue(maxsize=self.worker_num * 2)
        # test result
        self.__result: AnalyseResult = None
        # add workers
        [self.add(Worker(queue=self.__queue)) for _ in range(self.worker_num)]

    @property
    def worker_num(self):
        return self.__worker_num

    @property
    def result(self) -> AnalyseResult:
        return self.__result

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
        # eliminate workers without any job and update associate field
        self._container = [worker for worker in self._container if worker.job_num > 0]
        self.__worker_num = len(self._container)
        # start all workers
        [worker.start() for worker in self._container]

    def stop(self):
        # send stop signals
        for i in range(self.__worker_num):
            self.__queue.put(('stop', None))
        # gather results
        tmp_results: List[AnalyseResult] = []
        while len(tmp_results) < self.worker_num:
            message = self.__queue.get()
            # gather result message
            if message[0] == 'result':
                tmp_results.append(message[1])
            # put other messages back
            else:
                self.__queue.put(message)
        # generate self result
        start_time = min(tr.start_time for tr in tmp_results)
        stop_time = max(tr.stop_time for tr in tmp_results)
        latency = stop_time - start_time
        total_request = sum(tr.total_request for tr in tmp_results)
        success_result = sum(tr.success_request for tr in tmp_results)
        qps = total_request * 1000 // max(1, latency)
        self.__result = AnalyseResult(id=self._id, total_request=total_request, success_request=success_result,
                                      latency=latency, qps=qps, start_time=start_time, stop_time=stop_time)
