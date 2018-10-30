from .interfaces import IAnalysable, IManager
from ..net import Protocol


# noinspection PyMissingConstructor
class Session(IAnalysable):
    protocol: Protocol
    url: str
    status_code: int

    def __init__(self, _protocol: Protocol, _url: str): pass

    def stop(self, _status_code: int=200) -> None: pass
    def analyse(self) -> None: pass


# noinspection PyMissingConstructor
class SessionManager(IManager):
    __session: Session

    def __init__(self): pass

    def open(self, protocol: Protocol, url: str) -> Session: pass
    def close(self, status_code: int=200) -> None: pass
