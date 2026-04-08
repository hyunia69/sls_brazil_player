"""ABNT NBR 25606 Table D.3: reference (T-pose) joint offsets.

Each entry stores the translation offset from the parent joint to the child
joint in the reference pose, expressed in meters.  The coordinate system
follows ABNT convention: X (right-to-left), Y (down-to-up), Z (back-to-front).

The reference skeleton is based on a 1.67 m human figure.
"""

from __future__ import annotations

from typing import Final

# (x, y, z) offset in meters from parent joint
REFERENCE_POSE: Final[dict[str, tuple[float, float, float]]] = {
    # Root -- world origin
    "hips_JNT": (0.0, 0.0, 0.0),
    # Spine chain (parent: hips)
    "spine_JNT": (0.0, 0.04130373, -0.00008512),
    "spine1_JNT": (0.0, 0.10693992, -0.00005568),
    "spine2_JNT": (0.0, 0.10153212, -0.00012624),
    # Neck / head (parent: spine2)
    "neck_JNT": (0.0, 0.17065638, 0.00263754),
    "head_JNT": (0.0, 0.08137577, 0.00007754),
    # Eye locators (parent: head)
    "r_eye_LOC": (-0.05100100, 0.12306628, 0.09664178),
    "l_eye_LOC": (0.05100100, 0.12306628, 0.09664178),
    # ---- Right arm chain (parent: spine2 -> shoulder -> arm -> ...) ----
    "r_shoulder_JNT": (-0.02886765, 0.12539096, -0.00534970),
    "r_arm_JNT": (-0.10265322, -0.00000050, -0.00000020),
    "r_forearm_JNT": (-0.25572863, 0.0, -0.00000009),
    "r_hand_JNT": (-0.19807005, -0.00346000, -0.00000001),
    # ---- Left arm chain (parent: spine2 -> shoulder -> arm -> ...) ----
    "l_shoulder_JNT": (0.02886657, 0.12539132, -0.00534974),
    "l_arm_JNT": (0.10265323, 0.00000035, 0.00000019),
    "l_forearm_JNT": (0.25572872, 0.00000003, 0.00000003),
    "l_hand_JNT": (0.19806792, -0.00345714, 0.00000008),
    # ---- Right hand fingers ----
    # Thumb
    "r_handThumb1_JNT": (-0.01817488, -0.01260972, 0.03617090),
    "r_handThumb2_JNT": (-0.02639243, -0.00023618, -0.00053143),
    "r_handThumb3_JNT": (-0.02698978, -0.00823875, 0.00000033),
    # Index
    "r_handIndex1_JNT": (-0.08251890, -0.00108337, 0.03749100),
    "r_handIndex2_JNT": (-0.03896140, 0.00288500, -0.00000463),
    "r_handIndex3_JNT": (-0.02318387, 0.00159236, -0.00000487),
    # Middle
    "r_handMiddle1_JNT": (-0.09047189, 0.00040404, 0.01280809),
    "r_handMiddle2_JNT": (-0.03918013, 0.00058125, -0.00000245),
    "r_handMiddle3_JNT": (-0.02517173, 0.00020933, -0.00000344),
    # Ring
    "r_handRing1_JNT": (-0.08770376, -0.00316066, -0.01406740),
    "r_handRing2_JNT": (-0.03670816, 0.00003664, 0.00000012),
    "r_handRing3_JNT": (-0.02391655, 0.00005686, -0.00000005),
    # Pinky
    "r_handPinky1_JNT": (-0.07380626, -0.01009364, -0.03361094),
    "r_handPinky2_JNT": (-0.02923373, 0.00065774, -0.00000015),
    "r_handPinky3_JNT": (-0.01903112, -0.00013694, 0.00000004),
    # ---- Left hand fingers ----
    # Thumb
    "l_handThumb1_JNT": (0.01812944, -0.01252033, 0.03615281),
    "l_handThumb2_JNT": (0.02639235, -0.00023623, -0.00053106),
    "l_handThumb3_JNT": (0.02817296, 0.00161941, -0.00000019),
    # Index
    "l_handIndex1_JNT": (0.08246994, -0.00097605, 0.03748598),
    "l_handIndex2_JNT": (0.03896263, 0.00286875, -0.00000004),
    "l_handIndex3_JNT": (0.02318424, 0.00158303, -0.00000001),
    # Middle
    "l_handMiddle1_JNT": (0.09042166, 0.00054560, 0.01280483),
    "l_handMiddle2_JNT": (0.03918027, 0.00055923, -0.00000003),
    "l_handMiddle3_JNT": (0.02517179, 0.00019623, -0.00000001),
    # Ring
    "l_handRing1_JNT": (0.08765368, -0.00298586, -0.01407511),
    "l_handRing2_JNT": (0.03670795, 0.00003694, 0.00000002),
    "l_handRing3_JNT": (0.02391658, 0.00005747, 0.00000001),
    # Pinky
    "l_handPinky1_JNT": (0.07375719, -0.00989721, -0.03362722),
    "l_handPinky2_JNT": (0.02923453, 0.00065764, 0.00000007),
    "l_handPinky3_JNT": (0.01903052, -0.00013621, 0.00000002),
}
