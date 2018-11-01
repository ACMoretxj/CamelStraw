import asyncio
from multiprocessing import Queue, Lock, cpu_count
from typing import List, TypeVar, Iterable

from .job import Job, JobManager, JobContainer
from .interfaces import IAnalysable, IManager, AnalyseResult
from ..task import IDispatchable, IBalancer
JobType = TypeVar('JobType', Job, JobContainer)


def __try_stop_and_analyse(worker: Worker) -> None: pass
async def __work_timeout(worker: Worker, timeout: int) -> asyncio.coroutine: pass
async def __work_notice(worker: Worker) -> asyncio.coroutine: pass
async def __stop_work(worker: Worker, timeout: int) -> asyncio.Future: pass
def start_work(worker_bytes: bytes, timeout: int) -> None: pass


# noinspection PyMissingConstructor
class Worker(IAnalysable, IDispatchable):
    __job_manager: JobManager
    __lock: Lock
    # all workers user the same queue to communicate with manager
    __queue: Queue
    __weight: int

    lock: Lock
    queue: Queue
    jobs: Iterable[Job]
    job_num: int
    
    def __init__(self, queue: Queue, weight: int=1): pass

    def start(self) -> None: pass
    def dispatch(self, job: Job) -> None: pass
    def weight(self) -> int: pass


# noinspection PyMissingConstructor
class WorkerManager(IManager):
    __balancer: IBalancer
    __worker_num: int
    __queue: Queue
    __result: AnalyseResult

    worker_num: int
    result: AnalyseResult
    
    def __init__(self, worker_num: int=cpu_count()): pass
    def __iter__(self) -> Iterable[Worker]: pass

    def dispatch(self, job: JobContainer, worker: Worker=None) -> None: pass
    def start(self) -> None: pass
    def stop(self) -> None: pass
