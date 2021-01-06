from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

from aistats.heuristic import HeuristicSolver
from clauses.cnf import WeightedFormula, MLN, Constant
from cnf_parser import CnfParser

import argparse

import time

from possible_world import PossibleWorld

if __name__ == "__main__":
    a_parser = argparse.ArgumentParser("Runner for ILP RMP solver (heuristic if alpha > 0)")
    a_parser.add_argument("input_file", help="Path to input file (see cnfs for format)")
    a_parser.add_argument("domain_size", help="Domain size", type=int)
    a_parser.add_argument("-a", "--alpha", help="Alpha (> 0 - heuristic)", type=float, default=-1.0)
    a_parser.add_argument("-m", "--method", help="Solver type", type=str, choices=['qhull', 'ilp'],
                          default='ilp')
    args = a_parser.parse_args()
    parser = CnfParser()
    parser.read_file(args.input_file)
    domain_size = args.domain_size
    print(f"DOMAIN SIZE: {domain_size}")

    mln = MLN(parser.formulas)

    pw = PossibleWorld([Constant(f"d_{i}") for i in range(domain_size)], mln.weighted_formulas, [])
    a_solver = HeuristicSolver(mln, domain_size, reflexive=False)

    ntime = time.time()
    if 1.0 > args.alpha > 0.0:
        print(f"Use relaxation with parameter {args.alpha}")
        if args.method == 'qhull':
            print("qhull option ignored, executing ILP solver")
        a_solver.solve(relaxation=args.alpha)
    else:
        print("Run exact solver.")
        a_solver.solve(method=args.method)

    etime = time.time()
    print(f"Took {etime - ntime: 0.3f} s")

    if args.method == 'qhull' and len(mln.weighted_formulas) == 2:
        import matplotlib.pyplot as plt
        ch = a_solver.convex_hull
        plt.xlim([0, a_solver.limits[0]])
        plt.ylim([0, a_solver.limits[1]])


        polygon = Polygon(ch.points[ch.vertices], True)
        p = PatchCollection([polygon], alpha=0.4)

        ax = plt.gca()
        ax.add_collection(p)
        #ax.set_xlim([0, 1])
        #ax.set_ylim([0, 1])
        #pairs = calc_a()
        ax.plot(ch.points[ch.vertices, 0], ch.points[ch.vertices, 1], "ro", clip_on=False)

        #plt.plot(ch.points[ch.vertices, 0], ch.points[ch.vertices, 1], 'r--', lw=2)
        #plt.plot(ch.points[ch.vertices[0], 0], ch.points[ch.vertices[0], 1], 'bo')

        plt.show()

    print("VERTICES:")
    print(a_solver.vertices)
    print("HALFSPACES:")
    print(a_solver.halfspaces())
    if len(parser.formulas) == 2:
        a_solver.show_rmp()
