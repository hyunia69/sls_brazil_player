"""Quaternion operations using (w, x, y, z) convention.

All quaternions are represented as numpy arrays of shape (4,) with
the scalar component first: [w, x, y, z].

This convention matches the SLMB binary format where w >= 0 is required
for compact encoding.
"""

import numpy as np


_EPSILON = 1e-10


def normalize(q: np.ndarray) -> np.ndarray:
    """Normalize quaternion to unit length.

    Args:
        q: Quaternion array [w, x, y, z].

    Returns:
        Unit quaternion. If the input norm is near zero, returns the
        identity quaternion [1, 0, 0, 0].
    """
    norm = np.linalg.norm(q)
    if norm < _EPSILON:
        return np.array([1.0, 0.0, 0.0, 0.0])
    return q / norm


def multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Hamilton product q1 * q2.

    Args:
        q1: Left quaternion [w, x, y, z].
        q2: Right quaternion [w, x, y, z].

    Returns:
        Product quaternion [w, x, y, z].
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def conjugate(q: np.ndarray) -> np.ndarray:
    """Return the conjugate of a quaternion.

    Args:
        q: Quaternion [w, x, y, z].

    Returns:
        Conjugate [w, -x, -y, -z].
    """
    return np.array([q[0], -q[1], -q[2], -q[3]])


def inverse(q: np.ndarray) -> np.ndarray:
    """Return the inverse of a unit quaternion.

    For unit quaternions the inverse equals the conjugate. The input
    is normalized first to guard against accumulated drift.

    Args:
        q: Quaternion [w, x, y, z].

    Returns:
        Inverse quaternion [w, -x, -y, -z] (normalized).
    """
    return conjugate(normalize(q))


def ensure_positive_w(q: np.ndarray) -> np.ndarray:
    """Ensure w >= 0 by negating all components if necessary.

    SLMB binary format requires the scalar part to be non-negative so
    that only three components need to be stored.

    Args:
        q: Quaternion [w, x, y, z].

    Returns:
        Equivalent quaternion with w >= 0.
    """
    if q[0] < 0.0:
        return -q
    return q.copy()


def slerp(q1: np.ndarray, q2: np.ndarray, t: float) -> np.ndarray:
    """Spherical linear interpolation between two quaternions.

    Automatically takes the shortest path on the unit sphere by
    checking the sign of the dot product.

    Args:
        q1: Start quaternion [w, x, y, z].
        q2: End quaternion [w, x, y, z].
        t: Interpolation parameter in [0, 1].

    Returns:
        Interpolated unit quaternion [w, x, y, z].
    """
    q1 = normalize(q1)
    q2 = normalize(q2)

    dot = np.dot(q1, q2)

    # Take the shortest path.
    if dot < 0.0:
        q2 = -q2
        dot = -dot

    # Clamp to valid acos range.
    dot = np.clip(dot, -1.0, 1.0)

    # Fall back to linear interpolation when quaternions are very close
    # to avoid division by a near-zero sine.
    if dot > 1.0 - _EPSILON:
        result = q1 + t * (q2 - q1)
        return normalize(result)

    theta = np.arccos(dot)
    sin_theta = np.sin(theta)

    w1 = np.sin((1.0 - t) * theta) / sin_theta
    w2 = np.sin(t * theta) / sin_theta

    return normalize(w1 * q1 + w2 * q2)


def from_unity_xyzw(xyzw: list) -> np.ndarray:
    """Convert Unity quaternion format to internal format.

    Unity stores quaternions as [x, y, z, w]. This function reorders
    them to the internal [w, x, y, z] convention.

    Args:
        xyzw: Unity-ordered quaternion [x, y, z, w] as a list or
              array-like of length 4.

    Returns:
        Quaternion array [w, x, y, z].
    """
    x, y, z, w = xyzw
    return np.array([w, x, y, z])
