import asyncio
from typing import Dict, List

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request

from .interfaces import AnalyseResult
from .job import JobContainer
from ..settings import MASTER_PORT

class MasterService:
    __service: Application
    __slaves: Dict[str, web.WebSocketResponse]
    __results: Dict[str, AnalyseResult]
    __jobs: List[JobContainer]

    host: str
    port: int
    result: AnalyseResult

    def __init__(self, host: str='0.0.0.0', port: int=MASTER_PORT): pass

    def dispatch(self, *jobs: JobContainer) -> None: pass
    def start(self) -> None: pass
    def stop(self) -> None: pass
    async def __init_slave(self, slave: str, jobs: List[JobContainer]) -> asyncio.coroutine: pass
    def __init_slaves(self) -> None: pass
    def __gather_result(self) -> None: pass
    async def __handler(self, request: Request) -> asyncio.coroutine: pass
    async def __stop_slave(self, slave: str) -> asyncio.coroutine: pass

class Master:
    pass
