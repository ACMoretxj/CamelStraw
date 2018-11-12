from functools import wraps


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def readonly(obj, name, value):
    func_name: str = '__readonly_%s' % name
    setattr(obj, func_name, value)
    setattr(obj.__class__, name, property(lambda x: x.__dict__[func_name]()))
