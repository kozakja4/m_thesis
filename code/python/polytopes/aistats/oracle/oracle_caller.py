import abc

from typing import Iterable, List

from clauses.cnf import Atom, WeightedFormula


class OracleCaller(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def call_oracle(self, domain_size: int, atoms: Iterable[Atom], cnfs: List[WeightedFormula]) -> float:
        """

        :param domain_size:
        :param atoms:
        :param cnfs:
        :return: natural logarithm of MLN's partition function
        """
        pass
