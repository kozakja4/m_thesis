import abc

from typing import List
from numpy import empty, array


class PointEnumerator(abc.ABC):

    def __init__(self, limits: List[int]):
        self.limits = limits
        self.dimensions = len(limits)
        self.divisors = self._calculate_divisors()

    @abc.abstractmethod
    def generate_points(self):
        pass

    def unrank_combination(self, index: int) -> array:
        out = empty(self.dimensions)
        for dim, dim_div in enumerate(self.divisors):
            out[self.dimensions - 1 - dim] = index // dim_div
            index %= dim_div
        return out

    def _calculate_divisors(self) -> List[int]:
        out = [1]
        for i in range(len(self.limits) - 1):
            out.append(out[-1] * (self.limits[i] + 1))
        out.reverse()
        return out
