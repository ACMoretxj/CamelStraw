from .interfaces import IAnalysable, IManager
from ..util import uid, readonly


class Session(IAnalysable):
    """
    record for every single request
    """
    def __init__(self, _protocol, _url):
        super().__init__(uid(__class__.__name__))
        self.__status_code: int = 200
        # properties
        readonly(self, 'protocol', lambda: _protocol)
        readonly(self, 'url', lambda: _url)
        readonly(self, 'status_code', lambda: self.__status_code)

    def stop(self, _status_code=200):
        super().stop()
        self.__status_code = _status_code

    def analyse(self):
        super().analyse()
        self._total_request = 1
        self._success_request = 1 if self.status_code == 200 else 0


class SessionManager(IManager):
    """
    maintain a session list, provide a pair of convenient functions
    for adding a new session
    """
    def __init__(self):
        super().__init__(uid(__class__.__name__))
        # temporary saved session object, a open & close operation
        # is a complete life cycle of the session
        self.__session = None

    def open(self, protocol, url):
        """
        open a new session
        :return: the session object
        """
        self.__session = Session(_protocol=protocol, _url=url)
        self.__session.start()
        return self.__session

    def close(self, status_code):
        """
        close and save the opened session
        :param status_code:
        :return: None
        """
        self.__session.stop(_status_code=status_code)
        self._container.append(self.__session)
        self.__session = None
