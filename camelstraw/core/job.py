import asyncio
from abc import ABCMeta, abstractmethod
from itertools import cycle, repeat
from typing import Callable, Generator, Iterator

from aiohttp import ClientSession as Client, ClientError, WSMessage
from aiohttp import WSMsgType
from aiohttp.http_exceptions import HttpProcessingError

from camelstraw.util import readonly
from .session import SessionManager
from .interfaces import IAnalysable, IManager, CoreStatus
from ..util import uid
from ..net import Protocol, HttpMethod


class Job(IAnalysable):
    """
    execution unit
    """
    def __init__(self, url: str, **kwargs):
        self.__session_manager = SessionManager()
        super().__init__(uid(__class__.__name__), self.__session_manager)
        self.__protocol = Protocol.from_url(url)
        self.__url = url
        self.__job_kwargs = kwargs

    async def start(self) -> asyncio.coroutine:
        super().start()
        data = self.__data_iterator(self.__job_kwargs.get('data', None))
        headers = self.__job_kwargs.get('headers', None)
        cookies = self.__job_kwargs.get('cookies', {})
        callback = self.__job_kwargs.get('callback', None)
        await self.__do_request(data=data, headers=headers, cookies=cookies, callback=callback)

    @staticmethod
    def __data_iterator(data):
        """
        transform all types to generator
        :param data:
        :return:
        """
        if isinstance(data, Generator) or isinstance(data, Iterator):
            return cycle(data)
        elif isinstance(data, Callable):
            return repeat(data())
        else:
            return repeat(data or {})

    async def __do_request(self, data, headers=None, cookies=None, callback=None):
        if self.__protocol == Protocol.HTTP or self.__protocol == Protocol.HTTPS:
            method = self.__job_kwargs.get('method', HttpMethod.GET)
            async with Client(headers=headers, cookies=cookies) as client:
                await self.__do_http_request(client, method, data, callback)
        elif self.__protocol == Protocol.WS or self.__protocol == Protocol.WSS:
            message_type = self.__job_kwargs.get('message_type', WSMsgType.TEXT)
            async with Client(headers=headers, cookies=cookies).ws_connect(self.__url) as ws:
                await self.__do_websocket_request(ws, message_type, data, callback)

    async def __do_http_request(self, client, method, data, callback=None):
        while self.status == CoreStatus.STARTED:
            self.__session_manager.open(self.__protocol, self.__url)
            try:
                response = None
                if method == HttpMethod.GET:
                    response = await client.get(self.__url, params=next(data))
                elif method == HttpMethod.POST:
                    response = await client.post(self.__url, json=next(data))
                # record result and call callback
                content = await response.text() if response else 'empty message'
                self.__session_manager.close(response.status)
                if isinstance(callback, Callable):
                    callback(status_code=response.status, content=content)
            except (HttpProcessingError, ClientError):
                self.__session_manager.close(400)

    async def __do_websocket_request(self, ws, message_type, data, callback=None):
        while self.status == CoreStatus.STARTED:
            self.__session_manager.open(self.__protocol, self.__url)
            try:
                if message_type == WSMsgType.TEXT:
                    await ws.send_str(next(data))
                elif message_type == WSMsgType.BINARY:
                    await ws.send_bytes(next(data))
                # record result and call callback
                msg: WSMessage = await ws.receive()
                if msg.type == WSMsgType.TEXT:
                    self.__session_manager.close(200)
                    if isinstance(callback, Callable):
                        callback(status_code=200, content=msg.data)
                else:
                    self.__session_manager.close(500)
            except (HttpProcessingError, ClientError):
                self.__session_manager.close(400)


class JobContainer(metaclass=ABCMeta):
    """
    transform from arguments to Job instance, expose this instead of Job because
    multi-processing environment is error prone
    """
    def __init__(self, url, data=None, headers=None, cookies=None, callback=None, reuse_job=True):
        self._job = None
        self._url = url
        self._data = data
        self._headers = headers
        self._cookies = cookies
        self._callback = callback
        # properties
        readonly(self, 'reuse_job', lambda: reuse_job)

    @abstractmethod
    def job(self):
        pass


class HttpGetJob(JobContainer):

    def __new__(cls, *args, **kwargs):
        # TODO: unknown dill problem.
        # the following code seems duplicate to that in __init__,
        # but it's a must when used in Process & dill
        inst = super().__new__(cls)
        readonly(inst, 'reuse_job', lambda: None)
        return inst

    def job(self):
        if self._job is None or self.reuse_job:
            self._job = Job(url=self._url, data=self._data, headers=self._headers, cookies=self._cookies,
                            method=HttpMethod.GET, callback=self._callback)
        return self._job


class HttpPostJob(JobContainer):

    def __new__(cls, *args, **kwargs):
        # TODO: unknown dill problem.
        # the following code seems duplicate to that in __init__,
        # but it's a must when used in Process & dill
        inst = super().__new__(cls)
        readonly(inst, 'reuse_job', lambda: None)
        return inst

    def job(self):
        if self._job is None or self.reuse_job:
            self._job = Job(url=self._url, data=self._data, headers=self._headers, cookies=self._cookies,
                            method=HttpMethod.POST, callback=self._callback)
        return self._job


class WebsocketTextJob(JobContainer):

    def __new__(cls, *args, **kwargs):
        # TODO: unknown dill problem.
        # the following code seems duplicate to that in __init__,
        # but it's a must when used in Process & dill
        inst = super().__new__(cls)
        readonly(inst, 'reuse_job', lambda: None)
        return inst

    def job(self):
        if self._job is None or self.reuse_job:
            self._job = Job(url=self._url, data=self._data, headers=self._headers, cookies=self._cookies,
                            message_type=WSMsgType.TEXT, callback=self._callback)
        return self._job


class WebsocketBinaryJob(JobContainer):

    def __new__(cls, *args, **kwargs):
        # TODO: unknown dill problem.
        # the following code seems duplicate to that in __init__,
        # but it's a must when used in Process & dill
        inst = super().__new__(cls)
        readonly(inst, 'reuse_job', lambda: None)
        return inst

    def job(self):
        if self._job is None or self.reuse_job:
            self._job = Job(url=self._url, data=self._data, headers=self._headers, cookies=self._cookies
                            , message_type=WSMsgType.BINARY, callback=self._callback)
        return self._job


class JobManager(IManager):
    """
    maintain a job list
    """
    def __init__(self):
        super().__init__(uid(__class__.__name__))
