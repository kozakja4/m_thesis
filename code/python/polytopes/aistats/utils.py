import numpy as np


def calculate_normal(points: np.ndarray) -> np.ndarray:
    """
    Calculates normal vector for a set of linearly independent points passed as (n-1) x n matrix:
    :param points: (n-1) x n matrix (n >= 2)
    :return: vector perpendicular to all rows of the matrix
    """
    if points.shape == (2,):
        return np.array([points[1], -points[0]])  # 2D - switch values and multiply one of them by -1
    elif points.shape == (1, 2):
        return np.array([points[0, 1], -points[0, 0]])  # dtto
    elif points.ndim == 2:
        if points.shape[1] > 3:
            return cross(points)  # 4D+ - generalized cross product
        elif points.shape[1] == 3:
            return np.cross(points[0, :], points[1, :])  # 3D - standard cross product
    raise ValueError(f"Unsupported input shape, must be ((n-1) x n), but was {points.shape}")


def cross(points: np.ndarray) -> np.ndarray:  # (n-1) x n
    out = np.empty(points.shape[1])
    bix = np.ones(points.shape[1], dtype=np.bool_)
    for idx in range(points.shape[1]):
        bix[idx] = 0
        no_col = points[:, bix]
        sign = 1 if idx % 2 == 1 else -1
        out[idx] = sign * np.linalg.det(no_col)
        bix[idx] = 1
    return out


def normalize_vector(v) -> np.ndarray:
    """
    Normalizes input vector so the greatest common divisor of its elements is 1 and first non-zero element is
    positive
    :param v: 1-D numpy array
    :return: numpy array casted to int64 type, gcd of all elements is 1 and first non-zero index is positive
    """
    rounded = v.round().astype(np.int64)
    nzi = (rounded != 0).argmax(axis=0)  # find index of first non-zero element
    r_gcd = np.sign(rounded[nzi]) * np.gcd.reduce(rounded)
    if r_gcd == 0:
        return rounded
    else:
        return np.floor_divide(rounded, r_gcd)
