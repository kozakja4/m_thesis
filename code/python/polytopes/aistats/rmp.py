from typing import List

import numpy as np
import aistats.utils as aiu

from itertools import product


class Rmp:

    def __init__(self, limits):
        self.limits = limits
        self.dimensions = len(limits)
        self.vertices = self._generate_vertices()
        self.inner_point = [x * 0.5 for x in self.limits]

    def _generate_vertices(self):
        vertices = {}
        for vtx in product(*map(lambda x: [0, x], self.limits)):
            n_vertex = Vertex(vtx)
            vertices[vtx] = n_vertex
        for v_coord, vertex in vertices.items():
            for ix, ix_value in enumerate(v_coord):
                n_value = 0 if ix_value > 0 else self.limits[ix]
                neighbour_tuple = v_coord[:ix] + (n_value, ) + v_coord[(ix + 1):]
                neighbour_vtx = vertices[neighbour_tuple]
                vertex.neighbours.append(neighbour_vtx)
        return vertices


class Vertex:

    def __init__(self, position, neighbours=None):
        self.position = position
        self.dimension = len(position)
        self.numpy_position = np.array(position)
        self.neighbours = neighbours or []  # Set[Vertex]

    def neighbour_normal(self) -> np.ndarray:
        neighbours = self.neighbour_matrix()
        normal = aiu.calculate_normal(neighbours)
        return aiu.normalize_vector(normal)

    def neighbour_matrix(self) -> np.ndarray:
        out = np.empty((self.dimension - 1, self.dimension))
        for ix, nei in enumerate(self.neighbours[1:]):
            out[ix, :] = nei.numpy_position
        return out - self.neighbours[0].numpy_position

    def __str__(self):
        return f"{self.position}"

    def __repr__(self):
        return f"Vertex[{self.position}]"

    def __eq__(self, other):
        if isinstance(other, Vertex):
            return self.position == other.position
        return False

    def __hash__(self):
        return hash(self.position)


if __name__ == "__main__":
    rmp = Rmp([3, 5, 1])
    for tup, vtx in rmp.vertices.items():
        print(f"Vertex: {vtx}")
        print(vtx.neighbours)
        print(vtx.neighbour_matrix())
        print(vtx.neighbour_normal())
