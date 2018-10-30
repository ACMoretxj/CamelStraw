import asyncio

from aiohttp import ClientSession as Client, WSMsgType

from .interfaces import AnalyseResult
from .worker import WorkerManager
from ..util import uid

class Slave:
    __worker_manager: WorkerManager

    id: str
    result: AnalyseResult

    def __init__(self, _id=uid('Slave')): pass

    def start(self) -> None: pass
    async def __handler(self) -> asyncio.coroutine: pass
