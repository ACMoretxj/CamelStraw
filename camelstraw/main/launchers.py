import time
from abc import ABCMeta, abstractmethod

from ..net import HttpMethod
from ..core import JobContainer, Master, Slave
from ..util import singleton, readonly


class BaseLauncher(metaclass=ABCMeta):

    @abstractmethod
    def launch(self, *args, **kwargs):
        pass

    @staticmethod
    def launch_master(*jobs, worker_num=None):
        master = Master(*jobs, worker_num=worker_num)
        master.start()
        return master

    @staticmethod
    def launch_slaves(local_mode=True):
        if local_mode:
            slave = Slave()
            slave.start()
            return [slave]
        # TODO: implement left functions


@singleton
class CmdLauncher(BaseLauncher):

    def __init__(self, duration, worker_num, method, urls):
        readonly(self, 'duration', lambda: duration)
        readonly(self, 'worker_num', lambda: worker_num)
        readonly(self, 'method', lambda: method)
        readonly(self, 'urls', lambda: urls)

    def launch(self, local_mode=True):
        assert self.duration is not None and isinstance(self.duration, int)
        assert self.method is not None and isinstance(self.method, HttpMethod)
        assert len(self.urls) > 0 and all(isinstance(url, str) for url in self.urls)

        jobs = [JobContainer.from_url(url, self.method) for url in self.urls]
        master = self.launch_master(*jobs, worker_num=self.worker_num)
        self.launch_slaves(local_mode)
        time.sleep(self.duration)
        master.stop()
        print(master.result)


@singleton
class WebLauncher(BaseLauncher):

    def __init__(self, host, port):
        pass

    def launch(self, *args, **kwargs):
        pass


@singleton
class ApiLauncher(BaseLauncher):

    def __init__(self, *jobs, duration, worker_num=None):
        self.__jobs = jobs
        # properties
        readonly(self, 'jobs', lambda: self.__jobs)
        readonly(self, 'duration', lambda: duration)
        readonly(self, 'worker_num', lambda: worker_num)

    def dispatch(self, job):
        self.jobs.append(job)

    def launch(self, local_mode=True):
        assert self.duration is not None and isinstance(self.duration, int)
        assert len(self.jobs) > 0 and all(isinstance(job, JobContainer) for job in self.jobs)

        master = self.launch_master(*self.jobs, worker_num=self.worker_num)
        self.launch_slaves(local_mode)
        time.sleep(self.duration)
        master.stop()
        print(master.result)
