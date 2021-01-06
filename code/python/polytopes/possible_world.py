import gurobipy as g
import itertools as itt

from typing import List, Dict, Tuple

from clauses.cnf import Formula, Atom, Constant, WeightedFormula


class PossibleWorld:

    def __init__(self, domain: List[Constant], formulas: List[WeightedFormula], constraints: List[Atom], reflexive: bool = True):
        self.domain = domain
        self.formulas = formulas
        self.constraints = constraints
        self.reflexive = reflexive
        self.directive_map = {'eq': g.GRB.EQUAL, 'ge': g.GRB.GREATER_EQUAL, 'le': g.GRB.LESS_EQUAL}

    def satisfiable(self, satisfaction_count: Dict[int, Tuple[int, str]], write: bool = False,
                    write_name: str = "model.lp", opt_var_idx: int = -1, sense = g.GRB.MINIMIZE) \
            -> (bool, List[int]):
        """

        :param satisfaction_count: dictionary - idx to formulas, (number of satisfactions, mode),
        mode - 'eq', 'gt, 'lt'
        :param write: write model to file
        :param write_name: name of file to write
        :param opt_var_idx: index of formula which should be maximized/minimized
        :return: tuple (feasibility, satisfaction count list for each formula - i. e. a possible world in
        specified boundaries)
        """
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
        formulas_satisfaction_count = []
        for i, wf in enumerate(self.formulas):  # Right now - every formula contains one clause
            cnf = wf.formula
            target_satisfaction_count, target_mode = satisfaction_count[i]
            distinct_vars = cnf.get_distinct_vars()
            ds = []
            f_sat_count = mod.addVar(lb=0.0, name=f"F_{i}")
            formulas_satisfaction_count.append(f_sat_count)
            #print(cnf)
            assignment_generator = itt.permutations(self.domain, len(distinct_vars))
            if self.reflexive:
                assignment_generator = itt.product(self.domain, repeat=len(distinct_vars))
            for assignment in assignment_generator:
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
                    A = mod.addVar(lb=0.0, ub=1.0, name="A_{}".format(a_count))
                    avars.append(A)
                    grand_a.append(A)
                    a_count += 1
                    cl_literals = []
                    for literal in clause.literals:
                        pos_code = literal.atom.assignment_name(assgnmt_dir)
                        neg_code = f"~{pos_code}"
                        a_code = pos_code if literal.positive else neg_code
                        if a_code in opt_variable_mapping:
                            opt_var = opt_variable_mapping[a_code]
                            #print("Found")
                        else:
                            p_var = mod.addVar(vtype=g.GRB.BINARY, name=pos_code)
                            n_var = mod.addVar(vtype=g.GRB.BINARY, name=neg_code)
                            mod.addConstr(1 - p_var == n_var)
                            opt_variable_mapping[pos_code] = p_var
                            opt_variable_mapping[neg_code] = n_var
                            opt_var = p_var if literal.positive else n_var
                            #print("Not found")
                        cl_literals.append(opt_var)
                    mod.addGenConstrMax(A, cl_literals, 0.0)
                mod.addGenConstrMin(D, avars, 1.0)
            mod.addConstr(g.quicksum(ds), self.directive_map[target_mode], target_satisfaction_count)
            mod.addConstr(f_sat_count == g.quicksum(ds))
        # add always holding ground truths:
        for crn in self.constraints:  # obsolete
            name = crn.assignment_name({})
            optvar = opt_variable_mapping[name]
            mod.addConstr(optvar, g.GRB.EQUAL, 1)
        if write:
            mod.write(write_name)
        if opt_var_idx > 0:
            mod.setObjective(formulas_satisfaction_count[opt_var_idx], sense)
        else:
            mod.setObjective(0)
        mod.optimize()
        if mod.status != g.GRB.INFEASIBLE:
            print("Constraints are FEASIBLE")
            #if len(self.domain) < 7:
            #    for v in opt_variable_mapping.values():
            #        print(v.x, v.varname)
                # for v in grand_d:
                #     print(v.x, v.varname)
                # for v in grand_a:
                #     print(v.x, v.varname)
        else:
            print("Constraints are INFEASIBLE")
        out_list = [] if mod.status == g.GRB.INFEASIBLE else [v.x for v in formulas_satisfaction_count]
        return mod.status != g.GRB.INFEASIBLE, out_list

    def create_assignments(self, opt_var_map: Dict, var_map: Dict):
        pass

    def furthest_from_hull(self, qhull, var_limits, facet_eq,
                           write: bool = False, write_file: str = "pw.lp"):
        """
        The method should find the possible world satisfying the formulas furthest from the convex hull.
        Dtance from a point to the polytope is approximated as
        :param qhull:
        :param var_limits:
        :param write:
        :param write_file:
        :return:
        """
        # create ILP
        # returns satisfiability + point + objective
        mod = g.Model()
        # find all atoms in CNFs
        # create opt. variable for all possible assignments of constants to variables for each atom...
        opt_variable_mapping = {}  # key (predicate, [domain elements])
        greatest_distance = mod.addVar(lb=0.0, name="maxDist")
        tar_vars = []
        a_count = 0
        d_count = 0
        grand_d = []
        grand_a = []
        for i, wf in enumerate(self.formulas):  # Right now - every formula contains one clause
            cnf = wf.formula
            distinct_vars = cnf.get_distinct_vars()
            tar_var = mod.addVar(lb=0, ub=var_limits[i], vtype=g.GRB.INTEGER, name=f"Xf_{i}")
            tar_vars.append(tar_var)
            ds = []
            # print(cnf)
            assignment_generator = itt.permutations(self.domain, len(distinct_vars))
            if self.reflexive:
                assignment_generator = itt.product(self.domain, repeat=len(distinct_vars))
            for assignment in assignment_generator:
                assgnmt_dir = {a: b for a, b in zip(distinct_vars, assignment)}
                # D indicates that whole formula is satisfied in current assignment
                # D = {min A}  (see below)
                D = mod.addVar(lb=0.0, ub=1.0, name="D_{}".format(d_count))
                grand_d.append(D)
                d_count += 1
                ds.append(D)
                avars = []
                # print("Start")
                for clause in cnf.clauses:
                    # A indicates that a clause is satisfied in current assignment
                    # A = max{variables for each literal}
                    A = mod.addVar(lb=0.0, ub=1.0, name="A_{}".format(a_count))
                    avars.append(A)
                    grand_a.append(A)
                    a_count += 1
                    cl_literals = []
                    for literal in clause.literals:
                        pos_code = literal.atom.assignment_name(assgnmt_dir)
                        neg_code = f"~{pos_code}"
                        a_code = pos_code if literal.positive else neg_code
                        if a_code in opt_variable_mapping:
                            opt_var = opt_variable_mapping[a_code]
                            # print("Found")
                        else:
                            p_var = mod.addVar(vtype=g.GRB.BINARY, name=pos_code)
                            n_var = mod.addVar(vtype=g.GRB.BINARY, name=neg_code)
                            mod.addConstr(1 - p_var == n_var)
                            opt_variable_mapping[pos_code] = p_var
                            opt_variable_mapping[neg_code] = n_var
                            opt_var = p_var if literal.positive else n_var
                            # print("Not found")
                        cl_literals.append(opt_var)
                    mod.addGenConstrMax(A, cl_literals, 0.0)
                mod.addGenConstrMin(D, avars, 1.0)
            mod.addConstr(g.quicksum(ds) == tar_var)


        poly_lines, columns = qhull.equations.shape
        dist_vars = []
        indicators = []
        # Selected inequality must not hold
        #for ix in range(poly_lines):
        # Use inequality for chosen edge
        # qhull uses Ax + b < 0
        line = facet_eq[0:columns-1]
        b = facet_eq[columns-1]
        mod.addConstr(g.quicksum([w * v for w, v in zip(line, tar_vars)]) + b >= 0)  # TODO >= 1 but we need to rescale b  # inside polytope is <=
        # Find max L2 distance
        dst = mod.addVar(name="pd")
        mod.addConstr(g.quicksum([w * v for w, v in zip(line, tar_vars)]) + b == dst)
        mod.addConstr(greatest_distance == g.abs_(dst))
        mod.setObjective(greatest_distance, g.GRB.MAXIMIZE)
        if write:
            mod.write(write_file)
        mod.optimize()

        if mod.status == g.GRB.OPTIMAL:  # TODO not in INFEASIBLE, UNBOUNDED,
            print(mod.status)
            print("Found optimal solution")
            # if len(self.domain) < 7:
            #    for v in opt_variable_mapping.values():
            #        print(v.x, v.varname)
            # for v in grand_d:
            #     print(v.x, v.varname)
            # for v in grand_a:
            #     print(v.x, v.varname)
        else:
            print("Constraints are INFEASIBLE")
            print("inf or unb", g.GRB.INF_OR_UNBD == mod.status)
            print("unb", g.GRB.UNBOUNDED == mod.status)
            print("infis", g.GRB.INFEASIBLE == mod.status)

        out_list = [] if mod.status != g.GRB.OPTIMAL else [v.x for v in tar_vars]
        gdx = greatest_distance.x if mod.status == g.GRB.OPTIMAL else -1
        return mod.status == g.GRB.OPTIMAL, out_list, gdx
