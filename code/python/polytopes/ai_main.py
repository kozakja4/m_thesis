import argparse

import time

from aistats.aistats import AiStatsRmpSolver
from aistats.enumerator.naive_enumerator import Enumerator2D, NaiveEnumerator
from aistats.oracle.forclift_callers import ForcliftClientCaller, ForcliftV1
from clauses.cnf import WeightedFormula, MLN
from cnf_parser import CnfParser


if __name__ == "__main__":
    a_pars = argparse.ArgumentParser("Runner for WFOMC based solver.")
    a_pars.add_argument("input_file", "Path to input CNF file.")
    a_pars.add_argument("domain_size", "Domain size of MLN.", type=int)
    a_pars.add_argument("-f", "--forclift_path", "Path to forclift (for standard Oracle)")
    a_pars.add_argument("-p", "--port", "Port - for server-like WFOMC Oracle (must run on localhost)")
    a_pars.add_argument("-ot", "--oracle_type", "Oracle caller type (server or standard)",
                        choices=["server", "standard"], default="server")

    args = a_pars.parse_args()
    parser = CnfParser()
    cnf = parser.read_file(args.input_file)
    mln = MLN(cnf.formulas)
    domain_size = args.domain_size
    print(f"DOMAIN SIZE: {domain_size}")
    if args.ot == "standard":
        print("Use standard Forclift caller (new process for each call)")
        ocaller = ForcliftV1(args.forclift_path)
    else:
        if args.port > 0:
            print(f"Use forclift server on port {args.port}")
            ocaller = ForcliftClientCaller(port=args.port)
        else:
            print("Start a new forclift server")
            ocaller = ForcliftClientCaller(wrapper_path = args.forclift_path)

    a_solver = AiStatsRmpSolver(mln, domain_size, tolerance=1E-2, enumerator_cls=NaiveEnumerator,
                                oracle_caller=ForcliftClientCaller(port=1567))
    ntime = time.time()
    a_solver.solve()
    etime = time.time()
    print(f"Took {etime - ntime: 0.3f} s")
    print(a_solver.rmp)
    a_solver.plot_rmp()
