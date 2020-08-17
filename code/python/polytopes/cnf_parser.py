import re
import clauses.cnf as ccnf


class CnfParser:

    def __init__(self):
        self.predicates = {}
        self.formulas = []

    def read_file(self, input_file: str):
        # INPUT FORMAT:
        # CNF, or declared as OR, and as AND, negation as NOT, expecting function-free CNF
        # these are case-sensitive keywords, don't name any predicate or variable exactly like this
        # also it is straight-forward and targeted on CNF
        # AND HAS PRECEDENCE OVER OR THERE! also bracketing of clauses is also ignored...
        # A(X) OR B(X) AND C(X) -> clauses A(X) OR B(X), C(X)
        # A(X) OR (B(X) AND C(X)) -> same as above
        with open(input_file) as file:
            for line in file:
                self.read_cnf(line)

    def read_cnf(self, cnf: str) -> None:
        print(f"Parsing CNF: {cnf}")
        clauses = re.split(r"\s*AND\s+", cnf)
        cnf_known_vars = {}
        cnf_clauses = []
        for clause in clauses:
            literals = re.split(r"\s*OR\s+", clause)
            cnf_literals = []
            for literal in literals:
                while literal.startswith("("):
                    literal = literal[1:]
                neg_match = re.match(r"^NOT\s+", literal)
                positive = neg_match is None
                atom = literal
                if not positive:
                    atom = literal[neg_match.end():]
                split_atom = re.split(r"\(", atom)
                if len(split_atom) != 2:
                    raise ValueError(f"More than one left bracket encountered in {atom}")
                atom_name = split_atom[0]
                variables = split_atom[1]
                vars_here = []
                for v in re.split(r"\s*,\s*", variables):
                    while v.endswith(")"):
                        v = v[:-1]
                    if v not in cnf_known_vars:
                        cnf_known_vars[v] = ccnf.Variable(v)
                    vars_here.append(cnf_known_vars[v])
                if atom_name not in self.predicates:
                    self.predicates[atom_name] = ccnf.Predicate(atom_name, len(vars_here))
                cnf_predicate = self.predicates[atom_name]
                if cnf_predicate.arity != len(vars_here):
                    raise ValueError(f"{cnf_predicate} is already defined with arity {cnf_predicate.arity} but "
                                     f"now the arity is {len(vars_here)}")
                cnf_atom = ccnf.Atom(cnf_predicate, vars_here)
                cnf_literal = ccnf.Literal(cnf_atom, positive)
                cnf_literals.append(cnf_literal)
            cnf_clause = ccnf.Clause(cnf_literals)
            cnf_clauses.append(cnf_clause)
        self.formulas.append(ccnf.CNF(cnf_clauses))


if __name__ == "__main__":
    parser = CnfParser()
    parser.read_cnf("A(X,Y) OR B(Y,X) OR A(Y,Z)")
    parser.read_cnf("A(X,Y) AND B(Y,X) AND NOT A(Y,Z)")
    parser.read_cnf("A(X,Y) AND (B(Y,X) OR A(Y,Z))")
    parser.read_cnf("A(X,Y)")
    parser.read_cnf("A(X,Y) OR B(X,Z)")
    parser.read_cnf("Z(Z,Z) AND NOT B(X,Z)")
    print(parser.predicates)
    print(parser.formulas)
    parser.read_cnf("Z(Z,Z,Z)")

