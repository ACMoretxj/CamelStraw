from abc import ABCMeta, abstractmethod
from typing import List

from ..core import JobContainer
from ..net import HttpMethod


class Launcher(metaclass=ABCMeta):
    @abstractmethod
    def launch(self, *args, **kwargs) -> None: pass

class CmdLauncher(Launcher):
    duration: int
    worker_num: int
    method: HttpMethod
    urls: List[str]
    def __init__(self, worker_num: int, duration: int, method: HttpMethod, urls: List[str]): pass
    def launch(self, *args, **kwargs) -> None: pass

class WebLauncher(Launcher):
    def __init__(self, host: str, port: str): pass
    def launch(self, *args, **kwargs) -> None: pass

class ApiLauncher(Launcher):
    __jobs: List[JobContainer]
    jobs: List[JobContainer]
    duration: int
    worker_num: int
    def __init__(self, jobs: List[JobContainer], duration: int, worker_num: int=None): pass
    def dispatch(self, job: JobContainer) -> None: pass
    def launch(self, *args, **kwargs) -> None: pass
