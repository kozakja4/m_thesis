from unittest import TestCase

from aistats.enumerator.naive_enumerator import CenterEnumerator

import numpy as np


class TestCenterEnumerator(TestCase):

    def test_beginning_points(self):
        ce = CenterEnumerator([10, 3, 4, 5])
        for bp in ce.beginning_points():
            print(bp)
            non_zero_bps = -2 * np.sign(bp) + 1
            print(non_zero_bps)
