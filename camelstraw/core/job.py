import asyncio
from typing import Callable, Dict, List, TypeVar

from aiohttp import ClientSession as Client, ClientResponseError, ClientError
from aiohttp import WSMsgType
from aiohttp.http_exceptions import HttpProcessingError

from .session import SessionManager
from .interfaces import IAnalysable, IManager, CoreStatus
from ..util import uid
from ..net import Protocol, HttpMethod
WSMsgTypeHint = TypeVar('WSMsgTypeHint', str, bytes)


class Job(IAnalysable):
    """
    测试任务，是执行测试行为的单位
    """
    def __init__(self, url: str, **kwargs):
        self.__session_manager: SessionManager = SessionManager()
        self.__protocol: Protocol = Protocol.from_url(url)
        self.__url = url
        self.__job_kwargs = kwargs
        super().__init__(uid(__class__.__name__), self.__session_manager)

    async def start(self) -> asyncio.coroutine:
        super().start()
        callback = getattr(self.__job_kwargs, 'callback', None)
        if self.__protocol == Protocol.HTTP or self.__protocol == Protocol.HTTPS:
            method = getattr(self.__job_kwargs, 'method', HttpMethod.GET)
            data = getattr(self.__job_kwargs, 'data', {})
            return await self.do_http(self.__url, method, data, callback)
        elif self.__protocol == Protocol.WS or self.__protocol == Protocol.WSS:
            message_type = getattr(self.__job_kwargs, 'message_type', WSMsgType.TEXT)
            data = getattr(self.__job_kwargs, 'data', 'ping')
            return await self.do_websocket(self.__url, message_type, data, callback)

    async def do_http(self, url: str, method: HttpMethod, data: Dict=None, callback: Callable=None):
        async with Client() as client:
            while self.status == CoreStatus.STARTED:
                self.__session_manager.open(self.__protocol, url)
                try:
                    response = None
                    if method == HttpMethod.GET:
                        response = await client.get(url, params=data or {})
                    elif method == HttpMethod.POST:
                        response = await client.post(url, json=data or {})
                    # 记录结果，调用回调函数
                    content = await response.text() if response else 'empty message'
                    self.__session_manager.close(response.status)
                    if isinstance(callback, Callable):
                        callback(response=content)
                except (HttpProcessingError, ClientError):
                    self.__session_manager.close(400)

    async def do_websocket(self, url: str, message_type: WSMsgType, data: WSMsgTypeHint=None, callback: Callable=None):
        async with Client().ws_connect(url) as ws:
            while self.status == CoreStatus.STARTED:
                async for msg in ws:
                    self.__session_manager.open(self.__protocol, url)
                    try:
                        if msg.type == WSMsgType.TEXT:
                            if message_type == WSMsgType.TEXT:
                                await ws.send_str(data)
                            elif message_type == WSMsgType.BINARY:
                                await ws.send_bytes(data)
                            # 记录结果，调用回调函数
                            self.__session_manager.close(200)
                            if isinstance(callback, Callable):
                                callback(response=msg.data)
                        elif msg.type == WSMsgType.ERROR:
                            self.__session_manager.close(500)
                            await ws.close()
                    except (HttpProcessingError, ClientError):
                        self.__session_manager.close(400)


class HttpGetJob(Job):
    def __init__(self, url: str,  data: Dict=None, callback: Callable=None):
        super().__init__(url=url, data=data, method=HttpMethod.GET, callback=callback)


class HttpPostJob(Job):
    def __init__(self, url: str, data: Dict=None, callback: Callable=None):
        super().__init__(url=url, data=data, method=HttpMethod.POST, callback=callback)


class WebsocketTextJob(Job):
    def __init__(self, url: str, data: str=None, callback: Callable=None):
        super().__init__(url=url, data=data, message_type=WSMsgType.TEXT, callback=callback)


class WebsocketBinaryJob(Job):
    def __init__(self, url: str, data: bytes=None, callback: Callable=None):
        super().__init__(url=url, data=data, message_type=WSMsgType.BINARY, callback=callback)


class JobManager(IManager):
    """
    任务管理器，维护一个任务列表
    """
    def __init__(self):
        super().__init__(uid(__class__.__name__))
