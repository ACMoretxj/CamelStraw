from enum import IntEnum
from typing import Dict, TypeVar, List, Iterable

from ..util import Stopwatch

AnalyseResultType = TypeVar('AnalyseResultType', str, Dict)

class CoreStatus(IntEnum):
    def __new__(cls, value: str, phrase: str, description: str=''): pass

class AnalyseResult:
    id: int
    total_request: int
    success_request: int
    latency: int
    qps: int
    start_time: int
    stop_time: int

    json_result: str

    def __init__(self, _id: str, total_request: int, success_request: int, latency: int, qps: int, start_time: int, stop_time: int): pass
    def __repr__(self) -> str: pass

    @classmethod
    def from_json(cls, data: AnalyseResultType) -> AnalyseResult: pass
    @classmethod
    def from_results(cls, _id: str, results: List) -> AnalyseResult: pass

class IAnalysable:
    # fields
    _manager: IManager
    _status: CoreStatus
    _stopwatch: Stopwatch
    _total_request: int
    _success_request: int
    _latency: int
    _analyse_result: AnalyseResult

    total_request: int
    success_request: int
    latency: int

    id: str
    qps: int
    start_time: int
    stop_time: int
    status: CoreStatus
    result: AnalyseResult

    def __init__(self, _id: str, _manager=None): pass
    def __repr__(self) -> str: pass

    def start(self, *args, **kwargs): pass
    def stop(self, *args, **kwargs): pass
    def analyse(self) -> None: pass

class IManager:
    id: str
    _container: List[IAnalysable]

    def __init__(self, _id: str): pass
    def __iter__(self) -> Iterable: pass

    def add(self, obj: IAnalysable) -> None: pass
