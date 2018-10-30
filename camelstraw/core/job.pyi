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
    __protocol: Protocol
    __url: str
    __job_kwargs: Dict
    
    def __init__(self, url: str, **kwargs): pass
    
    async def start(self) -> asyncio.coroutine: pass
    async def __do_request(self, data: Iterator, headers: Dict=None, cookies: Dict=None, callback: Callable=None) -> asyncio.coroutine: pass
    async def __do_http_request(self, client: Client, method: HttpMethod, data: Iterator, callback: Callable=None) -> asyncio.coroutine: pass
    async def __do_websocket_request(self, ws: ClientWebSocketResponse, message_type: WSMsgType, data: Iterator, callback: Callable=None) -> asyncio.coroutine: pass
    
    @staticmethod
    def __data_iterator(data: DataType) -> Iterator: pass

class JobContainer(metaclass=ABCMeta):
    _url: str
    _data: DataType
    _headers: Dict
    _cookies: Dict
    _callback: Callable
    _job = Job

    def __init__(self, url: str, data: DataType=None, headers: Dict=None, cookies: Dict=None, callback: Callable=None): pass

    @abstractmethod
    def job(self) -> Job: pass

class HttpGetJob(JobContainer):
    def job(self) -> Job: pass

class HttpPostJob(JobContainer):
    def job(self) -> Job: pass

class WebsocketTextJob(JobContainer):
    def job(self) -> Job: pass

class WebsocketBinaryJob(JobContainer):
    def job(self) -> Job: pass


# noinspection PyMissingConstructor
class JobManager(IManager):
    def __init__(self): pass
