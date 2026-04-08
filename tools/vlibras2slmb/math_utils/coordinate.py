"""Coordinate system conversions between Unity and ABNT NBR 25606.

Unity uses a **left-handed** Y-up coordinate system.
ABNT NBR 25606 uses a **right-handed** system with:
  - X: right to left
  - Y: down to up
  - Z: back to front

The handedness flip requires negating the X and Z components of both
positions and quaternion imaginary parts.

Additionally, VLibras models exported through Blender carry an
``Armature.001`` root bone with a -90 degree X rotation (the standard
Blender-to-Unity axis convention transform). This rotation must be
removed before further processing.
"""

import math

import numpy as np

from . import quaternion as qops


# Pre-computed quaternion for the Armature.001 -90 deg X rotation.
# In (w, x, y, z) convention: cos(-45 deg), sin(-45 deg), 0, 0
_ROOT_ROTATION = np.array([
    math.cos(math.radians(-45.0)),   # w = cos(-pi/4) ~= 0.7071
    math.sin(math.radians(-45.0)),   # x = sin(-pi/4) ~= -0.7071
    0.0,
    0.0,
])

# Inverse of the root rotation (conjugate of the unit quaternion).
_ROOT_ROTATION_INV = qops.conjugate(_ROOT_ROTATION)


def unity_quat_to_abnt(q_wxyz: np.ndarray) -> np.ndarray:
    """Convert a quaternion from Unity left-handed to ABNT right-handed.

    The conversion negates the x and z imaginary components::

        (w, x, y, z) -> (w, -x, y, -z)

    This is equivalent to conjugating the rotation through the mirror
    matrix ``M = diag(-1, 1, -1)``:  ``R_abnt = M * R_unity * M^T``.

    Args:
        q_wxyz: Quaternion in (w, x, y, z) convention.

    Returns:
        ABNT-space quaternion (w, -x, y, -z).
    """
    w, x, y, z = q_wxyz
    return np.array([w, -x, y, -z])


def remove_root_rotation(q_wxyz: np.ndarray) -> np.ndarray:
    """Remove the Armature.001 root bone rotation from a quaternion.

    VLibras Unity assets have a root bone (``Armature.001``) carrying a
    -90 degree rotation around X.  In Unity ``[x, y, z, w]`` format the
    stored value is approximately ``[-0.7071, 0, 0, 0.7071]``, which in
    our ``(w, x, y, z)`` convention is ``(0.7071, -0.7071, 0, 0)``.

    To remove this rest-pose rotation the input quaternion is
    right-multiplied by the inverse::

        q_clean = q_wxyz * inverse(root_rotation)

    Args:
        q_wxyz: Quaternion including the root rotation, in (w, x, y, z).

    Returns:
        Quaternion with the root rotation factored out.
    """
    result = qops.multiply(q_wxyz, _ROOT_ROTATION_INV)
    return qops.normalize(result)


def unity_position_to_abnt(pos: list) -> np.ndarray:
    """Convert a position vector from Unity to ABNT coordinate system.

    Negates the X and Z components::

        (x, y, z) -> (-x, y, -z)

    Args:
        pos: Position as a list or array-like ``[x, y, z]``.

    Returns:
        ABNT-space position as a numpy array ``[-x, y, -z]``.
    """
    x, y, z = pos[0], pos[1], pos[2]
    return np.array([-x, y, -z])
