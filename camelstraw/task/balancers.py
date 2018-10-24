from abc import ABCMeta, abstractmethod
from random import randint
from typing import List


class IDispatchMixin:
    @abstractmethod
    def weight(self):
        pass


class IBalancer(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def choose(*args, **kwargs):
        pass


class RandomBalancer(IBalancer):
    @staticmethod
    def choose(items: List[IDispatchMixin]):
        return items[randint(0, len(items) - 1)]
