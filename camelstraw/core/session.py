from http import HTTPStatus

from camelstraw.core.interfaces import IAnalysable, IManager
from camelstraw.util import uid


class Session(IAnalysable):
    """
    每一次请求的记录
    """
    def __init__(self, _url: str):
        super().__init__(uid(__class__.__name__))
        self.__url: str = _url
        self.__status: HTTPStatus = None

    @property
    def url(self) -> str:
        return self.__url

    @property
    def status(self) -> HTTPStatus:
        return self.__status

    def stop(self, _status: HTTPStatus=HTTPStatus.OK):
        super().stop()
        self.__status = _status

    def analyse(self):
        self._total_request = 1
        self._success_request = 1 if self.status == HTTPStatus.OK else 0


class SessionManager(IManager):
    """
    请求管理器，维护一个请求列表
    """
    def __init__(self):
        super().__init__(uid(__class__.__name__))
