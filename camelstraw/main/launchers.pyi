from abc import ABCMeta, abstractmethod
from typing import List

from ..core import JobContainer, Master, Slave
from ..net import HttpMethod


class BaseLauncher(metaclass=ABCMeta):
    @abstractmethod
    def launch(self, *args, **kwargs) -> None: pass
    @staticmethod
    def launch_master(*jobs: JobContainer, worker_num: int=None) -> Master: pass
    @staticmethod
    def launch_slaves(local_mode: bool=True) -> List[Slave]: pass

class CmdLauncher(BaseLauncher):
    duration: int
    worker_num: int
    method: HttpMethod
    urls: List[str]
    def __init__(self, worker_num: int, duration: int, method: HttpMethod, urls: List[str]): pass
    def launch(self, local_mode: bool=True) -> None: pass

class WebLauncher(BaseLauncher):
    def __init__(self, host: str, port: str): pass
    def launch(self, *args, **kwargs) -> None: pass

class ApiLauncher(BaseLauncher):
    __jobs: List[JobContainer]
    jobs: List[JobContainer]
    duration: int
    worker_num: int
    def __init__(self, jobs: List[JobContainer], duration: int, worker_num: int=None): pass
    def dispatch(self, job: JobContainer) -> None: pass
    def launch(self, local_mode: bool=True) -> None: pass
