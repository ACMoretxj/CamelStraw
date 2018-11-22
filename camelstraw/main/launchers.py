import time
from abc import ABCMeta, abstractmethod

from ..core import JobContainer, Master, Slave
from ..util import singleton, readonly


class Launcher(metaclass=ABCMeta):
    @abstractmethod
    def launch(self, *args, **kwargs): pass


@singleton
class CmdLauncher(Launcher):

    def __init__(self, worker_num, duration, method, urls):
        readonly(self, 'worker_num', lambda: worker_num)
        readonly(self, 'duration', lambda: duration)
        readonly(self, 'method', lambda: method)
        readonly(self, 'urls', lambda: urls)

    def launch(self, *args, **kwargs):
        jobs = [JobContainer.from_url(url, self.method) for url in self.urls]
        master = Master(*jobs)
        master.start()
        slave = Slave()
        slave.start()
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
    def __init__(self):
        pass

    def launch(self, *args, **kwargs):
        pass
