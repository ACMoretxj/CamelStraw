from abc import ABCMeta
from collections import Iterable
from enum import IntEnum
from typing import List

from ..exception import WrongStatusException
from ..util import Stopwatch


class CoreStatus(IntEnum):

    def __new__(cls, value: int, phrase: str, description: str=''):
        # noinspection PyArgumentList
        obj: int = int.__new__(cls, value)
        obj._value_ = value

        obj.phrase = phrase
        obj.description = description
        return obj

    INIT = 100, 'CoreStatusInit'
    STARTED = 101, 'CoreStatusStarted'
    STOPPED = 103, 'CoreStatusStopped'
    ANALYSED = 104, 'CoreStatusAnalysed'


class IAnalysable(metaclass=ABCMeta):
    """
    generic interface for all analysable objects including
    Session/Job/Worker etc, for the convenience of computing
    and visualization
    """
    def __init__(self, _id: str, _manager=None):
        self._id: str = _id
        self._manager: IManager = _manager
        self._total_request: int = 0
        self._success_request: int = 0
        self._latency: int = 0
        self._stopwatch: Stopwatch = Stopwatch()
        self._status: CoreStatus = CoreStatus.INIT

    @property
    def id(self) -> str:
        return self._id

    @property
    def total_request(self) -> int:
        if self.status != CoreStatus.ANALYSED:
            raise WrongStatusException('_total_request is not computed')
        return self._total_request

    @property
    def success_request(self):
        if self.status != CoreStatus.ANALYSED:
            raise WrongStatusException('_success_request is not computed')
        return self._success_request

    @property
    def latency(self):
        if self.status != CoreStatus.ANALYSED:
            raise WrongStatusException('_latency is not computed')
        return self._latency

    @property
    def qps(self) -> int:
        return self.total_request * 1000 // max(1, self.latency)

    @property
    def status(self) -> CoreStatus:
        return self._status

    def start(self, *args, **kwargs):
        if self.status != CoreStatus.INIT:
            raise WrongStatusException('IAnalysable<%s with %s> can only be started at init status'
                                       % (self.__class__.__name__, self.status))
        self._status = CoreStatus.STARTED
        self._stopwatch.start()

    def stop(self, *args, **kwargs):
        if self.status != CoreStatus.STARTED:
            raise WrongStatusException('IAnalysable<%s with %s> can only be stopped at started status'
                                       % (self.__class__.__name__, self.status))
        self._status = CoreStatus.STOPPED
        self._latency = self._stopwatch.elapsed_time
        if self._manager is not None:
            for item in self._manager:
                if item.status != CoreStatus.STOPPED:
                    item.stop()

    def analyse(self):
        if self.status != CoreStatus.STOPPED:
            raise WrongStatusException('IAnalysable<%s with %s> can only be analysed at stopped status'
                                       % (self.__class__.__name__, self.status))
        self._status = CoreStatus.ANALYSED
        if self._manager is not None:
            for item in self._manager:
                item.analyse()
                self._total_request += item.total_request
                self._success_request += item.success_request

    def __repr__(self):
        reprs = [
            '=' * 128,
            'Id: %s' % self.id,
            'Request: %s/%s' % (self.success_request, self.total_request),
            'Latency: %s ms' % self.latency,
            'QPS: %s' % self.qps,
            '=' * 128]
        return '\n'.join(reprs)


class IManager(metaclass=ABCMeta):
    """
    generic interface for all manager objects including
    SessionManager/JobManager/WorkerManager etc, collecting
    common logic for all managers
    """
    def __init__(self, _id: str):
        self._id = _id
        self._container: List = []

    def add(self, obj: IAnalysable) -> None:
        self._container.append(obj)

    def __iter__(self) -> Iterable:
        return iter(self._container)
