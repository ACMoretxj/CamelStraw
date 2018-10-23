from uuid import uuid4


def uid(namespace: str=None) -> str:
    if namespace is None:
        return str(uuid4())
    return '%s-%s' % (namespace, uuid4())
