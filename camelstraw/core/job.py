from camelstraw.core.session import SessionManager
from camelstraw.core.interfaces import IAnalysable, IManager
from camelstraw.util import uid


class Job(IAnalysable):

    def __init__(self):
        self.__session_manager: SessionManager = SessionManager()
        super().__init__(uid(__class__.__name__), self.__session_manager)


class JobManager(IManager):

    def __init__(self):
        super().__init__(uid(__class__.__name__))
