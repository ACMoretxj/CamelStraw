import time
from abc import ABCMeta, abstractmethod

from ..net import HttpMethod
from ..core import JobContainer, Master, Slave
from ..util import singleton, readonly


class Launcher(metaclass=ABCMeta):
    @abstractmethod
    def launch(self, *args, **kwargs): pass


@singleton
class CmdLauncher(Launcher):

    def __init__(self, duration, worker_num, method, urls):
        readonly(self, 'duration', lambda: duration)
        readonly(self, 'worker_num', lambda: worker_num)
        readonly(self, 'method', lambda: method)
        readonly(self, 'urls', lambda: urls)

    def launch(self, *args, **kwargs):
        assert self.duration is not None and isinstance(self.duration, int)
        assert self.method is not None and isinstance(self.method, HttpMethod)
        assert len(self.urls) > 0 and all(isinstance(url, str) for url in self.urls)

        jobs = [JobContainer.from_url(url, self.method) for url in self.urls]
        master = Master(*jobs, worker_num=self.worker_num)
        master.start(local_mode=True)
        time.sleep(self.duration)
        master.stop()
        print(master.result)


@singleton
class WebLauncher(Launcher):

    def __init__(self, host, port):
        pass

    def launch(self, *args, **kwargs):
        pass


@singleton
class ApiLauncher(Launcher):

    def __init__(self, *jobs, duration, worker_num=None):
        self.__jobs = jobs
        # properties
        readonly(self, 'jobs', lambda: self.__jobs)
        readonly(self, 'duration', lambda: duration)
        readonly(self, 'worker_num', lambda: worker_num)

    def dispatch(self, job):
        self.jobs.append(job)

    def launch(self, *args, **kwargs):
        assert self.duration is not None and isinstance(self.duration, int)
        assert len(self.jobs) > 0 and all(isinstance(job, JobContainer) for job in self.jobs)

        master = Master(*self.jobs, worker_num=self.worker_num)
        master.start(local_mode=True)
        time.sleep(self.duration)
        master.stop()
        print(master.result)
