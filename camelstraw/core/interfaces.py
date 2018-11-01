import json
from abc import ABCMeta
from enum import IntEnum
from json import JSONDecodeError

from ..exception import WrongStatusException
from ..util import Stopwatch, TimeFormat, readonly


class CoreStatus(IntEnum):

    def __new__(cls, value, phrase, description=''):
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


class AnalyseResult:

    @classmethod
    def from_json(cls, data):
        try:
            if isinstance(data, str):
                data = json.loads(data)
        except (ValueError, JSONDecodeError):
            raise

        assert 'id' in data
        assert 'total_request' in data
        assert 'success_request' in data
        assert 'latency' in data
        assert 'qps' in data
        assert 'start_time' in data
        assert 'stop_time' in data

        return AnalyseResult(_id=data['id'], total_request=data['total_request'],
                             success_request=data['success_request'], latency=data['latency'], qps=data['qps'],
                             start_time=data['start_time'], stop_time=data['stop_time'])

    @classmethod
    def from_results(cls, _id, results):
        start_time = min(r.start_time for r in results)
        stop_time = max(r.stop_time for r in results)
        latency = stop_time - start_time
        total_request = sum(r.total_request for r in results)
        success_result = sum(r.success_request for r in results)
        qps = success_result * 1000 // max(1, latency)
        return AnalyseResult(_id=_id, total_request=total_request, success_request=success_result,
                             latency=latency, qps=qps, start_time=start_time, stop_time=stop_time)

    def __init__(self, _id, total_request, success_request, latency, qps, start_time, stop_time):
        readonly(self, 'id', lambda: _id)
        readonly(self, 'total_request', lambda: total_request)
        readonly(self, 'success_request', lambda: success_request)
        readonly(self, 'latency', lambda: latency)
        readonly(self, 'qps', lambda: qps)
        readonly(self, 'start_time', lambda: start_time)
        readonly(self, 'stop_time', lambda: stop_time)

    def __repr__(self):
        reprs = [
            '=' * 128,
            'Id: %s' % self.id,
            'Request: %s/%s' % (self.success_request, self.total_request),
            'Latency: %s ms' % self.latency,
            'QPS: %s' % self.qps,
            'Start Time: %s' % TimeFormat.from_millisecond(self.start_time),
            'Stop Time: %s' % TimeFormat.from_millisecond(self.stop_time),
            '=' * 128]
        return '\n'.join(reprs)

    @property
    def json_result(self) -> str:
        """
        return tests result in json format
        :return:
        """
        data = {
            'id': '%s' % self.id,
            'total_request': '%s' % self.total_request,
            'success_request': '%s' % self.success_request,
            'latency': '%s' % self.latency,
            'qps': '%s' % self.qps,
            'start_time': '%s' % self.start_time,
            'stop_time': '%s' % self.stop_time
        }
        return json.dumps(data)


class IAnalysable(metaclass=ABCMeta):
    """
    generic interface for all analysable objects including
    Session/Job/Worker etc, for the convenience of computing
    and visualization
    """
    def __new__(cls, *args, **kwargs):
        # TODO: unknown problem.
        # the following code seems duplicate to that in __init__,
        # but it's a must when used in Process & dill
        inst = super().__new__(cls)
        readonly(inst, 'id', lambda: None)
        readonly(inst, 'qps', lambda: None)
        readonly(inst, 'start_time', lambda: None)
        readonly(inst, 'stop_time', lambda: None)
        readonly(inst, 'status', lambda: None)
        readonly(inst, 'result', lambda: None)
        return inst

    def __init__(self, _id, _manager=None):
        self._manager = _manager
        self._status = CoreStatus.INIT
        self._stopwatch = Stopwatch()
        self._total_request = 0
        self._success_request = 0
        self._latency = 0
        self._analyse_result = None
        # properties
        readonly(self, 'id', lambda: _id)
        readonly(self, 'qps', lambda: self.success_request * 1000 // max(1, self.latency))
        readonly(self, 'start_time', lambda: self._stopwatch.start_time)
        readonly(self, 'stop_time', lambda: self.start_time + self.latency)
        readonly(self, 'status', lambda: self._status)
        readonly(self, 'result', lambda: self._analyse_result)

    def __repr__(self):
        return str(self.result)

    @property
    def total_request(self) -> int:
        if self.status != CoreStatus.ANALYSED:
            raise WrongStatusException('_total_request is not computed')
        return self._total_request

    @property
    def success_request(self) -> int:
        if self.status != CoreStatus.ANALYSED:
            raise WrongStatusException('_success_request is not computed')
        return self._success_request

    @property
    def latency(self) -> int:
        if self.status != CoreStatus.ANALYSED:
            raise WrongStatusException('_latency is not computed')
        return self._latency

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
        if self._analyse_result is not None:
            return
        if self._manager is not None:
            for item in self._manager:
                item.analyse()
                self._total_request += item.total_request
                self._success_request += item.success_request
            # record analyse result
            self._analyse_result = AnalyseResult(_id=self.id, total_request=self.total_request,
                                                 success_request=self.success_request, latency=self.latency,
                                                 qps=self.qps, start_time=self.start_time, stop_time=self.stop_time)


class IManager(metaclass=ABCMeta):
    """
    generic interface for all manager objects including
    SessionManager/JobManager/WorkerManager etc, collecting
    common logic for all managers
    """
    def __init__(self, _id):
        readonly(self, 'id', lambda: _id)
        self._container = []

    def __iter__(self):
        return iter(self._container)

    def add(self, obj):
        self._container.append(obj)
