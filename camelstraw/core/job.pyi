import asyncio
from abc import ABCMeta, abstractmethod
from typing import Dict, TypeVar, Callable, Generator, Iterator

from aiohttp import ClientSession as Client, ClientWebSocketResponse, WSMsgType

from .session import SessionManager
from ..net import Protocol, HttpMethod
from .interfaces import IAnalysable, IManager

DataType = TypeVar('DataType', Dict, str, bytes, Callable, Generator, Iterator)

# noinspection PyMissingConstructor
class Job(IAnalysable):
    __session_manager: SessionManager
    __job_kwargs: Dict

    protocol: Protocol
    url: str

    def __new__(cls, *args, **kwargs): pass
    def __init__(self, url: str, **kwargs): pass
    
    async def start(self) -> asyncio.coroutine: pass
    async def __do_request(self, data: Iterator, headers: Dict=None, cookies: Dict=None, callback: Callable=None) -> asyncio.coroutine: pass
    async def __do_http_request(self, client: Client, method: HttpMethod, data: Iterator, callback: Callable=None) -> asyncio.coroutine: pass
    async def __do_websocket_request(self, ws: ClientWebSocketResponse, message_type: WSMsgType, data: Iterator, callback: Callable=None) -> asyncio.coroutine: pass
    
    @staticmethod
    def __data_iterator(data: DataType) -> Iterator: pass

class JobContainer(metaclass=ABCMeta):
    _job: Job
    _url: str
    _data: DataType
    _headers: Dict
    _cookies: Dict
    _callback: Callable

    reuse_job: bool

    def __init__(self, url: str, data: DataType=None, headers: Dict=None, cookies: Dict=None, callback: Callable=None, reuse_job=True): pass

    @abstractmethod
    def job(self) -> Job: pass

class HttpGetJob(JobContainer):
    def __new__(cls, *args, **kwargs) -> JobContainer: pass
    def job(self) -> Job: pass

class HttpPostJob(JobContainer):
    def __new__(cls, *args, **kwargs) -> JobContainer: pass
    def job(self) -> Job: pass

class WebsocketTextJob(JobContainer):
    def __new__(cls, *args, **kwargs) -> JobContainer: pass
    def job(self) -> Job: pass

class WebsocketBinaryJob(JobContainer):
    def __new__(cls, *args, **kwargs) -> JobContainer: pass
    def job(self) -> Job: pass


# noinspection PyMissingConstructor
class JobManager(IManager):
    def __init__(self): pass
