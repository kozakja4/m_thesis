from functools import total_ordering
from typing import List, Dict, Set


class Term:

    def __init__(self, name: str):
        self.name = name


@total_ordering
class Constant(Term):

    def __init__(self, name: str):
        super().__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Constant(name='{self.name}')"

    def __eq__(self, other):
        if isinstance(other, Constant):
            return self.name == other.name
        return False

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)


@total_ordering
class Variable(Term):

    def __init__(self, name: str):
        super().__init__(name)

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return f"Variable(name='{self.name}')"

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name
        return False

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)


@total_ordering
class Predicate:

    def __init__(self, name: str, arity: int):
        self.name = name
        self.arity = arity

    def __str__(self):
        return f"{self.name}/{self.arity}"

    def __repr__(self):
        return f"Predicate(name={self.name}, arity={self.arity})"

    def __eq__(self, other):
        if isinstance(other, Predicate):
            return self.arity == other.arity and self.name == other.name
        return False

    def __lt__(self, other):
        return (self.name, self.arity) < (other.name, other.arity)

    def __hash__(self):
        return hash((self.name, self.arity))

    def with_domain(self, domain: str) -> str:
        return f"{self.name}({','.join(domain for _ in range(self.arity))})"


class Atom:
    # predicate with bound variables

    def __init__(self, predicate: Predicate, variables: List[Term]):
        self.predicate = predicate
        self.variables = variables
        self.renamed_vars, self.distinct_vars, self.distinct_const = self._rename_vars()
        assert(len(variables) == self.predicate.arity)

    def renamed_str(self) -> str:
        vlist = ",".join(v.name for v in self.renamed_vars)
        return f"{self.predicate.name}({vlist})"

    def assignment_name(self, assignment: Dict[str, str]) -> str:
        vlist = ",".join(assignment[v.name].name if isinstance(v, Variable) else v.name for v in self.variables)
        return f"{self.predicate.name}({vlist})"

    def _rename_vars(self) -> (List[Term], int, int):
        mapping = {}
        i, dv, dc = 0, 0, 0
        nvlist = []
        for v in self.variables:
            if v not in mapping:
                if isinstance(v, Variable):
                    mapping[v] = Variable("X_{ord}".format(ord=dv))
                    dv += 1
                elif isinstance(v, Constant):
                    mapping[v] = v
                    dc += 1
                else:
                    raise Exception("Non-term object in atom.")
            nvlist.append(mapping[v])
        return nvlist, dv, dc

    def __str__(self):
        vlist = ",".join(v.name.lower() for v in self.variables)
        return f"{self.predicate.name}({vlist})"

    def __repr__(self):
        return f"Atom(predicate={self.predicate.name}, variables={self.variables}, renamed={self.renamed_vars}))"

    def __eq__(self, other):
        if isinstance(other, Atom):
            if self.predicate != other.predicate:
                return False
            for i, term in enumerate(self.renamed_vars):
                if term != other.renamed_vars[i]:
                    return False
            return True
        return False

    def get_vars(self) -> List[str]:
        dist = set()
        for variable in self.variables:
            dist.add(variable.name)
        return list(dist)


class Literal:
    #  atom or its negation

    def __init__(self, atom: Atom, positive: bool = True):
        self.atom = atom
        self.positive = positive

    def __str__(self):
        if self.positive:
            return str(self.atom)
        else:
            return f"!{self.atom}"

    def __repr__(self):
        return f"Literal(positive={self.positive}, atom={repr(self.atom)})"

    def __eq__(self, other):
        if isinstance(other, Literal):
            return self.positive == other.positive and self.atom == other.atom
        return False

    def get_vars(self) -> List[str]:
        return self.atom.get_vars()


class Clause:
    #  disjunction of literals

    def __init__(self, literals: List[Literal]):
        self.literals = literals

    def __str__(self):
        return " v ".join(f"{lit}" for lit in self.literals)

    def __repr__(self):
        return f"Clause(literals={self.literals})"

    def __eq__(self, other):
        if isinstance(other, Clause):
            for lit in self.literals:
                if lit not in other.literals:
                    return False
            return True
        return False


# TODO Currently only works for CNF
class Formula:

    def __init__(self, clauses: List[Clause]):
        self.clauses = clauses  # TODO

    def __str__(self):
        return " ^ ".join(f"({clause})" for clause in self.clauses)

    def __repr__(self):
        return f"Formula[CNF](clauses={self.clauses})"

    def get_distinct_predicates(self) -> Set[Predicate]:
        p_set = set()
        for clause in self.clauses:
            for literal in clause.literals:
                p_set.add(literal.atom.predicate)
        return p_set

    def get_atoms(self) -> Dict[str, Atom]:
        p_dict = {}
        for clause in self.clauses:
            for literal in clause.literals:
                p_dict[str(literal.atom)] = literal.atom
        return p_dict

    def get_distinct_atoms(self) -> Dict[str, Atom]:
        p_dict = {}
        for clause in self.clauses:
            for literal in clause.literals:
                p_dict[literal.atom.renamed_str()] = literal.atom
        return p_dict

    def get_distinct_vars(self) -> List[str]:
        distinct_vars = set()
        for clause in self.clauses:
            for literal in clause.literals:
                for variable in literal.get_vars():
                    distinct_vars.add(variable)
        return list(distinct_vars)


class CNF(Formula):
    #  conjunction of clauses

    def __init__(self, clauses: List[Clause]):
        super().__init__(clauses)

    def __str__(self):
        return " ^ ".join(f"({clause})" for clause in self.clauses)

    def __repr__(self):
        return f"CNF(clauses={self.clauses})"


class WeightedFormula:

    def __init__(self, weight: float, formula: Formula):
        self.weight = weight
        self.formula = formula

    def __str__(self):
        return f"{self.weight:.5g}: {self.formula}"

    def __repr__(self):
        return f"WeightedFormula(weight:{self.weight},formula:{repr(self.formula)})"

    def __eq__(self, other):
        if isinstance(other, WeightedFormula):
            return self.weight == other.weight and self.formula == other.formula
        return False


class MLN:

    def __init__(self, weighted_formulas: List[WeightedFormula]):
        self.weighted_formulas = weighted_formulas

    def __str__(self):
        wf_list = "\n".join(f"{fml}" for fml in self.weighted_formulas)
        return f"MLN:\n{wf_list}"

    def __repr__(self):
        return f"MLN({self.weighted_formulas})"
