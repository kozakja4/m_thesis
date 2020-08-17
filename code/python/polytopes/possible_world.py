import gurobipy as g
import itertools as itt

from typing import List, Dict

from clauses.cnf import CNF, Atom, Constant


class PossibleWorld:

    def __init__(self, domain: List[Constant], clauses: List[CNF], constraints: List[Atom]):
        self.domain = domain
        self.clauses = clauses
        self.constraints = constraints

    def satisfiable(self, satisfaction_count: List[int]) -> (bool, Dict[Atom, bool]):
        # create ILP
        # returns satisfiability + assignment?
        mod = g.Model()
        mod = mod.feasibility()
        # find all atoms in CNFs
        # create opt. variable for all possible assignments of constants to variables for each atom...
        opt_variable_mapping = {}  # key (predicate, [domain elements])
        a_count = 0
        d_count = 0
        grand_d = []
        grand_a = []
        for i, cnf in enumerate(self.clauses):
            target_satisfaction_count = satisfaction_count[i]
            distinct_vars = cnf.get_distinct_vars()
            ds = []
            #print(cnf)
            for assignment in itt.permutations(self.domain, len(distinct_vars)):
                assgnmt_dir = {a: b for a, b in zip(distinct_vars, assignment)}
                # D indicates that whole formula is satisfied in current assignment
                # D = {min A}  (see below)
                D = mod.addVar(lb=0.0, name="D_{}".format(d_count))
                grand_d.append(D)
                d_count += 1
                ds.append(D)
                avars = []
                #print("Start")
                for clause in cnf.clauses:
                    # A indicates that a clause is satisfied in current assignment
                    # A = max{variables for each literal}
                    A = mod.addVar(0.0, 1.0, name="A_{}".format(a_count))
                    avars.append(A)
                    grand_a.append(A)
                    a_count += 1
                    literal_vars_pos = []
                    literal_vars_neg = []
                    neg_count = 0
                    for literal in clause.literals:
                        a_code = literal.atom.assignment_name(assgnmt_dir)
                        #print(a_code)
                        if a_code in opt_variable_mapping:
                            opt_var = opt_variable_mapping[a_code]
                            #print("Found")
                        else:
                            opt_var = mod.addVar(vtype=g.GRB.BINARY, name=a_code)
                            opt_variable_mapping[a_code] = opt_var
                            #print("Not found")
                        if literal.positive:
                            literal_vars_pos.append(opt_var)
                            mod.addConstr(A >= opt_var)
                        else:
                            literal_vars_neg.append(opt_var)
                            mod.addConstr(A >= opt_var - 1)
                            neg_count += 1
                    mod.addConstr(A <= g.quicksum(literal_vars_pos) - g.quicksum(literal_vars_neg) + neg_count)
                    mod.addConstr(D <= A)
                mod.addConstr(D >= g.quicksum(avars) - len(avars) + 1)
            mod.addConstr(g.quicksum(ds), g.GRB.EQUAL, target_satisfaction_count)
        # add always holding ground truths:
        for crn in self.constraints:
            name = crn.assignment_name({})
            optvar = opt_variable_mapping[name]
            mod.addConstr(optvar, g.GRB.EQUAL, 1)
        mod.write("show.lp")
        mod.setObjective(0)
        mod.optimize()
        if mod.status != g.GRB.INFEASIBLE:
            print("Constraints are FEASIBLE")
            if len(self.domain) < 7:
                for v in opt_variable_mapping.values():
                    print(v.x, v.varname)
                # for v in grand_d:
                #     print(v.x, v.varname)
                # for v in grand_a:
                #     print(v.x, v.varname)
        else:
            print("Constraints are INFEASIBLE")
        return not g.GRB.INFEASIBLE, {}

    def create_assignments(self, opt_var_map: Dict, var_map: Dict):
        pass
