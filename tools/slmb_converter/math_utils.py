"""
Quaternion and Euler angle conversion utilities for the SLMB converter.

Implements rotation conversions defined in ABNT NBR 25606 Annex D and
SBTVD OG-06 Annex D (sections D.2.3, D.3).

Conventions:
    - Quaternions use (w, x, y, z) ordering throughout.
    - All public function angles are in DEGREES.
    - Coordinate system: X (right-to-left), Y (bottom-to-top), Z (back-to-front).
    - No external dependencies beyond the standard library ``math`` module.
"""

import math
from typing import Tuple

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Quaternion = Tuple[float, float, float, float]  # (w, x, y, z)
Vec3 = Tuple[float, float, float]


# ---------------------------------------------------------------------------
# Quaternion arithmetic
# ---------------------------------------------------------------------------

def quaternion_multiply(q1: Quaternion, q2: Quaternion) -> Quaternion:
    """Return the Hamilton product *q1 * q2*.

    Each quaternion is represented as ``(w, x, y, z)``.
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def quaternion_inverse(q: Quaternion) -> Quaternion:
    """Return the inverse of a **unit** quaternion (i.e. its conjugate)."""
    w, x, y, z = q
    return (w, -x, -y, -z)


def quaternion_normalize(q: Quaternion) -> Quaternion:
    """Normalize *q* to unit length.

    Returns ``(0, 0, 0, 0)`` unchanged if the magnitude is near zero.
    """
    w, x, y, z = q
    mag = math.sqrt(w * w + x * x + y * y + z * z)
    if mag < 1e-12:
        return q
    inv = 1.0 / mag
    return (w * inv, x * inv, y * inv, z * inv)


# ---------------------------------------------------------------------------
# Angle helpers
# ---------------------------------------------------------------------------

def wrap_to_degrees(radians: float) -> float:
    """Convert *radians* to degrees and wrap the result into (-180, 180]."""
    deg = math.degrees(radians)
    # Map into (-180, 180]
    deg = deg % 360.0
    if deg > 180.0:
        deg -= 360.0
    # Ensure exactly 180 maps to 180, not -180
    if deg == -180.0:
        deg = 180.0
    return deg


# ---------------------------------------------------------------------------
# Rotation-axis matrix  -->  quaternion
# ---------------------------------------------------------------------------

def rotationaxis_to_quaternion(
    RX: Vec3, RY: Vec3, RZ: Vec3,
) -> Quaternion:
    """Convert a rotation-axis matrix to a quaternion.

    Parameters
    ----------
    RX, RY, RZ : Vec3
        Column vectors of a 3x3 rotation matrix.
        ``RX = (r00, r10, r20)``, ``RY = (r01, r11, r21)``,
        ``RZ = (r02, r12, r22)``.

    Returns
    -------
    Quaternion
        ``(qw, qx, qy, qz)``

    Notes
    -----
    Uses the trace-based formula from OG-06 D.2.3::

        qw = sqrt(1 + RX[0] + RY[1] + RZ[2]) / 2
        qx = (RY[2] - RZ[1]) / (4 * qw)
        qy = (RZ[0] - RX[2]) / (4 * qw)
        qz = (RX[1] - RY[0]) / (4 * qw)

    When the trace is non-positive an alternative branch is used to
    maintain numerical stability.
    """
    trace = RX[0] + RY[1] + RZ[2]

    if trace > 0.0:
        s = 2.0 * math.sqrt(1.0 + trace)
        qw = 0.25 * s
        qx = (RY[2] - RZ[1]) / s
        qy = (RZ[0] - RX[2]) / s
        qz = (RX[1] - RY[0]) / s
    elif RX[0] > RY[1] and RX[0] > RZ[2]:
        s = 2.0 * math.sqrt(1.0 + RX[0] - RY[1] - RZ[2])
        qw = (RY[2] - RZ[1]) / s
        qx = 0.25 * s
        qy = (RX[1] + RY[0]) / s
        qz = (RZ[0] + RX[2]) / s
    elif RY[1] > RZ[2]:
        s = 2.0 * math.sqrt(1.0 + RY[1] - RX[0] - RZ[2])
        qw = (RZ[0] - RX[2]) / s
        qx = (RX[1] + RY[0]) / s
        qy = 0.25 * s
        qz = (RY[2] + RZ[1]) / s
    else:
        s = 2.0 * math.sqrt(1.0 + RZ[2] - RX[0] - RY[1])
        qw = (RX[1] - RY[0]) / s
        qx = (RZ[0] + RX[2]) / s
        qy = (RY[2] + RZ[1]) / s
        qz = 0.25 * s

    return quaternion_normalize((qw, qx, qy, qz))


# ---------------------------------------------------------------------------
# Euler  -->  quaternion
# ---------------------------------------------------------------------------

def _euler_component_quaternions(
    Ex_deg: float, Ey_deg: float, Ez_deg: float,
) -> Tuple[Quaternion, Quaternion, Quaternion]:
    """Return individual axis quaternions for Euler angles (in degrees)."""
    Ex = math.radians(Ex_deg) / 2.0
    Ey = math.radians(Ey_deg) / 2.0
    Ez = math.radians(Ez_deg) / 2.0

    Qex: Quaternion = (math.cos(Ex), math.sin(Ex), 0.0, 0.0)
    Qey: Quaternion = (math.cos(Ey), 0.0, math.sin(Ey), 0.0)
    Qez: Quaternion = (math.cos(Ez), 0.0, 0.0, math.sin(Ez))
    return Qex, Qey, Qez


def euler2quaternion_yxz(
    Ex: float, Ey: float, Ez: float,
    RX: Vec3, RY: Vec3, RZ: Vec3,
) -> Quaternion:
    """Convert BVH Euler angles (Y/X/Z order) to a quaternion.

    Parameters
    ----------
    Ex, Ey, Ez : float
        Euler rotation angles in **degrees**.
    RX, RY, RZ : Vec3
        Rotation-axis matrix columns (rest-pose correction).

    Returns
    -------
    Quaternion
        ``Qez * Qex * Qey * Qr``
    """
    Qr = rotationaxis_to_quaternion(RX, RY, RZ)
    Qex, Qey, Qez = _euler_component_quaternions(Ex, Ey, Ez)
    # Composition order: Qez * Qex * Qey * Qr
    result = quaternion_multiply(Qez, quaternion_multiply(Qex, quaternion_multiply(Qey, Qr)))
    return quaternion_normalize(result)


def euler2quaternion_xyz(
    Ex: float, Ey: float, Ez: float,
    RX: Vec3, RY: Vec3, RZ: Vec3,
) -> Quaternion:
    """Convert SLMB Euler angles (X/Y/Z order) to a quaternion.

    Parameters
    ----------
    Ex, Ey, Ez : float
        Euler rotation angles in **degrees**.
    RX, RY, RZ : Vec3
        Rotation-axis matrix columns (rest-pose correction).

    Returns
    -------
    Quaternion
        ``Qez * Qey * Qex * Qr``
    """
    Qr = rotationaxis_to_quaternion(RX, RY, RZ)
    Qex, Qey, Qez = _euler_component_quaternions(Ex, Ey, Ez)
    # Composition order: Qez * Qey * Qex * Qr
    result = quaternion_multiply(Qez, quaternion_multiply(Qey, quaternion_multiply(Qex, Qr)))
    return quaternion_normalize(result)


# ---------------------------------------------------------------------------
# Quaternion  -->  Euler
# ---------------------------------------------------------------------------

def quaternion2euler_yxz(
    qw: float, qx: float, qy: float, qz: float,
    RX: Vec3, RY: Vec3, RZ: Vec3,
) -> Vec3:
    """Convert a quaternion to BVH Euler angles (Y/X/Z order).

    Parameters
    ----------
    qw, qx, qy, qz : float
        Input quaternion components.
    RX, RY, RZ : Vec3
        Rotation-axis matrix columns (rest-pose correction).

    Returns
    -------
    Vec3
        ``(Ex, Ey, Ez)`` in **degrees**, wrapped to (-180, 180].
    """
    Q: Quaternion = (qw, qx, qy, qz)
    Qr = rotationaxis_to_quaternion(RX, RY, RZ)
    Qr_inv = quaternion_inverse(Qr)
    qRw, qRx, qRy, qRz = quaternion_multiply(Q, Qr_inv)

    a = qRw - qRx
    b = qRy - qRz
    c = qRx + qRw
    d = -qRz - qRy

    th_plus = math.atan2(b, a)

    if d != 0.0 or c != 0.0:
        th_minus = math.atan2(d, c)
    else:
        th_minus = th_plus

    th1 = th_plus - th_minus
    denom = a * a + b * b + c * c + d * d
    if denom < 1e-12:
        th2 = 0.0
    else:
        arg = 2.0 * (a * a + b * b) / denom - 1.0
        # Clamp to [-1, 1] for numerical safety
        arg = max(-1.0, min(1.0, arg))
        th2 = math.acos(arg)
    th3 = th_plus + th_minus

    Ex = wrap_to_degrees(th2 - math.pi / 2.0)
    Ey = wrap_to_degrees(th1)
    Ez = wrap_to_degrees(-th3)

    return (Ex, Ey, Ez)


def quaternion2euler_xyz(
    qw: float, qx: float, qy: float, qz: float,
    RX: Vec3, RY: Vec3, RZ: Vec3,
) -> Vec3:
    """Convert a quaternion to SLMB Euler angles (X/Y/Z order).

    Parameters
    ----------
    qw, qx, qy, qz : float
        Input quaternion components.
    RX, RY, RZ : Vec3
        Rotation-axis matrix columns (rest-pose correction).

    Returns
    -------
    Vec3
        ``(Ex, Ey, Ez)`` in **degrees**, wrapped to (-180, 180].
    """
    Q: Quaternion = (qw, qx, qy, qz)
    Qr = rotationaxis_to_quaternion(RX, RY, RZ)
    Qr_inv = quaternion_inverse(Qr)
    qRw, qRx, qRy, qRz = quaternion_multiply(Q, Qr_inv)

    a = qRw - qRy
    b = qRx + qRz
    c = qRy + qRw
    d = qRz - qRx

    th_plus = math.atan2(b, a)

    if d != 0.0 or c != 0.0:
        th_minus = math.atan2(d, c)
    else:
        th_minus = th_plus

    th1 = th_plus - th_minus
    denom = a * a + b * b + c * c + d * d
    if denom < 1e-12:
        th2 = 0.0
    else:
        arg = 2.0 * (a * a + b * b) / denom - 1.0
        arg = max(-1.0, min(1.0, arg))
        th2 = math.acos(arg)
    th3 = th_plus + th_minus

    Ex = wrap_to_degrees(th1)
    Ey = wrap_to_degrees(th2 - math.pi / 2.0)
    Ez = wrap_to_degrees(th3)

    return (Ex, Ey, Ez)
