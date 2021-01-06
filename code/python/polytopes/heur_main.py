from aistats.heuristic import HeuristicSolver
from clauses.cnf import WeightedFormula, MLN, Constant
from cnf_parser import CnfParser

from scipy.spatial.qhull import ConvexHull

import argparse

import time

from possible_world import PossibleWorld

if __name__ == "__main__":
    a_parser = argparse.ArgumentParser("Runner for ILP RMP solver (heuristic if alpha > 0)")
    a_parser.add_argument("input_file", "Path to input file (see cnfs for format)")
    a_parser.add_argument("domain_size", "Domain size", type=int)
    a_parser.add_argument("-a", "--alpha", "Alpha (> 0 - heuristic)", type=float, default=0.0)
    args = a_parser.parse_args()
    parser = CnfParser()
    parser.read_file(args.input_file)
    domain_size = args.domain_size
    print(f"DOMAIN SIZE: {domain_size}")

    mln = MLN(parser.formulas)

    pw = PossibleWorld([Constant(f"d_{i}") for i in range(domain_size)], mln.weighted_formulas, [])

    #chs = ConvexHull([[9, 9], [0,9], [5, 8]], incremental=True)
    #print(chs.equations)
    #feasible, point, obj = pw.furthest_from_hull(chs, [domain_size**2, domain_size**2], write=True,
     #                                            write_file="lps/qhull.lp")
    #print(feasible, point, obj)
    a_solver = HeuristicSolver(mln, domain_size, reflexive=False)

    ntime = time.time()
    if 1.0 > a_parser.alpha > 0.0:
        print(f"Use relaxation with parameter {a_parser.alpha}")
        a_solver.solve(relaxation=a_parser.alpha)
    else:
        print("Run exact solver.")
        a_solver.solve(relaxation=0.0)
    etime = time.time()
    print(f"Took {etime - ntime: 0.3f} s")

    print("VERTICES:")
    print(a_solver.vertices)
    print("HALFSPACES:")
    print(a_solver.halfspaces())
    if len(parser.formulas) == 2:
        a_solver.show_rmp()
