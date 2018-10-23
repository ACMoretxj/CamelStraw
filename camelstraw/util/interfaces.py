from abc import ABCMeta, abstractmethod

from camelstraw.exception.exceptions import WrongStatusException


class IAnalysable(metaclass=ABCMeta):

    def __init__(self, _id):
        self._id: str = _id
        self._total_request: int = 0
        self._success_request: int = 0
        self._latency: int = 0

    @property
    def id(self) -> str:
        return self._id

    @property
    def total_request(self) -> int:
        if self._total_request == 0:
            raise WrongStatusException('_total_request is not computed')
        return self._total_request

    @property
    def success_request(self):
        if self._success_request == 0:
            raise WrongStatusException('_success_request is not computed')
        return self._success_request

    @property
    def latency(self):
        if self._latency == 0:
            raise WrongStatusException('_latency is not computed')
        return self._latency

    @property
    def qps(self) -> int:
        return self.success_request * 1000 // max(1, self.latency)

    @abstractmethod
    def analyse(self):
        pass

    def __repr__(self):
        reprs = [
            '=' * 100,
            'Id: %s' % self.id,
            'Request: %s/%s' % (self.success_request, self.total_request),
            'Latency: %sms' % self.latency,
            'QPS, %s' % self.qps,
            '=' * 100]
        return '\n'.join(reprs)
