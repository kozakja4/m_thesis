import sys

import clauses.cnf as cn
from cnf_parser import CnfParser
from possible_world import PossibleWorld

# USAGE: main.py DOMAIN_SIZE INPUT_FILE N(ALPHAS)
# DOMAIN_SIZE - size of domain in question (int)
# INPUT_FILE  - file with CNFs
# N_ALPHAS    - Number of groundings to check for each formula, delimited by comma, declared in same order
#               as CNF formulas in the input file


if __name__ == "__main__":
    domain = sys.argv[1]
    input_file = sys.argv[2]
    n_alphas = sys.argv[3]

    constants = [cn.Constant(f"v_{i}") for i in range(int(domain))]

    nums = [int(n) for n in n_alphas.split(",")]
    cnf_parser = CnfParser()
    cnf_parser.read_file(input_file)

    formulas = cnf_parser.formulas
    if len(nums) != len(formulas):
        raise ValueError(f"Number of groundings is different from number of formulas: {len(nums)} groundings vs "
                         f"{len(formulas)} formulas.")

    for num, form in zip(nums, formulas):
        print(f"{num}: {str(form)}")

    print(nums)

    pw = PossibleWorld(constants, formulas, [])
    pw.satisfiable(nums)
