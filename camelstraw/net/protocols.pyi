from enum import IntEnum


class Protocol(IntEnum):
    HTTP: Protocol
    HTTPS: Protocol
    WS: Protocol
    WSS: Protocol
    def __new__(cls, value: int, phrase: str, prefix: str='', description: str=''): pass
    @classmethod
    def from_url(cls, url) -> Protocol: pass
