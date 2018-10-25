class WrongStatusException(ValueError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WorkerExecuteException(ChildProcessError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
