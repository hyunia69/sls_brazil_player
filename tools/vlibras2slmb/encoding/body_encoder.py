"""SLMB BodyMotionBlock binary encoder per ABNT NBR 25606 Table D.8.

Encodes retargeted body motion data (uniform-frame quaternion rotations
and root translations) into the compact binary representation used inside
a MotionBundle.

Encoding types (Table D.9):
    Type 0 -- Root (hips_JNT): position uint16x3 + quaternion int16x3
    Type 1 -- Standard joints: quaternion int16x3 (smallest-three)
    Type 2 -- Palm joints:     packed euler uint32 (10|10|12 bits)
    Type 3 -- Finger joints:   packed euler uint8 (Z-axis only)
    Type 4 -- Eye joints:      packed euler uint16 (8|8 bits)
"""

from __future__ import annotations

import math
import struct
from typing import TYPE_CHECKING

import numpy as np

from ..data.joint_types import JOINT_ENCODING_ORDER, JOINT_TYPE
from ..data.rotation_axes import ROTATION_AXES
from ..math_utils.euler import quaternion2euler_xyz
from ..math_utils.quaternion import ensure_positive_w

if TYPE_CHECKING:
    from typing import Protocol

    class BodyMotionData(Protocol):
        num_frames: int
        frame_time: float
        joint_rotations: dict[str, list[np.ndarray]]
        root_translations: list[np.ndarray]


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _encode_type0_frame(
    position: np.ndarray,
    quaternion: np.ndarray,
    buf: bytearray,
) -> None:
    """Encode a single Type-0 frame (root joint) into *buf*.

    Position is quantized to uint16 with offset +0.5:
        Tx = (x + 0.5) * 65535, clamped to [0, 65535]

    Quaternion is stored as smallest-three int16:
        Qc = qc * 32767, clamped to [-32767, 32767]
    """
    q = ensure_positive_w(quaternion)

    for i in range(3):
        raw = (position[i] + 0.5) * 65535.0
        val = int(round(_clamp(raw, 0.0, 65535.0)))
        buf += struct.pack("<H", val)

    for i in range(1, 4):  # qx, qy, qz
        raw = q[i] * 32767.0
        val = int(round(_clamp(raw, -32767.0, 32767.0)))
        buf += struct.pack("<h", val)


def _encode_type1_frame(quaternion: np.ndarray, buf: bytearray) -> None:
    """Encode a single Type-1 frame (standard joint) into *buf*.

    Smallest-three encoding: store qx, qy, qz as int16.
    """
    q = ensure_positive_w(quaternion)

    for i in range(1, 4):
        raw = q[i] * 32767.0
        val = int(round(_clamp(raw, -32767.0, 32767.0)))
        buf += struct.pack("<h", val)


def _encode_type2_frame(
    quaternion: np.ndarray,
    joint_name: str,
    buf: bytearray,
) -> None:
    """Encode a single Type-2 frame (palm joint) into *buf*.

    Quaternion is converted to custom-axis Euler angles, then packed
    into a single uint32:
        E2x = (Ex + 90) / 180 * 1023  -> upper 10 bits
        E2y = (Ey + 90) / 180 * 1023  -> middle 10 bits
        E2z = (Ez + 180) / 360 * 4095 -> lower 12 bits
        E2  = (E2x << 22) | (E2y << 12) | E2z
    """
    axes = ROTATION_AXES[joint_name]
    RX, RY, RZ = axes

    Ex, Ey, Ez = quaternion2euler_xyz(
        quaternion[0], quaternion[1], quaternion[2], quaternion[3],
        RX, RY, RZ,
    )

    e2x = int(round(_clamp((Ex + 90.0) / 180.0 * 1023.0, 0.0, 1023.0)))
    e2y = int(round(_clamp((Ey + 90.0) / 180.0 * 1023.0, 0.0, 1023.0)))
    e2z = int(round(_clamp((Ez + 180.0) / 360.0 * 4095.0, 0.0, 4095.0)))

    packed = (e2x << 22) | (e2y << 12) | e2z
    buf += struct.pack("<I", packed)


def _encode_type3_frame(
    quaternion: np.ndarray,
    joint_name: str,
    buf: bytearray,
) -> None:
    """Encode a single Type-3 frame (finger phalanx) into *buf*.

    Only the Z-axis Euler angle is stored as a single uint8:
        E3 = (Ez + 180) / 360 * 255

    Uses swing-twist decomposition to extract the rotation angle
    around RZ directly, avoiding numerical instability when the
    rotation axes define a ~180°-rotated frame (right-hand joints).
    """
    axes = ROTATION_AXES[joint_name]
    _RX, _RY, RZ = axes

    # Swing-twist decomposition: extract twist angle around RZ axis.
    # For quaternion Q = [w, x, y, z], project rotation axis onto RZ.
    w, x, y, z = quaternion
    rz = np.array(RZ)

    # Project imaginary part onto RZ to get twist component
    imag = np.array([x, y, z])
    proj = np.dot(imag, rz)  # projection of rotation axis onto RZ

    # Twist quaternion: [w, proj*RZ]
    twist_w = w
    twist_xyz = proj * rz

    # Normalize twist quaternion
    twist_norm = math.sqrt(twist_w * twist_w + proj * proj)
    if twist_norm < 1e-12:
        Ez = 0.0
    else:
        twist_w /= twist_norm
        proj /= twist_norm
        # Twist angle = 2 * atan2(|proj|, twist_w)
        # Sign: positive if proj > 0 (rotation in RZ direction)
        Ez = math.degrees(2.0 * math.atan2(proj, twist_w))

    val = int(round(_clamp((Ez + 180.0) / 360.0 * 255.0, 0.0, 255.0)))
    buf += struct.pack("B", val)


def _encode_type4_frame(
    quaternion: np.ndarray,
    joint_name: str,
    buf: bytearray,
) -> None:
    """Encode a single Type-4 frame (eye locator) into *buf*.

    The eye rotation is stored as two Euler angles packed into uint16:
        E4x = (Ex + 90) / 180 * 255  -> upper 8 bits
        E4y = (Ey + 90) / 180 * 255  -> lower 8 bits
        E4  = (E4x << 8) | E4y
    """
    axes = ROTATION_AXES[joint_name]
    RX, RY, RZ = axes

    Ex, Ey, _Ez = quaternion2euler_xyz(
        quaternion[0], quaternion[1], quaternion[2], quaternion[3],
        RX, RY, RZ,
    )

    e4x = int(round(_clamp((Ex + 90.0) / 180.0 * 255.0, 0.0, 255.0)))
    e4y = int(round(_clamp((Ey + 90.0) / 180.0 * 255.0, 0.0, 255.0)))

    packed = (e4x << 8) | e4y
    buf += struct.pack("<H", packed)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode_body_motion(body_data: BodyMotionData) -> bytes:
    """Encode BodyMotionData to BodyMotionBlock binary.

    The binary layout is:
        - number_of_frames:  uint32 LE
        - frame_time:        float32 LE (IEEE-754)
        - Per joint (in JOINT_ENCODING_ORDER), per frame:
            Type-0: 6 + 6 = 12 bytes (3x uint16 position + 3x int16 quat)
            Type-1: 6 bytes (3x int16 quat)
            Type-2: 4 bytes (1x uint32 packed euler)
            Type-3: 1 byte  (1x uint8 packed euler)
            Type-4: 2 bytes (1x uint16 packed euler)

    Args:
        body_data: Retargeted body motion data containing:
            - num_frames: total uniform frames
            - frame_time: seconds per frame
            - joint_rotations: joint_name -> list of [w,x,y,z] quaternions
            - root_translations: list of [x,y,z] positions

    Returns:
        Raw bytes of the BodyMotionBlock (uncompressed).

    Raises:
        KeyError: If a required joint is missing from joint_rotations.
        ValueError: If frame counts are inconsistent.
    """
    num_frames = body_data.num_frames
    frame_time = body_data.frame_time

    buf = bytearray()

    # Header
    buf += struct.pack("<I", num_frames)
    buf += struct.pack("<f", frame_time)

    # Encode each joint in canonical order
    for _idx, joint_name, joint_type in JOINT_ENCODING_ORDER:
        rotations = body_data.joint_rotations.get(joint_name)
        if rotations is None:
            raise KeyError(
                f"Missing joint '{joint_name}' in body_data.joint_rotations"
            )
        if len(rotations) != num_frames:
            raise ValueError(
                f"Joint '{joint_name}' has {len(rotations)} frames, "
                f"expected {num_frames}"
            )

        for frame_idx in range(num_frames):
            q = rotations[frame_idx]

            if joint_type == 0:
                pos = body_data.root_translations[frame_idx]
                _encode_type0_frame(pos, q, buf)
            elif joint_type == 1:
                _encode_type1_frame(q, buf)
            elif joint_type == 2:
                _encode_type2_frame(q, joint_name, buf)
            elif joint_type == 3:
                _encode_type3_frame(q, joint_name, buf)
            elif joint_type == 4:
                _encode_type4_frame(q, joint_name, buf)
            else:
                raise ValueError(f"Unknown joint type {joint_type}")

    return bytes(buf)
