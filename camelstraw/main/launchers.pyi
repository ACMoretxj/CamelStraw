from abc import ABCMeta, abstractmethod
from typing import List

from ..net import HttpMethod


class Launcher(metaclass=ABCMeta):
    @abstractmethod
    def launch(self, *args, **kwargs) -> None: pass

class CmdLauncher(Launcher):
    def __init__(self, worker_num: int, duration: int, method: HttpMethod, urls: List[str]): pass
    def launch(self, *args, **kwargs) -> None: pass

class WebLauncher(Launcher):
    def __init__(self, host: str, port: str): pass
    def launch(self, *args, **kwargs) -> None: pass

class ApiLauncher(Launcher):
    def __init__(self): pass
    def launch(self, *args, **kwargs) -> None: pass
