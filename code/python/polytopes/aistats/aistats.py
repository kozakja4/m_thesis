import math
import numpy as np
import polytope
import re

from typing import List
from functools import reduce

import aistats.utils as aiu

from aistats.enumerator.naive_enumerator import NaiveEnumerator
from aistats.enumerator.point_enumerator import PointEnumerator
from aistats.oracle.forclift_callers import ForcliftV1
from aistats.oracle.oracle_caller import OracleCaller
from clauses.cnf import MLN, WeightedFormula


class AiStatsRmpSolver:

    def __init__(self, mln: MLN, domain_size: int, enumerator_cls=NaiveEnumerator,
                 enumerator: PointEnumerator = None, oracle_caller: OracleCaller = None,
                 tolerance: float = 0.0):
        self.mln = mln
        self.domain_size = domain_size
        self.limits = self.calculate_limits()
        self.omega_size_log = reduce(lambda x, y: x + y, (math.log(x) for x in self.limits))
        self.enumerator = enumerator or enumerator_cls(self.limits)
        self.oracle_caller = oracle_caller or ForcliftV1()
        self.predicates = self.get_predicates()
        self.rmp = polytope.box2poly([[0, lim] for lim in self.limits])
        self.tolerance = tolerance

    def calculate_limits(self) -> List[int]:
        wfs = self.mln.weighted_formulas
        return [self.domain_size ** len(f.formula.get_distinct_vars()) for f in wfs]

    def get_predicates(self):
        out = set()
        for wf in self.mln.weighted_formulas:
            pset = wf.formula.get_distinct_predicates()
            out = out.union(pset)
        return out

    def solve(self) -> None:
        normals = set()
        irmp_constraints = []
        for normal in self.generate_normals():
            n_tuple = tuple(normal)
            if n_tuple in normals:
                continue
            normals.add(n_tuple)
            normals.add(tuple(-normal))
            for c_normal in [normal, -normal]:
                try:
                    z_log = self.forclift_for_normal(c_normal)
                except (ValueError, TypeError) as e:
                    # log
                    print(e)
                    continue
                # b = math.ceil(0.5 * z_log / self.omega_size_log - 0.5)
                if math.isnan(z_log) or math.isinf(z_log):
                    continue
                b = 0.5 * z_log / self.omega_size_log - 0.5
                if self.tolerance == 0.0 or b - math.floor(b) > self.tolerance:
                    irmp_constraints.append((c_normal, math.ceil(b)))
                else:
                    irmp_constraints.append((c_normal, math.floor(b)))

            if len(irmp_constraints) > 10:
                self.find_min_set(irmp_constraints)
                print(irmp_constraints)
                irmp_constraints = []
        self.find_min_set(irmp_constraints)

    def generate_normals(self):
        for points in self.enumerator.generate_points():
            normal = aiu.calculate_normal(points)
            yield aiu.normalize_vector(normal)

    def forclift_for_normal(self, normal):
        """

        :param normal:
        :return: natural logarithm of the partition function
        """
        n_formulas = [
            WeightedFormula(2 * w * self.omega_size_log, f.formula) for w, f in zip(normal, self.mln.weighted_formulas)
        ]
        print("Call oracle")
        return self.oracle_caller.call_oracle(self.domain_size, self.predicates, n_formulas)

    def find_min_set(self, irmp_constraints):
        A_rmp = np.empty((len(irmp_constraints), len(self.limits)))
        for ix in range(len(irmp_constraints)):
            A_rmp[ix, :] = irmp_constraints[ix][0]
        b_rmp = np.array([val[1] for val in irmp_constraints])
        A_stack, b_stack = np.row_stack((self.rmp.A, A_rmp)), np.concatenate((self.rmp.b, b_rmp))
        self.rmp = polytope.reduce(polytope.Polytope(A_stack, b_stack))

    def plot_rmp(self):
        if self.rmp.dim != 2:
            raise Exception("Plotting only 2D RMP is supported")
        import matplotlib.pyplot as plt
        rmp_bb = self.rmp.bounding_box
        plt.xlim((rmp_bb[0][0], rmp_bb[1][0]))
        plt.ylim((rmp_bb[0][1], rmp_bb[1][1]))
        plt.xlabel(str(self.mln.weighted_formulas[0]))
        plt.ylabel(str(self.mln.weighted_formulas[1]))
        ax = plt.gca()
        self.rmp.plot(ax=ax)
        plt.show()
