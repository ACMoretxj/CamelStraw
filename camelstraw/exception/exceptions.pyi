class WrongStatusException(ValueError):
    def __init__(self, *args, **kwargs): pass

class WorkerExecuteException(ChildProcessError):
    def __init__(self, *args, **kwargs): pass
