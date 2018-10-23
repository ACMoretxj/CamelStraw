from http import HTTPStatus
from typing import List

from camelstraw.util import Stopwatch, IAnalysable, uid


class Session:
    """
    每一次请求的记录
    """
    def __init__(self, _url: str):
        self.__url: str = _url
        self.__status: HTTPStatus = 0
        self.__latency: int = 0
        self.stopwatch: Stopwatch = Stopwatch()

    @property
    def url(self) -> str:
        return self.__url

    @property
    def status(self) -> HTTPStatus:
        return self.__status

    @property
    def latency(self) -> int:
        return self.__latency

    def close(self, _status: HTTPStatus=HTTPStatus.OK) -> None:
        self.__status = _status
        self.__latency = self.stopwatch.elapsed_time


class SessionManager(IAnalysable):
    """
    请求管理器，维护一个请求列表
    """

    def __init__(self):
        super().__init__(uid(__class__.__name__))
        self.__sessions: List = []
        self.__stopwatch: Stopwatch = Stopwatch().start()

    def add(self, session: Session) -> None:
        self.__sessions.append(session)
        self._total_request += 1
        self._success_request += 1 if session.status == HTTPStatus.OK else 0

    def analyse(self) -> None:
        self._latency = self.__stopwatch.elapsed_time
