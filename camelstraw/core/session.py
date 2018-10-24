from .interfaces import IAnalysable, IManager
from ..util import uid
from ..net import Protocol


class Session(IAnalysable):
    """
    每一次请求的记录
    """
    def __init__(self, _protocol: Protocol, _url: str):
        super().__init__(uid(__class__.__name__))
        self.__protocol: Protocol = _protocol
        self.__url: str = _url
        self.__status_code: int = 200

    @property
    def protocol(self) -> Protocol:
        return self.__protocol

    @property
    def url(self) -> str:
        return self.__url

    @property
    def status_code(self) -> int:
        return self.__status_code

    def stop(self, _status_code: int=200):
        super().stop()
        self.__status_code = _status_code

    def analyse(self):
        super().analyse()
        self._total_request = 1
        self._success_request = 1 if self.status == 200 else 0


class SessionManager(IManager):
    """
    请求管理器，维护一个请求列表
    """
    def __init__(self):
        super().__init__(uid(__class__.__name__))
        # 临时保存的session对象，SessionManager的一次打开和关闭是一个完整的生命周期
        self.session: Session = None

    def open(self, protocol: Protocol, url: str) -> Session:
        """
        打开一个Session
        :return:
        """
        self.session = Session(_protocol=protocol, _url=url)
        self.session.start()
        return self.session

    def close(self, status_code: int=200) -> None:
        self.session.stop(_status_code=status_code)
        self._container.append(self.session)
        self.session = None
