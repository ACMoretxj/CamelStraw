import asyncio
import multiprocessing
import sys
from multiprocessing import Process, cpu_count, Queue, Manager as ProcessManager
from queue import Empty
from threading import Lock as ThreadLock
from typing import List

import dill

from ..settings import WORKER_TIMEOUT, WORKER_CHECK_INTERVAL
from ..exception import WrongStatusException, WorkerExecuteException
from .job import JobManager, Job, JobContainer
from .interfaces import IAnalysable, IManager, CoreStatus, AnalyseResult
from ..task import RoundRobin, IDispatchable
from ..util import uid, singleton, readonly


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
            worker.queue.put(('result', worker.result.json_result))
        except WrongStatusException:
            pass


async def __work_timeout(worker, timeout=None):
    """
    worker's stop trigger for timeout mechanism
    :param worker:
    :param timeout: seconds
    :return:
    """
    if timeout is None:
        timeout = WORKER_TIMEOUT
    if timeout <= 0:
        timeout = sys.maxsize
    timeout = int(timeout)
    while timeout > 0 and worker.status == CoreStatus.STARTED:
        # take a nap and check the worker status
        await asyncio.sleep(1)
        timeout -= 1
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


async def __stop_work(worker, timeout=None):
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


def start_work(worker_bytes, timeout=None):
    """
    :param worker_bytes
    :param timeout:
    :return:
    """
    if multiprocessing.current_process().name == 'MainProcess':
        raise WorkerExecuteException('worker can only run at child process')
    worker: Worker = dill.loads(worker_bytes)
    tasks = [job.start() for job in worker.jobs]
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
    def __new__(cls, *args, **kwargs):
        # TODO: unknown dill problem.
        # the following code seems duplicate to that in __init__,
        # but it's a must when used in Process & dill
        worker = super().__new__(cls)
        readonly(worker, 'lock', lambda: None)
        readonly(worker, 'queue', lambda: None)
        readonly(worker, 'jobs', lambda: None)
        readonly(worker, 'job_num', lambda: None)
        return worker

    def __init__(self, queue, weight=1):
        self.__job_manager = JobManager()
        super().__init__(uid(__class__.__name__), self.__job_manager)
        # the worker itself has an another lock for correctly perform stop & analyse action
        self.__lock = ThreadLock()
        # all workers user the same queue to communicate with manager
        self.__queue = queue
        self.__weight = weight
        # properties
        readonly(self, 'lock', lambda: self.__lock)
        readonly(self, 'queue', lambda: self.__queue)
        readonly(self, 'jobs', lambda: (job for job in self.__job_manager))
        readonly(self, 'job_num', lambda: len(list(self.__job_manager)))

    def start(self):
        # not dispatched jobs, just return
        if self.job_num <= 0:
            return
        super().start()
        process = Process(target=start_work, args=(dill.dumps(self, recurse=True),))
        process.start()

    def dispatch(self, job):
        if not isinstance(job, Job):
            raise TypeError('Worker.dispatch only accept Job type')
        if self.status != CoreStatus.INIT:
            raise WrongStatusException('Worker can only be dispatched job at init status')
        self.__job_manager.add(job)

    def weight(self):
        return self.__weight


@singleton
class WorkerManager(IManager):
    """
    initialize workers and dispatch jobs for them
    """
    def __init__(self, worker_num=cpu_count()):
        super().__init__(uid(__class__.__name__))
        self.__balancer = RoundRobin()
        self.__worker_num = min(max(worker_num, 1), cpu_count() * 2)
        # all workers communicate through this queue
        self.__queue = ProcessManager().Queue(maxsize=self.__worker_num * 2)
        self.__result = None
        [self.add(Worker(queue=self.__queue)) for _ in range(self.__worker_num)]
        # properties
        readonly(self, 'worker_num', lambda: self.__worker_num)
        readonly(self, 'result', lambda: self.__result)

    def dispatch(self, job, worker=None):
        if worker is None:
            worker = self.__balancer.choose(self._container)
        if job.reuse_job:
            [worker.dispatch(job.job()) for worker in self]
        else:
            worker.dispatch(job.job())

    def start(self):
        # eliminate workers without any job and update associate field
        self._container = [worker for worker in self if worker.job_num > 0]
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
                tmp_results.append(AnalyseResult.from_json(message[1]))
            # put other messages back
            else:
                self.__queue.put(message)
        # generate self result
        self.__result = AnalyseResult.from_results(self.id, tmp_results)
