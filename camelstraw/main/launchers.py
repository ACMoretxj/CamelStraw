from abc import ABCMeta, abstractmethod


class Launcher(metaclass=ABCMeta):
    @abstractmethod
    def launch(self, *args, **kwargs) -> None: pass


class CmdLauncher(Launcher):
    def __init__(self, worker_num, duration, method, urls):
        pass

    def launch(self, *args, **kwargs):
        pass


class WebLauncher(Launcher):
    def __init__(self, host, port):
        pass

    def launch(self, *args, **kwargs):
        pass


class ApiLauncher(Launcher):
    def __init__(self):
        pass

    def launch(self, *args, **kwargs):
        pass
