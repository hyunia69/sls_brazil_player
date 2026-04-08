"""Euler-to-quaternion and quaternion-to-Euler conversions per OG-06 D.2.3.

These functions implement the exact algorithms from the SBTVD OG-06
operational guideline for converting between Euler angle representations
and quaternion representations used in BVH and SLMB formats.

Rotation axis vectors (RX, RY, RZ) are the column vectors of the joint's
rest-pose rotation matrix. For joints at identity orientation these are
simply the standard basis vectors (1,0,0), (0,1,0), (0,0,1).
"""

import math
from typing import Tuple

import numpy as np

from . import quaternion as qops


# -- Helpers -----------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def wrap_to_degrees(radians: float) -> float:
    """Convert radians to degrees and wrap to the half-open interval (-180, 180].

    Args:
        radians: Angle in radians.

    Returns:
        Angle in degrees within (-180, 180].
    """
    deg = math.degrees(radians)
    # Wrap into (-180, 180].
    deg = ((deg + 180.0) % 360.0) - 180.0
    if deg == -180.0:
        deg = 180.0
    return deg


# -- Rotation matrix to quaternion -------------------------------------------

def rotationaxis_to_quaternion(
    RX: Tuple[float, float, float],
    RY: Tuple[float, float, float],
    RZ: Tuple[float, float, float],
) -> np.ndarray:
    """Convert rotation-axis column vectors to a quaternion.

    The rotation matrix is assembled as ``R = [RX | RY | RZ]`` where each
    vector is a column.  The quaternion is derived from the standard
    Shepperd method for the dominant-diagonal case (trace > 0).

    OG-06 D.2.3 pseudocode::

        qw = sqrt(1 + Rx.x + Ry.y + Rz.z) / 2
        qx = (Ry.z - Rz.y) / (4*qw)
        qy = (Rz.x - Rx.z) / (4*qw)
        qz = (Rx.y - Ry.x) / (4*qw)

    The spec text literally writes ``qz = (Rx.y - Ry.z) / (4*qw)`` but
    the mathematically correct form for the standard rotation-matrix-to-
    quaternion conversion is ``qz = (R[1,0] - R[0,1]) / (4*qw)`` which
    in column-vector notation is ``(Rx.y - Ry.x)``.  We implement the
    standard (correct) form here.

    For near-singular cases (trace <= 0) the function falls back to the
    full Shepperd branch selection to remain numerically stable.

    Args:
        RX: First column of the rotation matrix (3-tuple).
        RY: Second column of the rotation matrix (3-tuple).
        RZ: Third column of the rotation matrix (3-tuple).

    Returns:
        Unit quaternion [w, x, y, z] as a numpy array.
    """
    # Diagonal elements of the rotation matrix.
    m00, m10, m20 = RX[0], RX[1], RX[2]
    m01, m11, m21 = RY[0], RY[1], RY[2]
    m02, m12, m22 = RZ[0], RZ[1], RZ[2]

    trace = m00 + m11 + m22

    if trace > 0.0:
        s = 2.0 * math.sqrt(trace + 1.0)
        qw = 0.25 * s
        qx = (m12 - m21) / s  # (Ry.z - Rz.y)
        qy = (m20 - m02) / s  # (Rz.x - Rx.z)
        qz = (m10 - m01) / s  # (Rx.y - Ry.x) -- standard form
    elif m00 > m11 and m00 > m22:
        s = 2.0 * math.sqrt(1.0 + m00 - m11 - m22)
        qw = (m12 - m21) / s
        qx = 0.25 * s
        qy = (m01 + m10) / s
        qz = (m02 + m20) / s
    elif m11 > m22:
        s = 2.0 * math.sqrt(1.0 + m11 - m00 - m22)
        qw = (m20 - m02) / s
        qx = (m01 + m10) / s
        qy = 0.25 * s
        qz = (m12 + m21) / s
    else:
        s = 2.0 * math.sqrt(1.0 + m22 - m00 - m11)
        qw = (m10 - m01) / s
        qx = (m02 + m20) / s
        qy = (m12 + m21) / s
        qz = 0.25 * s

    return qops.normalize(np.array([qw, qx, qy, qz]))


# -- Euler to quaternion -----------------------------------------------------

def euler2quaternion_xyz(
    Ex: float, Ey: float, Ez: float,
    RX: Tuple[float, float, float],
    RY: Tuple[float, float, float],
    RZ: Tuple[float, float, float],
) -> np.ndarray:
    """Convert SLMB Euler angles (XYZ order) to a quaternion.

    Implements OG-06 D.2.3 ``euler2quaternion`` for the SLMB rotation
    order X-Y-Z.

    Args:
        Ex: Rotation around X axis in **radians**.
        Ey: Rotation around Y axis in **radians**.
        Ez: Rotation around Z axis in **radians**.
        RX: Rest-pose X-axis column vector (3-tuple).
        RY: Rest-pose Y-axis column vector (3-tuple).
        RZ: Rest-pose Z-axis column vector (3-tuple).

    Returns:
        Unit quaternion [w, x, y, z].
    """
    Qr = rotationaxis_to_quaternion(RX, RY, RZ)

    cx, sx = math.cos(Ex / 2.0), math.sin(Ex / 2.0)
    cy, sy = math.cos(Ey / 2.0), math.sin(Ey / 2.0)
    cz, sz = math.cos(Ez / 2.0), math.sin(Ez / 2.0)

    Qex = np.array([cx, sx, 0.0, 0.0])
    Qey = np.array([cy, 0.0, sy, 0.0])
    Qez = np.array([cz, 0.0, 0.0, sz])

    # OG-06: result = Qez * Qey * Qex * Qr
    result = qops.multiply(Qez, qops.multiply(Qey, qops.multiply(Qex, Qr)))
    return qops.normalize(result)


def euler2quaternion_yxz(
    Ex: float, Ey: float, Ez: float,
    RX: Tuple[float, float, float],
    RY: Tuple[float, float, float],
    RZ: Tuple[float, float, float],
) -> np.ndarray:
    """Convert BVH Euler angles (YXZ order) to a quaternion.

    Implements OG-06 D.2.3 ``euler2quaternion`` for the BVH rotation
    order Y-X-Z.

    Args:
        Ex: Rotation around X axis in **radians**.
        Ey: Rotation around Y axis in **radians**.
        Ez: Rotation around Z axis in **radians**.
        RX: Rest-pose X-axis column vector (3-tuple).
        RY: Rest-pose Y-axis column vector (3-tuple).
        RZ: Rest-pose Z-axis column vector (3-tuple).

    Returns:
        Unit quaternion [w, x, y, z].
    """
    Qr = rotationaxis_to_quaternion(RX, RY, RZ)

    cx, sx = math.cos(Ex / 2.0), math.sin(Ex / 2.0)
    cy, sy = math.cos(Ey / 2.0), math.sin(Ey / 2.0)
    cz, sz = math.cos(Ez / 2.0), math.sin(Ez / 2.0)

    Qex = np.array([cx, sx, 0.0, 0.0])
    Qey = np.array([cy, 0.0, sy, 0.0])
    Qez = np.array([cz, 0.0, 0.0, sz])

    # OG-06: result = Qez * Qex * Qey * Qr
    result = qops.multiply(Qez, qops.multiply(Qex, qops.multiply(Qey, Qr)))
    return qops.normalize(result)


# -- Quaternion to Euler -----------------------------------------------------

def quaternion2euler_xyz(
    qw: float, qx: float, qy: float, qz: float,
    RX: Tuple[float, float, float],
    RY: Tuple[float, float, float],
    RZ: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Convert a quaternion to SLMB Euler angles (XYZ order).

    Implements OG-06 D.2.3 ``quaternion2euler`` for the SLMB rotation
    order X-Y-Z.  The returned angles are in **degrees**.

    Args:
        qw: Scalar part of the quaternion.
        qx: X component.
        qy: Y component.
        qz: Z component.
        RX: Rest-pose X-axis column vector (3-tuple).
        RY: Rest-pose Y-axis column vector (3-tuple).
        RZ: Rest-pose Z-axis column vector (3-tuple).

    Returns:
        Tuple (Ex, Ey, Ez) in degrees, each in (-180, 180].
    """
    # Robust euler extraction using rotation-matrix decomposition.
    # This avoids the numerical instability of the Q_rel approach
    # when Qr represents a large rotation (e.g. right-hand fingers
    # where the rotation axes define a ~180° rotated frame).
    #
    # OG-06 defines: Q = Qez * Qey * Qex * Qr
    #   where Qex/Qey/Qez are standard-axis rotations.
    # So: M_Q = Rz(Ez) * Ry(Ey) * Rx(Ex) * M_axes
    # Therefore: M_Q * M_axes^T = Rz(Ez) * Ry(Ey) * Rx(Ex)
    # Extract XYZ euler from M_Q * M_axes^T.

    Q = np.array([qw, qx, qy, qz])
    Q = qops.normalize(Q)
    w, x, y, z = Q

    # Quaternion to 3x3 rotation matrix
    M = np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w)],
        [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y)],
    ])

    # Axes matrix (columns are RX, RY, RZ) = M_axes
    A = np.array([[RX[0], RY[0], RZ[0]],
                  [RX[1], RY[1], RZ[1]],
                  [RX[2], RY[2], RZ[2]]])

    # Ml = M * A^T = Rz(Ez) * Ry(Ey) * Rx(Ex)
    Ml = M @ A.T

    # Extract XYZ euler angles: Ml[2][0] = -sin(Ey)
    sy = -Ml[2, 0]
    sy = _clamp(sy, -1.0, 1.0)
    Ey_rad = math.asin(sy)

    if abs(abs(sy) - 1.0) < 1e-8:
        # Gimbal lock: Ey = ±90°
        Ex_rad = math.atan2(-Ml[1, 2], Ml[1, 1])
        Ez_rad = 0.0
    else:
        # Normal case
        Ex_rad = math.atan2(Ml[2, 1], Ml[2, 2])
        Ez_rad = math.atan2(Ml[1, 0], Ml[0, 0])

    Ex = wrap_to_degrees(Ex_rad)
    Ey = wrap_to_degrees(Ey_rad)
    Ez = wrap_to_degrees(Ez_rad)
    return (Ex, Ey, Ez)


def quaternion2euler_yxz(
    qw: float, qx: float, qy: float, qz: float,
    RX: Tuple[float, float, float],
    RY: Tuple[float, float, float],
    RZ: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Convert a quaternion to BVH Euler angles (YXZ order).

    Implements OG-06 D.2.3 ``quaternion2euler`` for the BVH rotation
    order Y-X-Z.  The returned angles are in **degrees**.

    Args:
        qw: Scalar part of the quaternion.
        qx: X component.
        qy: Y component.
        qz: Z component.
        RX: Rest-pose X-axis column vector (3-tuple).
        RY: Rest-pose Y-axis column vector (3-tuple).
        RZ: Rest-pose Z-axis column vector (3-tuple).

    Returns:
        Tuple (Ex, Ey, Ez) in degrees, each in (-180, 180].
    """
    # Robust euler extraction using rotation-matrix decomposition.
    # OG-06 defines for YXZ: Q = Qez * Qex * Qey * Qr
    # So: M_Q * M_axes^T = Rz(Ez) * Rx(Ex) * Ry(Ey)
    Q = np.array([qw, qx, qy, qz])
    Q = qops.normalize(Q)
    w, x, y, z = Q

    M = np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w)],
        [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y)],
    ])

    A = np.array([[RX[0], RY[0], RZ[0]],
                  [RX[1], RY[1], RZ[1]],
                  [RX[2], RY[2], RZ[2]]])

    # Ml = M * A^T = Rz(Ez) * Rx(Ex) * Ry(Ey)
    Ml = M @ A.T

    # Extract YXZ euler: Ml[2][1] = -sin(Ex)
    sx = -Ml[2, 1]
    sx = _clamp(sx, -1.0, 1.0)
    Ex_rad = math.asin(sx)

    if abs(abs(sx) - 1.0) < 1e-8:
        Ey_rad = math.atan2(-Ml[0, 2], Ml[0, 0])
        Ez_rad = 0.0
    else:
        Ey_rad = math.atan2(Ml[2, 0], Ml[2, 2])
        Ez_rad = math.atan2(Ml[0, 1], Ml[1, 1])

    Ex = wrap_to_degrees(Ex_rad)
    Ey = wrap_to_degrees(Ey_rad)
    Ez = wrap_to_degrees(Ez_rad)
    return (Ex, Ey, Ez)
