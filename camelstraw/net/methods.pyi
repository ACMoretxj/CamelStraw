from enum import IntEnum


class HttpMethod(IntEnum):
    value: int
    phrase: str
    description: str

    GET: HttpMethod
    POST: HttpMethod
    PUT: HttpMethod
    PATCH: HttpMethod
    DELETE: HttpMethod
    HEAD: HttpMethod
    OPTIONS: HttpMethod
    def __new__(cls, value: int, phrase: str, description: str=''): pass
