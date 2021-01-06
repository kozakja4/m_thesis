import numpy as np

from unittest import TestCase

from aistats.utils import calculate_normal, cross, normalize_vector


class TestUtils(TestCase):

    def test_normalize_vector(self):
        test_1 = np.array([1, 2, 3, 4, 5])
        out = normalize_vector(test_1)
        self.assertTrue(self.arr_eq(test_1, out))
        test_2 = np.array([-1, 2, 3, 4, 5])
        out = normalize_vector(test_2)
        self.assertTrue(self.arr_eq(np.array([1, -2, -3, -4, -5]), out))
        test_3 = np.array([0, 2, 4, 6])
        out = normalize_vector(test_3)
        self.assertTrue(self.arr_eq(np.array([0, 1, 2, 3]), out))
        test_4 = np.array([0, 0, -2, 0, -4, 10])
        out = normalize_vector(test_4)
        self.assertTrue(self.arr_eq(np.array([0, 0, 1, 0, 2, -5]), out))
        test_no_crash = np.array([0, 0, 0])
        out = normalize_vector(test_no_crash)
        self.assertTrue(self.arr_eq(np.array([0, 0, 0]), out))

    def test_calculate_normal_2d(self):
        test_1 = np.array([1, 2])
        out = calculate_normal(test_1)
        self.assertTrue((out != 0).any)
        self.assertEqual(np.dot(test_1, out), 0)
        test_2 = np.array([1000, -333])
        out = calculate_normal(test_2)
        self.assertTrue((out != 0).any)
        self.assertEqual(np.dot(test_2, out), 0)
        test_3 = np.array([[1, 20]])
        out = calculate_normal(test_3)
        self.assertTrue((out != 0).any)
        self.assertEqual(np.dot(test_3, out), 0)

    def test_calculate_normal_3d(self):
        test_1 = np.array([[1, 0, 0], [0, 1, 0]])
        out = calculate_normal(test_1)
        self.assertTrue((out != 0).any)
        self.assertTrue(self.arr_eq(np.matmul(test_1, out.T), np.array([0, 0])))
        test_2 = np.array([[3, 9, 1], [-8, 22, 12]])
        out = calculate_normal(test_2)
        self.assertTrue((out != 0).any)
        self.assertTrue(self.arr_eq(np.matmul(test_2, out.T), np.array([0, 0])))

    def test_cross(self):
        test_1 = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ])
        out = cross(test_1)
        self.assertTrue(out.max() > 0.1 or out.min() < 0.1)
        self.assertTrue(self.arr_eq(np.matmul(test_1, out.T), np.array([0, 0, 0])))
        test_2 = np.array([
            [1, 5, 2, -9, -3],
            [2, 1, 5,  2, -8],
            [0, 7, 1,  8,  1],
            [0, 0, 3, -9,  0]
        ])
        out = cross(test_2)
        self.assertTrue(out.max() > 0.1 or out.min() < 0.1)
        self.assertTrue(np.allclose(np.array([0, 0, 0, 0]), np.matmul(test_2, out.T), 1E-9))

    @staticmethod
    def arr_eq(a1, a2):
        return np.alltrue(a1 == a2)
