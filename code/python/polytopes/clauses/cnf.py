from typing import List, Dict


class Term:

    def __init__(self, name: str):
        self.name = name


class Constant(Term):

    def __init__(self, name: str):
        super().__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Constant(name='{}')".format(self.name)

    def __eq__(self, other):
        if isinstance(other, Constant):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)


class Variable(Term):

    def __init__(self, name: str):
        super().__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Variable(name='{}')".format(self.name)

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)


class Predicate:

    def __init__(self, name: str, arity: int):
        self.name = name
        self.arity = arity

    def __str__(self):
        return "{name}/{arity}".format(name=self.name, arity=self.arity)

    def __repr__(self):
        return "Predicate(name={name}, arity={arity})".format(name=self.name, arity=self.arity)

    def __eq__(self, other):
        if isinstance(other, Predicate):
            return self.arity == other.arity and self.name == other.name
        return False


class Atom:
    # predicate with bound variables

    def __init__(self, predicate: Predicate, variables: List[Term]):
        self.predicate = predicate
        self.variables = variables
        self.renamed_vars, self.distinct_vars, self.distinct_const = self._rename_vars()
        assert(len(variables) == self.predicate.arity)

    def renamed_str(self) -> str:
        vlist = ",".join(v.name for v in self.renamed_vars)
        return "{name}({vlist})".format(name=self.predicate.name, vlist=vlist)

    def assignment_name(self, assignment: Dict[str, str]) -> str:
        vlist = ",".join(assignment[v.name].name if isinstance(v, Variable) else v.name for v in self.variables)
        return "{name}({vlist})".format(name=self.predicate.name, vlist=vlist)

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
        vlist = ",".join(v.name for v in self.variables)
        return "{name}({vlist})".format(name=self.predicate.name, vlist=vlist)

    def __repr__(self):
        return "Atom(predicate={name}, variables={vlist}, renamed={ren}))".format(name=self.predicate.name,
                                                                                  vlist=self.variables,
                                                                                  ren=self.renamed_vars)

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

    def __init__(self, atom: Atom, positive: bool=True):
        self.atom = atom
        self.positive = positive

    def __str__(self):
        if self.positive:
            return str(self.atom)
        else:
            return "~{atom}".format(atom=self.atom)

    def __repr__(self):
        return "Literal(positive={pos}, atom={atom})".format(pos=self.positive, atom=repr(self.atom))

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
        return " | ".join(str(lit) for lit in self.literals)

    def __repr__(self):
        return "Clause(literals={lits})".format(lits=self.literals)

    def __eq__(self, other):
        if isinstance(other, Literal):
            for lit in self.literals:
                if lit not in other.literals:
                    return False
            return True
        return False


class CNF:
    #  conjunction of clauses

    def __init__(self, clauses: List[Clause]):
        self.clauses = clauses

    def __str__(self):
        return " & ".join("({})".format(lit) for lit in self.clauses)

    def __repr__(self):
        return "Clause(literals={lits})".format(lits=self.clauses)

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
