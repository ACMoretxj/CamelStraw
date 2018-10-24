from enum import IntEnum


class Protocol(IntEnum):

    def __new__(cls, value: int, phrase: str, prefix: str='', description: str=''):
        # noinspection PyArgumentList
        obj: int = int.__new__(cls, value)
        obj._value_ = value

        obj.prefix = prefix
        obj.phrase = phrase
        obj.description = description
        return obj

    @classmethod
    def from_url(cls, url):
        for protocol in [Protocol.HTTP, Protocol.HTTPS, Protocol.WS, Protocol.WSS]:
            if protocol.prefix in url:
                return protocol
        return Protocol.HTTP

    HTTP = 100, 'Http', 'http'
    HTTPS = 101, 'Http-Safe', 'https'
    WS = 102, 'Websocket', 'ws'
    WSS = 103, 'Websocket-Safe', 'wss'
