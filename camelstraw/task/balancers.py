from abc import ABCMeta, abstractmethod
from random import randint
from typing import List


class IDispatchable:

    @abstractmethod
    def dispatch(self, *args, **kwargs):
        pass

    @abstractmethod
    def weight(self):
        pass


class IBalancer(metaclass=ABCMeta):
    @abstractmethod
    def choose(self, *args, **kwargs):
        pass


class Random(IBalancer):

    @staticmethod
    def choose(items: List[IDispatchable]):
        return items[randint(0, len(items) - 1)]


class RoundRobin(IBalancer):

    def __init__(self):
        self.__pos = 0

    def choose(self, items: List[IDispatchable]):
        self.__pos += 1
        return items[self.__pos % len(items)]


class WeightRoundRobin(IBalancer):

    def __init__(self):
        self.__pos = 0

    def choose(self, items: List[IDispatchable]):
        self.__pos += 1
        weight_items = [item for item in items for _ in range(item.weight())]
        return weight_items[self.__pos % len(weight_items)]
