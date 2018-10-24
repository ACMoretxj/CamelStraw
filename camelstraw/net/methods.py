from enum import IntEnum


class HttpMethod(IntEnum):

    def __new__(cls, value: int, phrase: str, description: str=''):
        # noinspection PyArgumentList
        obj: int = int.__new__(cls, value)
        obj._value_ = value

        obj.phrase = phrase
        obj.description = description
        return obj

    GET = 100, 'HttpGet'
    POST = 101, 'HttpPost'
    PUT = 103, 'HttpPut'
    PATCH = 104, 'HttpPatch'
    DELETE = 105, 'HttpDelete'
    HEAD = 106, 'HttpHead'
    OPTIONS = 107, 'HttpOptions'
