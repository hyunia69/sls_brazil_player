"""ABNT NBR 25606 Table D.9: joint encoding order and types.

Defines the canonical 46-joint skeleton used in SLMB binary encoding.
Each joint has:

- An encoding order index (0-45) that determines byte position in a frame.
- A type (0-4) that determines how rotation data is encoded:

    Type 0 (1 joint):   Root -- position + quaternion
    Type 1 (15 joints): Standard -- quaternion (smallest-three)
    Type 2 (8 joints):  Finger metacarpal -- 2 custom-axis angles
    Type 3 (20 joints): Finger phalanx -- 1 custom-axis angle
    Type 4 (2 joints):  Eye locator -- 2 gaze angles
"""

from __future__ import annotations

from typing import Final


# ---------------------------------------------------------------------------
# ABNT Table D.9 -- Joint encoding order and types
# ---------------------------------------------------------------------------
# Each entry: (encoding_order_index, joint_name, joint_type)

JOINT_ENCODING_ORDER: Final[list[tuple[int, str, int]]] = [
    (0, "hips_JNT", 0),
    (1, "spine_JNT", 1),
    (2, "spine1_JNT", 1),
    (3, "spine2_JNT", 1),
    (4, "neck_JNT", 1),
    (5, "head_JNT", 1),
    (6, "l_shoulder_JNT", 1),
    (7, "l_arm_JNT", 1),
    (8, "l_forearm_JNT", 1),
    (9, "l_hand_JNT", 1),
    (10, "r_shoulder_JNT", 1),
    (11, "r_arm_JNT", 1),
    (12, "r_forearm_JNT", 1),
    (13, "r_hand_JNT", 1),
    (14, "l_handThumb1_JNT", 1),
    (15, "r_handThumb1_JNT", 1),
    (16, "l_handIndex1_JNT", 2),
    (17, "l_handMiddle1_JNT", 2),
    (18, "l_handRing1_JNT", 2),
    (19, "l_handPinky1_JNT", 2),
    (20, "r_handIndex1_JNT", 2),
    (21, "r_handMiddle1_JNT", 2),
    (22, "r_handRing1_JNT", 2),
    (23, "r_handPinky1_JNT", 2),
    (24, "l_handIndex2_JNT", 3),
    (25, "l_handIndex3_JNT", 3),
    (26, "l_handMiddle2_JNT", 3),
    (27, "l_handMiddle3_JNT", 3),
    (28, "l_handRing2_JNT", 3),
    (29, "l_handRing3_JNT", 3),
    (30, "l_handPinky2_JNT", 3),
    (31, "l_handPinky3_JNT", 3),
    (32, "l_handThumb2_JNT", 3),
    (33, "l_handThumb3_JNT", 3),
    (34, "r_handIndex2_JNT", 3),
    (35, "r_handIndex3_JNT", 3),
    (36, "r_handMiddle2_JNT", 3),
    (37, "r_handMiddle3_JNT", 3),
    (38, "r_handRing2_JNT", 3),
    (39, "r_handRing3_JNT", 3),
    (40, "r_handPinky2_JNT", 3),
    (41, "r_handPinky3_JNT", 3),
    (42, "r_handThumb2_JNT", 3),
    (43, "r_handThumb3_JNT", 3),
    (44, "r_eye_LOC", 4),
    (45, "l_eye_LOC", 4),
]

NUM_JOINTS: Final[int] = 46

# ---------------------------------------------------------------------------
# Derived lookup tables
# ---------------------------------------------------------------------------

JOINT_ORDER: Final[dict[str, int]] = {
    name: idx for idx, name, _ in JOINT_ENCODING_ORDER
}

JOINT_TYPE: Final[dict[str, int]] = {
    name: jtype for _, name, jtype in JOINT_ENCODING_ORDER
}

# Joint names grouped by type
TYPE_0_JOINTS: Final[list[str]] = [
    name for _, name, jtype in JOINT_ENCODING_ORDER if jtype == 0
]
TYPE_1_JOINTS: Final[list[str]] = [
    name for _, name, jtype in JOINT_ENCODING_ORDER if jtype == 1
]
TYPE_2_JOINTS: Final[list[str]] = [
    name for _, name, jtype in JOINT_ENCODING_ORDER if jtype == 2
]
TYPE_3_JOINTS: Final[list[str]] = [
    name for _, name, jtype in JOINT_ENCODING_ORDER if jtype == 3
]
TYPE_4_JOINTS: Final[list[str]] = [
    name for _, name, jtype in JOINT_ENCODING_ORDER if jtype == 4
]

# ---------------------------------------------------------------------------
# Bytes per frame in the SLMB BodyMotionBlock
# ---------------------------------------------------------------------------
# Type-0: 12B (3×u16 trans + 3×s16 quat) × 1 joint  = 12
# Type-1:  6B (3×s16 quat)               × 15 joints = 90
# Type-2:  4B (u32 packed euler)          × 8 joints  = 32
# Type-3:  1B (u8 euler)                  × 20 joints = 20
# Type-4:  2B (u16 packed euler)          × 2 joints  = 4
# Total per frame: 12 + 90 + 32 + 20 + 4 = 158 bytes

BYTES_PER_FRAME: Final[int] = 158
