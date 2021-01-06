import itertools
from functools import reduce

import math
from typing import List

import random
import pypoman
import numpy as np
import gurobipy as g

from scipy.spatial.qhull import ConvexHull

from aistats.oracle.oracle_caller import OracleCaller
from aistats.rmp import Rmp, Vertex
from clauses.cnf import MLN, Constant
from possible_world import PossibleWorld


class HeuristicSolver:

    def __init__(self, mln: MLN, domain_size: int, oracle_caller: OracleCaller = None, tolerance: float = 0.0,
                 reflexive: bool = True):
        self.mln = mln
        self.domain_size = domain_size
        self.reflexive = reflexive
        self.convex_hull = None
        self.limits = self.calculate_limits()
        self.omega_size_log = reduce(lambda x, y: x + y, (math.log(x) for x in self.limits))
        self.oracle_caller = oracle_caller #or ForcliftClientCaller()
        self.predicates = self.get_predicates()
        self.rmp = Rmp(self.limits)
        self.tolerance = tolerance
        self.domain_constants = [Constant(f"Cons_{i}") for i in range(self.domain_size)]
        self.vertices = {}

    def calculate_limits(self) -> List[int]:
        wfs = self.mln.weighted_formulas
        if self.reflexive:
            return [self.domain_size ** len(f.formula.get_distinct_vars()) for f in wfs]
        else:
            return [reduce(lambda x, y: x * y,
                           range(self.domain_size - len(f.formula.get_distinct_vars()) + 1,
                                 self.domain_size + 1)
                           ) for f in wfs]

    def get_predicates(self):
        out = set()
        for wf in self.mln.weighted_formulas:
            pset = wf.formula.get_distinct_predicates()
            out = out.union(pset)
        return out

    def solve(self, method: str = 'ilp', relaxation: float = -1.0):
        # 1] check feasibility of all vertices as standard SAT
        not_a_corners = {}
        for k, v in self.rmp.vertices.items():
            print(k, v)
            feas = self.calculate_ilp_vtx(k)
            print(f"FEASIBLE: {feas}")
            if not feas:
                not_a_corners[k] = v
            else:
                self.vertices[k] = v

        if method == 'ilp':
            for vtx in self.run_exact_solver(relaxation):
                self.vertices[vtx.position] = vtx
        elif method == 'qhull':
            print("QHULL")
            self.get_initial_qhull()
            pw = PossibleWorld(self.domain_constants, self.mln.weighted_formulas, [], self.reflexive)
            ix = 0
            from collections import deque
            facets_ix = deque()
            dims = len(self.limits)
            for i in range(len(self.convex_hull.equations)):
                facets_ix.append(self.convex_hull.equations[i])
            while len(facets_ix) > 0:
                eq = facets_ix.popleft()
                print("FACET: ", eq)
                feasible, n_vertex, dstnc = pw.furthest_from_hull(self.convex_hull, self.limits, eq,
                                                                  write=True, write_file=f"lps/qhull/lp-{ix}.lp")
                print(feasible, n_vertex, dstnc)
                if feasible and dstnc > 1E-6:
                    self.convex_hull.add_points(np.array([n_vertex]))
                    print(self.convex_hull.equations)
                    for nix in range(-dims, 0):
                        facets_ix.append(self.convex_hull.equations[nix])
                    print(f"Found new vertex with distance {dstnc}, coordinates {n_vertex}")

        for k, v in not_a_corners.items():
            print(f"NOT A CORNER: {k}, {v}")
            for nei in v.neighbours:
                pass

    def get_initial_qhull(self):
        try:
            self.convex_hull = ConvexHull(np.array([v for v in self.vertices]), incremental=True)
        except Exception as e:
            print(e)
        if self.convex_hull is None:
            for vtx in self.run_exact_solver():
                self.vertices[vtx.position] = vtx
                if len(self.vertices) >= len(self.limits) + 1:
                    try:
                        self.convex_hull = ConvexHull(np.array([v for v in self.vertices]), incremental=True)
                    except Exception as e:
                        print(e)
                    # run exact ILP sorver until all points are found
                if self.convex_hull is not None:
                    print("Initial hull found")
                    break

    def run_exact_solver(self, relaxation = -1.0):
        #sort by limits, start from smallest
        ord_lims = [(ix, lim) for ix, lim in enumerate(self.limits)]
        ord_lims.sort(key=lambda x: x[1])
        # for each coordinate except the last one call ILP with weights
        pw = PossibleWorld(self.domain_constants, self.mln.weighted_formulas, [], self.reflexive)
        trailing_idx = ord_lims[-1][0]
        print(ord_lims)
        for cut in itertools.product(
                *[range(0, v[1] + 1, max(1, math.floor(relaxation * v[0]))) for v in ord_lims[:-1]]):
            if random.random() < relaxation:
                print(f"Skipping cut {cut}")
                continue
            print(f"Calculating for cut {cut}")
            sat_cstrs = self.satisfiable_constraints(cut, ord_lims, trailing_idx, 0, 'ge')
            print(sat_cstrs)
            # get minimal value for last idx if feasible
            satisfiable, lim = pw.satisfiable(sat_cstrs, opt_var_idx=trailing_idx, sense=g.GRB.MINIMIZE)
            if not satisfiable:
                continue
            zcoord = lim[trailing_idx]
            sat_cstrs[trailing_idx] = (zcoord, 'ge')
            tup, vtx = self.build_a_vertex(cut, ord_lims, zcoord, trailing_idx)
            if tup not in self.vertices:
                yield vtx
            # and then get maximal value
            satisfiable2, lim2 = pw.satisfiable(sat_cstrs, opt_var_idx=trailing_idx, sense=g.GRB.MAXIMIZE)
            if satisfiable2:
                zcoord = lim2[trailing_idx]
                tup, vtx = self.build_a_vertex(cut, ord_lims, zcoord, trailing_idx)
                if tup not in self.vertices:
                    yield vtx

    def build_a_vertex(self, cut, ord_lims, zcoord, tix):
        lst = [0 for _ in range(len(self.limits))]
        for ix, cval in enumerate(cut):
            lst_ix = ord_lims[ix][0]
            lst[lst_ix] = cval
        lst[tix] = int(zcoord)
        tup = tuple(lst)
        return tup, Vertex(tup)

    def satisfiable_constraints(self, cut, ord_lims, t_idx, t_val=0, t_mode='gt'):
        print(cut, t_idx)
        constraints_dict = {}
        for c_ix, val in enumerate(cut):
            formula_ix = ord_lims[c_ix][0]
            formula_val = val
            constraints_dict[formula_ix] = (formula_val, 'eq')
        constraints_dict[t_idx] = (0, 'ge')
        return constraints_dict

    def calculate_edge_frechet(self, non_corner, other, other_corner) -> (bool, float, float):
        """

        :param non_corner:
        :param other:
        :param other_corner:
        :return: (feasible, min, max); min or max is set if other is corner
        """
        model = g.Model()
        coor_var = model.addVar(lb=0.0, ub=1.0, name='P')
        diff = non_corner.numpy_position - other.numpy_position
        print(non_corner, other, other_corner)
        pred_vars = {}
        free_idx = -1
        for ix, wf in enumerate(self.mln.weighted_formulas):
            fixed = diff[ix] == 0
            free_idx = ix if not fixed else free_idx
            print(f"{ix} fixed: {fixed}")
            for clause in wf.formula.clauses:
                clause_vars = []
                for literal in clause.literals:
                    nm = f"{literal.atom.predicate.name}"
                    neg_nm = f"~{literal.atom.predicate.name}"
                    if nm in pred_vars:
                        var = pred_vars[nm] if literal.positive else pred_vars[neg_nm]
                    else:
                        pos_var = model.addVar(lb=0.0, ub=1.0, name=nm)
                        neg_var = model.addVar(lb=0.0, ub=1.0, name=f"neg_{nm}")
                        pred_vars[nm] = pos_var
                        pred_vars[neg_nm] = neg_var
                        model.addConstr(neg_var == 1 - pos_var)
                        var = pos_var if literal.positive else neg_var
                    clause_vars.append(var)
                if fixed:
                    if non_corner.position[ix] == 0:
                        model.addConstr(g.quicksum(clause_vars) == 0)
                    else:
                        model.addConstr(g.quicksum(clause_vars) >= 1)
                else:
                    model.addConstr(g.quicksum(clause_vars) >= coor_var)
                    for x in clause_vars:
                        model.addConstr(x <= coor_var)
        if other_corner:
            # We need to calculate only max or min
            if non_corner.numpy_position[free_idx] < other.numpy_position[free_idx]:
                model.setObjective(coor_var, g.GRB.MINIMIZE)
            else:
                model.setObjective(coor_var, g.GRB.MAXIMIZE)
            model.write(f"lps/{non_corner}-{other}.lp")
            model.optimize()
            if model.status == g.GRB.INFEASIBLE:
                return False, 0.0, 0.0
            else:
                res = coor_var.x
                corner = min(other.position[free_idx], 1)
                return True, min(res, corner), max(res, corner)
        else:
            # We need to calculate both max and min, but it may be infeasible
            model.setObjective(coor_var, g.GRB.MINIMIZE)
            model.write(f"lps/{non_corner}-{other}-min.lp")
            model.optimize()
            if model.status == g.GRB.INFEASIBLE:
                return False, 0.0, 0.0
            c_min = coor_var.x
            model.setObjective(coor_var. g.GRB.MAXIMIZE)
            model.write(f"lps/{non_corner}-{other}-max.lp")
            model.optimize()
            c_max = coor_var.x
            return True, c_min, c_max

    def show_rmp(self):
        if len(self.limits) != 2:
            raise Exception("Plot currently supported only for 2D")
        vtcs = [[*vtx.position] for vtx in self.vertices.values()]
        print(vtcs)
        pypoman.plot_polygon(vtcs)

    def halfspaces(self):
        vtcs = np.array([vtx.position for vtx in self.vertices.values()])
        return pypoman.duality.compute_polytope_halfspaces(vtcs)

    def calculate_ilp_vtx(self, vertex) -> bool:
        model = g.Model()
        model = model.feasibility()
        pred_vars = {}
        for ix, wf in enumerate(self.mln.weighted_formulas):
            formula = wf.formula
            for clause in formula.clauses:
                clause_vars = []
                for literal in clause.literals:
                    nm = f"{literal.atom.predicate.name}"
                    neg_nm = f"~{literal.atom.predicate.name}"
                    if nm in pred_vars:
                        var = pred_vars[nm] if literal.positive else pred_vars[neg_nm]
                    else:
                        pos_var = model.addVar(vtype=g.GRB.BINARY, name=nm)
                        neg_var = model.addVar(vtype=g.GRB.BINARY, name=f"neg_{nm}")
                        pred_vars[nm] = pos_var
                        pred_vars[neg_nm] = neg_var
                        model.addConstr(neg_var == 1 - pos_var)
                        var = pos_var if literal.positive else neg_var
                    clause_vars.append(var)
                if vertex[ix] == 0:
                    model.addConstr(g.quicksum(clause_vars) == 0)
                else:
                    model.addConstr(g.quicksum(clause_vars) >= 1)
        model.write(f"lps/heur-{vertex}.lp")
        model.setObjective(0)
        model.optimize()
        return model.status != g.GRB.INFEASIBLE


