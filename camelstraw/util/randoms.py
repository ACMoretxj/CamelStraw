from uuid import uuid4

from ..net import get_host_ip


def uid(namespace=None):
    if namespace is None:
        return str(uuid4())
    return '%s-%s-%s' % (get_host_ip(), namespace, uuid4())
