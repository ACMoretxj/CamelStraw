from abc import ABCMeta
from collections import Iterable

from camelstraw.exception.exceptions import WrongStatusException
from camelstraw.util.clocks import Stopwatch


class IAnalysable(metaclass=ABCMeta):

    def __init__(self, _id: str, _manager=None):
        self._id: str = _id
        self._manager: IManager = _manager
        self._total_request: int = 0
        self._success_request: int = 0
        self._latency: int = 0
        self._stopwatch: Stopwatch = Stopwatch()

    @property
    def id(self) -> str:
        return self._id

    @property
    def total_request(self) -> int:
        if self._total_request < 0:
            raise WrongStatusException('_total_request is not computed')
        return self._total_request

    @property
    def success_request(self):
        if self._success_request < 0:
            raise WrongStatusException('_success_request is not computed')
        return self._success_request

    @property
    def latency(self):
        if self._latency < 0:
            raise WrongStatusException('_latency is not computed')
        return self._latency

    @property
    def qps(self) -> int:
        return self.success_request * 1000 // max(1, self.latency)

    def start(self, *args, **kwargs):
        self._stopwatch.start()

    def stop(self, *args, **kwargs):
        self._latency = self._stopwatch.elapsed_time

    def analyse(self):
        if self._manager is not None:
            for item in self._manager:
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

    def __init__(self, _id: str):
        self._id = _id
        self._container = []

    def add(self, obj: IAnalysable) -> None:
        self._container.append(obj)

    def __iter__(self) -> Iterable:
        return iter(self._container)
