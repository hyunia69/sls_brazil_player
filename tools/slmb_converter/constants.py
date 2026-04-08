"""
Constants from ABNT NBR 25606 Annex D specifications.
Joint definitions, blendshape IDs, rotation axes.
"""

import struct
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# ─── SLMB Magic & Keys ───

SLMB_TITLE_KEY = bytes([0x53, 0x4C, 0x4D, 0x42])  # "SLMB"
BODY_MOTION_KEY = bytes([0x01, 0x01])  # Body Geometry ID 1
FACE_MOTION_KEY = bytes([0x02, 0x01])  # Face Geometry ID 1

# ─── Joint Type Enum ───

JOINT_TYPE_0 = 0  # Root: translation + quaternion rotation
JOINT_TYPE_1 = 1  # Main joints: quaternion rotation only
JOINT_TYPE_2 = 2  # Palm joints: 3-axis euler packed 32-bit
JOINT_TYPE_3 = 3  # Finger joints: z-axis euler 8-bit
JOINT_TYPE_4 = 4  # Eye joints: x/y euler packed 16-bit

# ─── Joint Order (Table D.9) ───
# SLMB binary encoding order: (joint_name, joint_type)

JOINT_ORDER: List[Tuple[str, int]] = [
    ("hips_JNT", 0),           # 0
    ("spine_JNT", 1),          # 1
    ("spine1_JNT", 1),         # 2
    ("spine2_JNT", 1),         # 3
    ("neck_JNT", 1),           # 4
    ("head_JNT", 1),           # 5
    ("l_shoulder_JNT", 1),     # 6
    ("l_arm_JNT", 1),          # 7
    ("l_forearm_JNT", 1),      # 8
    ("l_hand_JNT", 1),         # 9
    ("r_shoulder_JNT", 1),     # 10
    ("r_arm_JNT", 1),          # 11
    ("r_forearm_JNT", 1),      # 12
    ("r_hand_JNT", 1),         # 13
    ("l_handThumb1_JNT", 1),   # 14
    ("r_handThumb1_JNT", 1),   # 15
    ("l_handIndex1_JNT", 2),   # 16
    ("l_handMiddle1_JNT", 2),  # 17
    ("l_handRing1_JNT", 2),    # 18
    ("l_handPinky1_JNT", 2),   # 19
    ("r_handIndex1_JNT", 2),   # 20
    ("r_handMiddle1_JNT", 2),  # 21
    ("r_handRing1_JNT", 2),    # 22
    ("r_handPinky1_JNT", 2),   # 23
    ("l_handIndex2_JNT", 3),   # 24
    ("l_handIndex3_JNT", 3),   # 25
    ("l_handMiddle2_JNT", 3),  # 26
    ("l_handMiddle3_JNT", 3),  # 27
    ("l_handRing2_JNT", 3),    # 28
    ("l_handRing3_JNT", 3),    # 29
    ("l_handPinky2_JNT", 3),   # 30
    ("l_handPinky3_JNT", 3),   # 31
    ("l_handThumb2_JNT", 3),   # 32
    ("l_handThumb3_JNT", 3),   # 33
    ("r_handIndex2_JNT", 3),   # 34
    ("r_handIndex3_JNT", 3),   # 35
    ("r_handMiddle2_JNT", 3),  # 36
    ("r_handMiddle3_JNT", 3),  # 37
    ("r_handRing2_JNT", 3),    # 38
    ("r_handRing3_JNT", 3),    # 39
    ("r_handPinky2_JNT", 3),   # 40
    ("r_handPinky3_JNT", 3),   # 41
    ("r_handThumb2_JNT", 3),   # 42
    ("r_handThumb3_JNT", 3),   # 43
    ("r_eye_LOC", 4),          # 44
    ("l_eye_LOC", 4),          # 45
]

NUM_JOINTS = 46

# Build lookup: joint_name -> (slmb_order, joint_type)
JOINT_NAME_TO_ORDER: Dict[str, Tuple[int, int]] = {
    name: (idx, jtype) for idx, (name, jtype) in enumerate(JOINT_ORDER)
}

# ─── Skeleton Hierarchy (Table D.1) ───
# parent_name -> list of child names

SKELETON_HIERARCHY: Dict[str, List[str]] = {
    "hips_JNT": ["spine_JNT"],
    "spine_JNT": ["spine1_JNT"],
    "spine1_JNT": ["spine2_JNT"],
    "spine2_JNT": ["neck_JNT", "r_shoulder_JNT", "l_shoulder_JNT"],
    "neck_JNT": ["head_JNT"],
    "head_JNT": ["r_eye_LOC", "l_eye_LOC"],
    "r_shoulder_JNT": ["r_arm_JNT"],
    "r_arm_JNT": ["r_forearm_JNT"],
    "r_forearm_JNT": ["r_hand_JNT"],
    "r_hand_JNT": [
        "r_handThumb1_JNT", "r_handIndex1_JNT", "r_handMiddle1_JNT",
        "r_handRing1_JNT", "r_handPinky1_JNT"
    ],
    "r_handThumb1_JNT": ["r_handThumb2_JNT"],
    "r_handThumb2_JNT": ["r_handThumb3_JNT"],
    "r_handIndex1_JNT": ["r_handIndex2_JNT"],
    "r_handIndex2_JNT": ["r_handIndex3_JNT"],
    "r_handMiddle1_JNT": ["r_handMiddle2_JNT"],
    "r_handMiddle2_JNT": ["r_handMiddle3_JNT"],
    "r_handRing1_JNT": ["r_handRing2_JNT"],
    "r_handRing2_JNT": ["r_handRing3_JNT"],
    "r_handPinky1_JNT": ["r_handPinky2_JNT"],
    "r_handPinky2_JNT": ["r_handPinky3_JNT"],
    "l_shoulder_JNT": ["l_arm_JNT"],
    "l_arm_JNT": ["l_forearm_JNT"],
    "l_forearm_JNT": ["l_hand_JNT"],
    "l_hand_JNT": [
        "l_handThumb1_JNT", "l_handIndex1_JNT", "l_handMiddle1_JNT",
        "l_handRing1_JNT", "l_handPinky1_JNT"
    ],
    "l_handThumb1_JNT": ["l_handThumb2_JNT"],
    "l_handThumb2_JNT": ["l_handThumb3_JNT"],
    "l_handIndex1_JNT": ["l_handIndex2_JNT"],
    "l_handIndex2_JNT": ["l_handIndex3_JNT"],
    "l_handMiddle1_JNT": ["l_handMiddle2_JNT"],
    "l_handMiddle2_JNT": ["l_handMiddle3_JNT"],
    "l_handRing1_JNT": ["l_handRing2_JNT"],
    "l_handRing2_JNT": ["l_handRing3_JNT"],
    "l_handPinky1_JNT": ["l_handPinky2_JNT"],
    "l_handPinky2_JNT": ["l_handPinky3_JNT"],
}

# ─── Reference Pose (Table D.3) ───
# Offsets from parent joint in meters

REFPOSE_FROM_PARENT: Dict[str, Tuple[float, float, float]] = {
    "hips_JNT":             (0.0, 0.0, 0.0),
    "spine_JNT":            (0.0, 0.04130373, -0.00008512),
    "spine1_JNT":           (0.0, 0.10693992, -0.00005568),
    "spine2_JNT":           (0.0, 0.10153212, -0.00012624),
    "neck_JNT":             (0.0, 0.17065638, 0.00263754),
    "head_JNT":             (0.0, 0.08137577, 0.00007754),
    "r_eye_LOC":            (-0.05100100, 0.12306628, 0.09664178),
    "l_eye_LOC":            (0.05100100, 0.12306628, 0.09664178),
    "r_shoulder_JNT":       (-0.02886765, 0.12539096, -0.00534970),
    "r_arm_JNT":            (-0.10265322, -0.00000050, -0.00000020),
    "r_forearm_JNT":        (-0.25572863, 0.0, -0.00000009),
    "r_hand_JNT":           (-0.19807005, -0.00346000, -0.00000001),
    "l_shoulder_JNT":       (0.02886657, 0.12539132, -0.00534974),
    "l_arm_JNT":            (0.10265323, 0.00000035, 0.00000019),
    "l_forearm_JNT":        (0.25572872, 0.00000003, 0.00000003),
    "l_hand_JNT":           (0.19806792, -0.00345714, 0.00000008),
    # Right hand fingers
    "r_handThumb1_JNT":     (-0.01817488, -0.01260972, 0.03617090),
    "r_handThumb2_JNT":     (-0.02639243, -0.00023618, -0.00053143),
    "r_handThumb3_JNT":     (-0.02698978, -0.00823875, 0.00000033),
    "r_handIndex1_JNT":     (-0.08251890, -0.00108337, 0.03749100),
    "r_handIndex2_JNT":     (-0.03896140, 0.00288500, -0.00000463),
    "r_handIndex3_JNT":     (-0.02318387, 0.00159236, -0.00000487),
    "r_handMiddle1_JNT":    (-0.09047189, 0.00040404, 0.01280809),
    "r_handMiddle2_JNT":    (-0.03918013, 0.00058125, -0.00000245),
    "r_handMiddle3_JNT":    (-0.02517173, 0.00020933, -0.00000344),
    "r_handRing1_JNT":      (-0.08770376, -0.00316066, -0.01406740),
    "r_handRing2_JNT":      (-0.03670816, 0.00003664, 0.00000012),
    "r_handRing3_JNT":      (-0.02391655, 0.00005686, -0.00000005),
    "r_handPinky1_JNT":     (-0.07380626, -0.01009364, -0.03361094),
    "r_handPinky2_JNT":     (-0.02923373, 0.00065774, -0.00000015),
    "r_handPinky3_JNT":     (-0.01903112, -0.00013694, 0.00000004),
    # Left hand fingers
    "l_handThumb1_JNT":     (0.01812944, -0.01252033, 0.03615281),
    "l_handThumb2_JNT":     (0.02639235, -0.00023623, -0.00053106),
    "l_handThumb3_JNT":     (0.02817296, 0.00161941, -0.00000019),
    "l_handIndex1_JNT":     (0.08246994, -0.00097605, 0.03748598),
    "l_handIndex2_JNT":     (0.03896263, 0.00286875, -0.00000004),
    "l_handIndex3_JNT":     (0.02318424, 0.00158303, -0.00000001),
    "l_handMiddle1_JNT":    (0.09042166, 0.00054560, 0.01280483),
    "l_handMiddle2_JNT":    (0.03918027, 0.00055923, -0.00000003),
    "l_handMiddle3_JNT":    (0.02517179, 0.00019623, -0.00000001),
    "l_handRing1_JNT":      (0.08765368, -0.00298586, -0.01407511),
    "l_handRing2_JNT":      (0.03670795, 0.00003694, 0.00000002),
    "l_handRing3_JNT":      (0.02391658, 0.00005747, 0.00000001),
    "l_handPinky1_JNT":     (0.07375719, -0.00989721, -0.03362722),
    "l_handPinky2_JNT":     (0.02923453, 0.00065764, 0.00000007),
    "l_handPinky3_JNT":     (0.01903052, -0.00013621, 0.00000002),
}

# End-site offsets for leaf joints (approximate bone end points)
REFPOSE_END: Dict[str, Tuple[float, float, float]] = {
    "r_eye_LOC":         (0.0, 0.0, 0.0),
    "l_eye_LOC":         (0.0, 0.0, 0.0),
    "r_handThumb3_JNT":  (-0.038753, -0.00611784, -0.00000028),
    "r_handIndex3_JNT":  (-0.02565999, -0.00000006, -0.00000002),
    "r_handMiddle3_JNT": (-0.02488746, -0.00000003, -0.00000001),
    "r_handRing3_JNT":   (-0.02137327, -0.00000002, 0.0),
    "r_handPinky3_JNT":  (-0.01808159, -0.00000003, 0.00000001),
    "l_handThumb3_JNT":  (0.038753, -0.00611784, -0.00000028),
    "l_handIndex3_JNT":  (0.02565999, -0.00000006, -0.00000002),
    "l_handMiddle3_JNT": (0.02488746, -0.00000003, -0.00000001),
    "l_handRing3_JNT":   (0.02137327, -0.00000002, 0.0),
    "l_handPinky3_JNT":  (0.01808159, -0.00000003, 0.00000001),
}

# ─── Rotation Axes for Type-2/3 Joints (Table D.5) ───
# Each entry: (RX, RY, RZ) where each is a 3D vector

Vec3 = Tuple[float, float, float]
RotAxis = Tuple[Vec3, Vec3, Vec3]  # (RX, RY, RZ)

ROTATION_AXES: Dict[str, RotAxis] = {
    # Left hand
    "l_handThumb2_JNT": (
        (0.99975759, -0.00894864, -0.02011682),
        (0.00894864, 0.99995996, -0.00009002),
        (0.02011682, -0.00009002, 0.99979763),
    ),
    "l_handThumb3_JNT": (
        (0.99975759, -0.00894864, -0.02011682),
        (0.00894864, 0.99995996, -0.00009002),
        (0.02011682, -0.00009002, 0.99979763),
    ),
    "l_handIndex1_JNT": (
        (0.99730041, 0.07342955, -0.00000095),
        (-0.07342955, 0.99730041, 0.00000004),
        (0.00000095, 0.00000004, 1.0),
    ),
    "l_handIndex2_JNT": (
        (0.99730041, 0.07342955, -0.00000095),
        (-0.07342955, 0.99730041, 0.00000004),
        (0.00000095, 0.00000004, 1.0),
    ),
    "l_handIndex3_JNT": (
        (0.99730041, 0.07342955, -0.00000095),
        (-0.07342955, 0.99730041, 0.00000004),
        (0.00000095, 0.00000004, 1.0),
    ),
    "l_handMiddle1_JNT": (
        (0.99989815, 0.01427188, -0.00000065),
        (-0.01427188, 0.99989815, 0.0),
        (0.00000065, 0.0, 1.0),
    ),
    "l_handMiddle2_JNT": (
        (0.99989815, 0.01427188, -0.00000065),
        (-0.01427188, 0.99989815, 0.0),
        (0.00000065, 0.0, 1.0),
    ),
    "l_handMiddle3_JNT": (
        (0.99989815, 0.01427188, -0.00000065),
        (-0.01427188, 0.99989815, 0.0),
        (0.00000065, 0.0, 1.0),
    ),
    "l_handRing1_JNT": (
        (0.99999949, 0.00100632, 0.00000062),
        (-0.00100632, 0.99999949, 0.0),
        (-0.00000062, 0.0, 1.0),
    ),
    "l_handRing2_JNT": (
        (0.99999949, 0.00100632, 0.00000062),
        (-0.00100632, 0.99999949, 0.0),
        (-0.00000062, 0.0, 1.0),
    ),
    "l_handRing3_JNT": (
        (0.99999949, 0.00100632, 0.00000062),
        (-0.00100632, 0.99999949, 0.0),
        (-0.00000062, 0.0, 1.0),
    ),
    "l_handPinky1_JNT": (
        (0.99974707, 0.02248970, 0.00000248),
        (-0.02248970, 0.99974707, -0.00000003),
        (-0.00000248, -0.00000003, 1.0),
    ),
    "l_handPinky2_JNT": (
        (0.99974707, 0.02248970, 0.00000248),
        (-0.02248970, 0.99974707, -0.00000003),
        (-0.00000248, -0.00000003, 1.0),
    ),
    "l_handPinky3_JNT": (
        (0.99974707, 0.02248970, 0.00000248),
        (-0.02248970, 0.99974707, -0.00000003),
        (-0.00000248, -0.00000003, 1.0),
    ),
    # Right hand
    "r_handThumb2_JNT": (
        (-0.99975732, -0.00894659, -0.02013100),
        (-0.00894659, 0.99995997, -0.00009006),
        (0.02013100, 0.00009006, -0.99979735),
    ),
    "r_handThumb3_JNT": (
        (-0.99975732, -0.00894659, -0.02013100),
        (-0.00894659, 0.99995997, -0.00009006),
        (0.02013100, 0.00009006, -0.99979735),
    ),
    "r_handIndex1_JNT": (
        (-0.99726970, 0.07384535, -0.00011862),
        (0.07384535, 0.99726971, 0.00000439),
        (0.00011862, -0.00000439, -0.99999999),
    ),
    "r_handIndex2_JNT": (
        (-0.99726970, 0.07384535, -0.00011862),
        (0.07384535, 0.99726971, 0.00000439),
        (0.00011862, -0.00000439, -0.99999999),
    ),
    "r_handIndex3_JNT": (
        (-0.99726970, 0.07384535, -0.00011862),
        (0.07384535, 0.99726971, 0.00000439),
        (0.00011862, -0.00000439, -0.99999999),
    ),
    "r_handMiddle1_JNT": (
        (-0.99988997, 0.01483368, -0.00006243),
        (0.01483368, 0.99988997, 0.00000046),
        (0.00006243, -0.00000046, -1.0),
    ),
    "r_handMiddle2_JNT": (
        (-0.99988997, 0.01483368, -0.00006243),
        (0.01483368, 0.99988997, 0.00000046),
        (0.00006243, -0.00000046, -1.0),
    ),
    "r_handMiddle3_JNT": (
        (-0.99988997, 0.01483368, -0.00006243),
        (0.01483368, 0.99988997, 0.00000046),
        (0.00006243, -0.00000046, -1.0),
    ),
    "r_handRing1_JNT": (
        (-0.99999950, 0.00099809, 0.00000332),
        (0.00099809, 0.99999950, 0.0),
        (-0.00000332, 0.0, -1.0),
    ),
    "r_handRing2_JNT": (
        (-0.99999950, 0.00099809, 0.00000332),
        (0.00099809, 0.99999950, 0.0),
        (-0.00000332, 0.0, -1.0),
    ),
    "r_handRing3_JNT": (
        (-0.99999950, 0.00099809, 0.00000332),
        (0.00099809, 0.99999950, 0.0),
        (-0.00000332, 0.0, -1.0),
    ),
    "r_handPinky1_JNT": (
        (-0.99974698, 0.02249369, -0.00000500),
        (0.02249369, 0.99974698, 0.00000006),
        (0.00000500, -0.00000006, -1.0),
    ),
    "r_handPinky2_JNT": (
        (-0.99974698, 0.02249369, -0.00000500),
        (0.02249369, 0.99974698, 0.00000006),
        (0.00000500, -0.00000006, -1.0),
    ),
    "r_handPinky3_JNT": (
        (-0.99974698, 0.02249369, -0.00000500),
        (0.02249369, 0.99974698, 0.00000006),
        (0.00000500, -0.00000006, -1.0),
    ),
}

# Identity rotation axes for Type-0/1/4 joints
IDENTITY_AXES: RotAxis = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)


def get_rotation_axes(joint_name: str) -> RotAxis:
    """Get rotation axes for a joint. Returns custom axes for Type-2/3, identity for others."""
    return ROTATION_AXES.get(joint_name, IDENTITY_AXES)


# ─── Blendshape ID Mapping (Table D.11) ───

# head_GEO blendshape names by ID (0-67)
HEAD_GEO_BLENDSHAPES = [
    "EyeBlink_Left", "EyeBlink_Right", "EyeSquint_Left", "EyeSquint_Right",
    "EyeDown_Left", "EyeDown_Right", "EyeIn_Left", "EyeIn_Right",
    "EyeOpen_Left", "EyeOpen_Right", "EyeOut_Left", "EyeOut_Right",
    "EyeUp_Left", "EyeUp_Right", "BrowsDown_Left", "BrowsDown_Right",
    "BrowsUp_Center", "BrowsUp_Left", "BrowsUp_Right", "JawFwd",
    "JawLeft", "JawOpen", "JawChew", "JawRight",
    "MouthLeft", "MouthRight", "MouthFrown_Left", "MouthFrown_Right",
    "MouthSmile_Left", "MouthSmile_Right", "MouthDimple_Left", "MouthDimple_Right",
    "LipsStretch_Left", "LipsStretch_Right", "LipsUpperClose", "LipsLowerClose",
    "LipsUpperUp", "LipsLowerDown", "LipsUpperOpen", "LipsLowerOpen",
    "LipsFunnel", "LipsPucker", "ChinLowerRaise", "ChinUpperRaise",
    "Sneer", "Puff", "CheekSquint_Left", "CheekSquint_Right",
    "HAPPY_48", "HAPPY_49", "HAPPY_50", "HAPPY_51", "HAPPY_52",
    "ANGRY_53", "ANGRY_54", "ANGRY_55",
    "DISGUST_56", "DISGUST_57", "SAD_58", "SURPRISE_59", "SURPRISE_60",
    "Puff_Left", "Puff_Right", "Tongue_Out", "Tongue_Up",
    "Tongue_Down", "Tongue_Left", "Tongue_Right",
]

# Mesh name -> (base_id, blendshape_name_list)
# For complete Table D.11 mapping
MESH_BLENDSHAPE_MAP: Dict[str, Dict[int, str]] = {
    "head_GEO": {i: name for i, name in enumerate(HEAD_GEO_BLENDSHAPES)},
    "mouth_GEO": {
        1020: "JawLeft", 1021: "JawOpen", 1023: "JawRight",
        1024: "MouthLeft", 1025: "MouthRight",
        1036: "LipsUpperUp", 1037: "LipsLowerDown", 1040: "LipsFunnel",
        1042: "ChinLowerRaise",
        1050: "HAPPY_50", 1051: "HAPPY_51", 1052: "HAPPY_52",
        1059: "SURPRISE_59",
        1063: "Tongue_Out", 1064: "Tongue_Up", 1065: "Tongue_Down",
        1066: "Tongue_Left", 1067: "Tongue_Right",
    },
    "eyelash_GEO": {
        2000: "EyeBlink_Left", 2001: "EyeBlink_Right",
        2002: "EyeSquint_Left", 2003: "EyeSquint_Right",
        2004: "EyeDown_Left", 2005: "EyeDown_Right",
        2006: "EyeIn_Left", 2007: "EyeIn_Right",
        2008: "EyeOpen_Left", 2009: "EyeOpen_Right",
        2010: "EyeOut_Left", 2011: "EyeOut_Right",
        2012: "EyeUp_Left", 2013: "EyeUp_Right",
        2046: "CheekSquint_Left", 2047: "CheekSquint_Right",
        2048: "HAPPY_48", 2054: "ANGRY_54", 2058: "SAD_58", 2059: "SURPRISE_59",
    },
    "eyebrow_l_GEO": {
        3014: "BrowsDown_Left", 3015: "BrowsDown_Right",
        3016: "BrowsUp_Center", 3017: "BrowsUp_Left", 3018: "BrowsUp_Right",
        3044: "Sneer", 3051: "HAPPY_51", 3055: "ANGRY_55", 3058: "SAD_58",
    },
    "eyebrow_r_GEO": {
        4014: "BrowsDown_Left", 4015: "BrowsDown_Right",
        4016: "BrowsUp_Center", 4017: "BrowsUp_Left", 4018: "BrowsUp_Right",
        4044: "Sneer", 4051: "HAPPY_51", 4055: "ANGRY_55", 4058: "SAD_58",
    },
    "iris_l_GEO": {5059: "SURPRISE_59"},
    "iris_r_GEO": {6059: "SURPRISE_59"},
}

# Build reverse lookup: (mesh_name, blendshape_name) -> blendshape_id
BLENDSHAPE_NAME_TO_ID: Dict[Tuple[str, str], int] = {}
BLENDSHAPE_ID_TO_NAME: Dict[int, Tuple[str, str]] = {}

for mesh_name, id_map in MESH_BLENDSHAPE_MAP.items():
    for bs_id, bs_name in id_map.items():
        BLENDSHAPE_NAME_TO_ID[(mesh_name, bs_name)] = bs_id
        BLENDSHAPE_ID_TO_NAME[bs_id] = (mesh_name, bs_name)
