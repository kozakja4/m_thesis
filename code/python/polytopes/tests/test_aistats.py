from unittest import TestCase
from unittest.mock import Mock, MagicMock

from aistats.aistats import AiStatsRmpSolver
from clauses.cnf import WeightedFormula, MLN, Predicate


class TestAiStatsRmpSolver(TestCase):

    def test_init(self):
        mln = self.create_mock_mln()
        rmp = AiStatsRmpSolver(mln, 10)
        self.assertEqual(rmp.domain_size, 10)
        self.assertEqual(rmp.limits, [10, 100, 1000])
        self.assertAlmostEqual(rmp.omega_size_log, 13.8155106, delta=1E-6)
        self.assertEqual(rmp.predicates, {Predicate("A", 1), Predicate("B", 1), Predicate("C", 2), Predicate("D", 3)})

    def create_mock_mln(self):
        formula1 = MagicMock()
        formula1.get_distinct_vars = Mock(return_value=["X"])
        formula1.get_distinct_predicates = Mock(return_value={Predicate("A", 1), Predicate("B", 1)})
        formula2 = MagicMock()
        formula2.get_distinct_vars = Mock(return_value=["X", "Y"])
        formula2.get_distinct_predicates = Mock(return_value={Predicate("A", 1), Predicate("C", 2)})
        formula3 = MagicMock()
        formula3.get_distinct_vars = Mock(return_value=["X", "Y", "Z"])
        formula3.get_distinct_predicates = Mock(return_value={Predicate("B", 1), Predicate("C", 2), Predicate("D", 3)})
        mln = MLN([WeightedFormula(1, formula1), WeightedFormula(1, formula2), WeightedFormula(1, formula3)])
        return mln
