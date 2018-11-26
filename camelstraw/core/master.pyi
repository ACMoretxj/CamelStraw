import asyncio
from multiprocessing import Process
from typing import Dict, List

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request

from .interfaces import AnalyseResult
from .job import JobContainer
from ..settings import MASTER_PORT

class MasterService:
    __app: Application
    __master: web.WebSocketResponse
    __slaves: Dict[str, web.WebSocketResponse]
    __results: Dict[str, AnalyseResult]

    jobs: List[JobContainer]
    worker_num: int
    host: str
    port: int
    result: AnalyseResult

    def __init__(self, jobs: List[JobContainer], worker_num: int=None, host: str='0.0.0.0', port: int=MASTER_PORT): pass

    def start(self) -> None: pass
    async def __init_slave(self, slave: str, jobs: List[JobContainer], worker_num: int) -> asyncio.coroutine: pass
    def __init_slaves(self) -> None: pass
    async def __stop_slave(self, slave: str) -> asyncio.coroutine: pass
    def __stop_slaves(self) -> None: pass
    async def __gather_result(self) -> None: pass
    async def __slave_handler(self, request: Request) -> asyncio.coroutine: pass
    async def __master_handler(self, request: Request) -> asyncio.coroutine: pass

def start_service(jobs_bytes: bytes, worker_num: int) -> None: pass

class Master:
    __process: Process
    __jobs: List[JobContainer]
    __result: AnalyseResult

    jobs: List[JobContainer]
    result: AnalyseResult
    worker_num: int

    def __init__(self, *jobs: JobContainer, worker_num: int=None): pass

    def start(self, local_mode: bool=True) -> None: pass
    def stop(self) -> None: pass
    async def __stop(self) -> asyncio.coroutine: pass
