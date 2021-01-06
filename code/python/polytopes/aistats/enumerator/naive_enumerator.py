from typing import List

import numpy as np

from itertools import combinations, permutations, product
from functools import reduce
from numpy.linalg import matrix_rank

from aistats.enumerator.point_enumerator import PointEnumerator


class NaiveEnumerator(PointEnumerator):
    # Enumerate all combinations, check independence after that...

    def generate_points(self):
        domain_size = reduce(lambda x, y: x * y, (x + 1 for x in self.limits))
        for combination in combinations(range(domain_size), self.dimensions):
            pre_out = np.empty((self.dimensions, self.dimensions))
            for out_idx, c_idx in enumerate(combination):
                pre_out[out_idx, :] = self.unrank_combination(c_idx)
            out, independent = self._check_independence(pre_out)
            if independent:
                yield out

    def _check_independence(self, matrix: np.array) -> (np.array, bool):
        first_line = matrix[0, :]
        out = matrix[1:, :] - first_line
        m_rank = matrix_rank(out)
        return out, m_rank == self.dimensions - 1


class IterEnumerator(PointEnumerator):

    def generate_points(self):
        pre_out = np.empty((self.dimensions - 1, self.dimensions))
        center = np.zeros((1, self.dimensions))
        base_limits = [(-x, x) for x in self.limits]

        def inner_next_points_in_limits(point_limit):
            for drct in product(*map(lambda x: range(x[0], x[1] + 1), point_limit)):
                yield drct

        def inner_yielding(dimension, point_limit, it_center):
            if dimension == self.dimensions:
                out = pre_out.copy()
                print(out)
                yield out
            else:
                for point in inner_next_points_in_limits(point_limit):
                    pre_out[dimension - 1, :] = np.array(point) + it_center
                    if matrix_rank(pre_out) == dimension:
                        n_limit = [
                            (max(-sl, pl[0] - pt), min(sl, pl[1] - pt))
                            for pl, sl, pt in zip(point_limit, self.limits, point)
                        ]
                        yield from inner_yielding(dimension + 1, n_limit, point)

        yield from inner_yielding(1, base_limits, center)


# OK only in 2d
class CenterEnumerator(PointEnumerator):

    def generate_points(self):
        domain_size = reduce(lambda x, y: x * y, (x + 1 for x in self.limits))

        for bp in self.beginning_points():
            print(bp)
            signs = -2 * np.sign(bp) + 1
            pre_out = np.empty((self.dimensions, self.dimensions))
            pre_out[0, :] = bp
            for combination in combinations(range(1, domain_size), self.dimensions - 1):
                for out_idx, c_idx in enumerate(combination):
                    pre_out[out_idx + 1, :] = self.unrank_combination(c_idx) * signs + bp
                out, independent = self._check_independence(pre_out)
                if independent:
                    yield out

    def _check_independence(self, matrix: np.array) -> (np.array, bool):
        first_line = matrix[0, :]
        out = matrix[1:, :] - first_line
        m_rank = matrix_rank(out)
        return out, m_rank == self.dimensions - 1

    def beginning_points(self):
        """
        Generates starting points for enumeration (half of initial polytope vertices, first axis is set to its limit)
        :return:
        """
        #for bp in product([self.limits[0]], *map(lambda x: [0, x], self.limits[1:])):
        for bp in product(*map(lambda x: [0, x], self.limits)):
            yield np.array(bp)


class Enumerator2D(PointEnumerator):

    def __init__(self, limits: List[int]):
        super().__init__(limits)
        if self.dimensions != 2:
            raise TypeError("This enumerator works only in 2D")

    def generate_points(self):
        for x in range(self.limits[0] + 1):
            for y in range(self.limits[1] + 1):
                if x == y == 0:
                    continue
                yield np.array([x, y])
                yield np.array([-x, y])


if __name__ == "__main__":
    import aistats.utils as aiu
    dims = [1,1,1,1,1]
    en = IterEnumerator(dims)  #NaiveEnumerator([10, 4, 3])
    dist_normals, points = set(), 0  # 12150, 278k
    for point in en.generate_points():
        points += 1
        if points % 10000 == 0:
            print(f"Point n-tuples: {points}\nDist_points: {len(dist_normals)}")
        normal = aiu.calculate_normal(point)
        nmlzd = aiu.normalize_vector(normal)
        dist_normals.add(tuple(nmlzd))
        dist_normals.add(tuple(-nmlzd))
    #print(dist_normals)
    print(f"Point n-tuples: {points}\nDist_points: {len(dist_normals)}")

    print("NAIVE")
    en = NaiveEnumerator(dims)  # NaiveEnumerator([10, 4, 3])
    dist_normals2, points2 = set(), 0  # 12150, 278k
    for point in en.generate_points():
        points2 += 1
        if points2 % 10000 == 0:
            print(f"Point n-tuples: {points2}\nDist_normals: {len(dist_normals2)}")
        normal = aiu.calculate_normal(point)
        nmlzd = aiu.normalize_vector(normal)
        dist_normals2.add(tuple(nmlzd))
        dist_normals2.add(tuple(-nmlzd))
    #print(dist_normals2)
    print("In naive, not in center")
    print(dist_normals2 - dist_normals)
    print("In center, not in naive")
    print(dist_normals - dist_normals2)
    print(f"Point n-tuples: {points2}\nDist_normals: {len(dist_normals2)}")
