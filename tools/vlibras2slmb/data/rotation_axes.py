"""ABNT NBR 25606 Table D.5: custom rotation axes for Type-2 and Type-3 joints.

Type-2 and Type-3 finger joints use custom rotation axes for compact angle
encoding.  Each joint is associated with three orthonormal-ish vectors
(RX, RY, RZ) that define the local rotation coordinate frame used for
encoding.

Type-0, Type-1, and Type-4 joints use identity axes.
"""

from __future__ import annotations

from typing import Final

# Type alias for a rotation axis set: (RX, RY, RZ) each being (x, y, z)
AxisSet = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

# ---------------------------------------------------------------------------
# Identity axes for Type-0, Type-1, and Type-4 joints
# ---------------------------------------------------------------------------
_IDENTITY_AXES: Final[AxisSet] = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)

# ---------------------------------------------------------------------------
# Custom axes for left hand joints (from ABNT Table D.5)
# ---------------------------------------------------------------------------
_L_THUMB_AXES: Final[AxisSet] = (
    (0.99975759, -0.00894864, -0.02011682),
    (0.00894864, 0.99995996, -0.00009002),
    (0.02011682, -0.00009002, 0.99979763),
)

_L_INDEX_AXES: Final[AxisSet] = (
    (0.99730041, 0.07342955, -0.00000095),
    (-0.07342955, 0.99730041, 0.00000004),
    (0.00000095, 0.00000004, 1.00000000),
)

_L_MIDDLE_AXES: Final[AxisSet] = (
    (0.99989815, 0.01427188, -0.00000065),
    (-0.01427188, 0.99989815, 0.00000000),
    (0.00000065, 0.00000000, 1.00000000),
)

_L_RING_AXES: Final[AxisSet] = (
    (0.99999949, 0.00100632, 0.00000062),
    (-0.00100632, 0.99999949, 0.00000000),
    (-0.00000062, 0.00000000, 1.00000000),
)

_L_PINKY_AXES: Final[AxisSet] = (
    (0.99974707, 0.02248970, 0.00000248),
    (-0.02248970, 0.99974707, -0.00000003),
    (-0.00000248, -0.00000003, 1.00000000),
)

# ---------------------------------------------------------------------------
# Custom axes for right hand joints (from ABNT Table D.5)
# ---------------------------------------------------------------------------
_R_THUMB_AXES: Final[AxisSet] = (
    (-0.99975732, -0.00894659, -0.02013100),
    (-0.00894659, 0.99995997, -0.00009006),
    (0.02013100, 0.00009006, -0.99979735),
)

_R_INDEX_AXES: Final[AxisSet] = (
    (-0.99726970, 0.07384535, -0.00011862),
    (0.07384535, 0.99726971, 0.00000439),
    (0.00011862, -0.00000439, -0.99999999),
)

_R_MIDDLE_AXES: Final[AxisSet] = (
    (-0.99988997, 0.01483368, -0.00006243),
    (0.01483368, 0.99988997, 0.00000046),
    (0.00006243, -0.00000046, -1.00000000),
)

_R_RING_AXES: Final[AxisSet] = (
    (-0.99999950, 0.00099809, 0.00000332),
    (0.00099809, 0.99999950, 0.00000000),
    (-0.00000332, 0.00000000, -1.00000000),
)

_R_PINKY_AXES: Final[AxisSet] = (
    (-0.99974698, 0.02249369, -0.00000500),
    (0.02249369, 0.99974698, 0.00000006),
    (0.00000500, -0.00000006, -1.00000000),
)

# ---------------------------------------------------------------------------
# ROTATION_AXES: joint_name -> (RX, RY, RZ)
# ---------------------------------------------------------------------------
# For Type-2 and Type-3 joints the custom axes from Table D.5 are used.
# All other joints (Type-0, Type-1, Type-4) use identity axes.

ROTATION_AXES: Final[dict[str, AxisSet]] = {
    # Type 0 -- root
    "hips_JNT": _IDENTITY_AXES,
    # Type 1 -- standard quaternion joints
    "spine_JNT": _IDENTITY_AXES,
    "spine1_JNT": _IDENTITY_AXES,
    "spine2_JNT": _IDENTITY_AXES,
    "neck_JNT": _IDENTITY_AXES,
    "head_JNT": _IDENTITY_AXES,
    "l_shoulder_JNT": _IDENTITY_AXES,
    "l_arm_JNT": _IDENTITY_AXES,
    "l_forearm_JNT": _IDENTITY_AXES,
    "l_hand_JNT": _IDENTITY_AXES,
    "r_shoulder_JNT": _IDENTITY_AXES,
    "r_arm_JNT": _IDENTITY_AXES,
    "r_forearm_JNT": _IDENTITY_AXES,
    "r_hand_JNT": _IDENTITY_AXES,
    "l_handThumb1_JNT": _IDENTITY_AXES,
    "r_handThumb1_JNT": _IDENTITY_AXES,
    # Type 2 -- finger metacarpals (2 custom-axis angles)
    "l_handIndex1_JNT": _L_INDEX_AXES,
    "l_handMiddle1_JNT": _L_MIDDLE_AXES,
    "l_handRing1_JNT": _L_RING_AXES,
    "l_handPinky1_JNT": _L_PINKY_AXES,
    "r_handIndex1_JNT": _R_INDEX_AXES,
    "r_handMiddle1_JNT": _R_MIDDLE_AXES,
    "r_handRing1_JNT": _R_RING_AXES,
    "r_handPinky1_JNT": _R_PINKY_AXES,
    # Type 3 -- finger phalanges (1 custom-axis angle)
    # Left thumb phalanges share thumb axes
    "l_handThumb2_JNT": _L_THUMB_AXES,
    "l_handThumb3_JNT": _L_THUMB_AXES,
    # Left index phalanges share index axes
    "l_handIndex2_JNT": _L_INDEX_AXES,
    "l_handIndex3_JNT": _L_INDEX_AXES,
    # Left middle phalanges share middle axes
    "l_handMiddle2_JNT": _L_MIDDLE_AXES,
    "l_handMiddle3_JNT": _L_MIDDLE_AXES,
    # Left ring phalanges share ring axes
    "l_handRing2_JNT": _L_RING_AXES,
    "l_handRing3_JNT": _L_RING_AXES,
    # Left pinky phalanges share pinky axes
    "l_handPinky2_JNT": _L_PINKY_AXES,
    "l_handPinky3_JNT": _L_PINKY_AXES,
    # Right thumb phalanges share thumb axes
    "r_handThumb2_JNT": _R_THUMB_AXES,
    "r_handThumb3_JNT": _R_THUMB_AXES,
    # Right index phalanges share index axes
    "r_handIndex2_JNT": _R_INDEX_AXES,
    "r_handIndex3_JNT": _R_INDEX_AXES,
    # Right middle phalanges share middle axes
    "r_handMiddle2_JNT": _R_MIDDLE_AXES,
    "r_handMiddle3_JNT": _R_MIDDLE_AXES,
    # Right ring phalanges share ring axes
    "r_handRing2_JNT": _R_RING_AXES,
    "r_handRing3_JNT": _R_RING_AXES,
    # Right pinky phalanges share pinky axes
    "r_handPinky2_JNT": _R_PINKY_AXES,
    "r_handPinky3_JNT": _R_PINKY_AXES,
    # Type 4 -- eye locators
    "r_eye_LOC": _IDENTITY_AXES,
    "l_eye_LOC": _IDENTITY_AXES,
}
