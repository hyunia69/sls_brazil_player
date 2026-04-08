"""Roundtrip verification for SLMB encode/decode fidelity.

Decodes BodyMotionBlock and FaceMotionBlock binary data back to their
semantic representations and compares against original source data to
quantify encoding loss.

Decoding follows the SLMB->BVH pseudocode from OG-06 D.2.4.4.
"""

from __future__ import annotations

import math
import struct
from typing import Any

import numpy as np

from ..data.joint_types import JOINT_ENCODING_ORDER, JOINT_TYPE
from ..data.rotation_axes import ROTATION_AXES
from ..math_utils.euler import euler2quaternion_xyz, rotationaxis_to_quaternion
from ..math_utils import quaternion


# ---------------------------------------------------------------------------
# BodyMotionBlock decoder
# ---------------------------------------------------------------------------

def _decode_type0_frame(data: bytes, offset: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Decode a Type-0 frame. Returns (position, quaternion, new_offset)."""
    tx = struct.unpack_from("<H", data, offset)[0]; offset += 2
    ty = struct.unpack_from("<H", data, offset)[0]; offset += 2
    tz = struct.unpack_from("<H", data, offset)[0]; offset += 2

    px = tx / 65535.0 - 0.5
    py = ty / 65535.0 - 0.5
    pz = tz / 65535.0 - 0.5
    position = np.array([px, py, pz])

    qx_raw = struct.unpack_from("<h", data, offset)[0]; offset += 2
    qy_raw = struct.unpack_from("<h", data, offset)[0]; offset += 2
    qz_raw = struct.unpack_from("<h", data, offset)[0]; offset += 2

    qx = qx_raw / 32767.0
    qy = qy_raw / 32767.0
    qz = qz_raw / 32767.0

    # Reconstruct qw (always positive in SLMB)
    sum_sq = qx * qx + qy * qy + qz * qz
    qw = math.sqrt(max(0.0, 1.0 - sum_sq))

    quaternion = np.array([qw, qx, qy, qz])
    return position, quaternion, offset


def _decode_type1_frame(data: bytes, offset: int) -> tuple[np.ndarray, int]:
    """Decode a Type-1 frame. Returns (quaternion, new_offset)."""
    qx_raw = struct.unpack_from("<h", data, offset)[0]; offset += 2
    qy_raw = struct.unpack_from("<h", data, offset)[0]; offset += 2
    qz_raw = struct.unpack_from("<h", data, offset)[0]; offset += 2

    qx = qx_raw / 32767.0
    qy = qy_raw / 32767.0
    qz = qz_raw / 32767.0

    sum_sq = qx * qx + qy * qy + qz * qz
    qw = math.sqrt(max(0.0, 1.0 - sum_sq))

    return np.array([qw, qx, qy, qz]), offset


def _decode_type2_frame(
    data: bytes, offset: int, joint_name: str,
) -> tuple[np.ndarray, int]:
    """Decode a Type-2 frame. Returns (quaternion, new_offset)."""
    packed = struct.unpack_from("<I", data, offset)[0]; offset += 4

    e2x = (packed >> 22) & 0x3FF
    e2y = (packed >> 12) & 0x3FF
    e2z = packed & 0xFFF

    Ex_deg = e2x / 1023.0 * 180.0 - 90.0
    Ey_deg = e2y / 1023.0 * 180.0 - 90.0
    Ez_deg = e2z / 4095.0 * 360.0 - 180.0

    axes = ROTATION_AXES[joint_name]
    RX, RY, RZ = axes

    q = euler2quaternion_xyz(
        math.radians(Ex_deg), math.radians(Ey_deg), math.radians(Ez_deg),
        RX, RY, RZ,
    )
    return q, offset


def _decode_type3_frame(
    data: bytes, offset: int, joint_name: str,
) -> tuple[np.ndarray, int]:
    """Decode a Type-3 frame using swing-twist reconstruction.

    The encoder stores the twist angle around the joint's RZ axis.
    Reconstruction: build a quaternion for rotation of Ez degrees
    around RZ.  This is already a world-space rotation (no Qr needed),
    matching the swing-twist decomposition used by the encoder.
    """
    e3 = struct.unpack_from("B", data, offset)[0]; offset += 1
    Ez_deg = e3 / 255.0 * 360.0 - 180.0

    axes = ROTATION_AXES[joint_name]
    _RX, _RY, RZ = axes

    # Quaternion for rotation of Ez_deg around RZ axis (world space)
    half = math.radians(Ez_deg) / 2.0
    rz = np.array(RZ, dtype=np.float64)
    rz_len = np.linalg.norm(rz)
    if rz_len > 1e-12:
        rz = rz / rz_len
    q = np.array([math.cos(half), math.sin(half)*rz[0],
                  math.sin(half)*rz[1], math.sin(half)*rz[2]])
    return q, offset


def _decode_type4_frame(
    data: bytes, offset: int, joint_name: str,
) -> tuple[np.ndarray, int]:
    """Decode a Type-4 frame. Returns (quaternion, new_offset)."""
    packed = struct.unpack_from("<H", data, offset)[0]; offset += 2

    e4x = (packed >> 8) & 0xFF
    e4y = packed & 0xFF

    Ex_deg = e4x / 255.0 * 180.0 - 90.0
    Ey_deg = e4y / 255.0 * 180.0 - 90.0

    axes = ROTATION_AXES[joint_name]
    RX, RY, RZ = axes

    q = euler2quaternion_xyz(
        math.radians(Ex_deg), math.radians(Ey_deg), 0.0,
        RX, RY, RZ,
    )
    return q, offset


def decode_body_motion_block(data: bytes) -> dict[str, Any]:
    """Decode BodyMotionBlock binary back to semantic data.

    Args:
        data: Raw BodyMotionBlock bytes.

    Returns:
        Dictionary with keys:
            - 'num_frames': int
            - 'frame_time': float
            - 'joint_rotations': dict[str, list[np.ndarray]]
            - 'root_translations': list[np.ndarray]
    """
    offset = 0
    num_frames = struct.unpack_from("<I", data, offset)[0]; offset += 4
    frame_time = struct.unpack_from("<f", data, offset)[0]; offset += 4

    joint_rotations: dict[str, list[np.ndarray]] = {}
    root_translations: list[np.ndarray] = []

    for _idx, joint_name, joint_type in JOINT_ENCODING_ORDER:
        rotations: list[np.ndarray] = []

        for _frame in range(num_frames):
            if joint_type == 0:
                pos, q, offset = _decode_type0_frame(data, offset)
                root_translations.append(pos)
                rotations.append(q)
            elif joint_type == 1:
                q, offset = _decode_type1_frame(data, offset)
                rotations.append(q)
            elif joint_type == 2:
                q, offset = _decode_type2_frame(data, offset, joint_name)
                rotations.append(q)
            elif joint_type == 3:
                q, offset = _decode_type3_frame(data, offset, joint_name)
                rotations.append(q)
            elif joint_type == 4:
                q, offset = _decode_type4_frame(data, offset, joint_name)
                rotations.append(q)
            else:
                raise ValueError(f"Unknown joint type {joint_type}")

        joint_rotations[joint_name] = rotations

    return {
        "num_frames": num_frames,
        "frame_time": frame_time,
        "joint_rotations": joint_rotations,
        "root_translations": root_translations,
    }


# ---------------------------------------------------------------------------
# FaceMotionBlock decoder
# ---------------------------------------------------------------------------

def decode_face_motion_block(data: bytes) -> dict[str, Any]:
    """Decode FaceMotionBlock binary back to semantic data.

    Args:
        data: Raw FaceMotionBlock bytes.

    Returns:
        Dictionary with keys:
            - 'num_frames': int
            - 'frame_times': list[float]
            - 'num_blendshapes': int
            - 'blendshape_weights': dict[int, list[float]]
    """
    offset = 0
    num_frames = struct.unpack_from("<H", data, offset)[0]; offset += 2

    frame_times: list[float] = []
    for _ in range(num_frames):
        t = struct.unpack_from("<f", data, offset)[0]; offset += 4
        frame_times.append(t)

    num_blendshapes = struct.unpack_from("<H", data, offset)[0]; offset += 2

    blendshape_weights: dict[int, list[float]] = {}

    for _ in range(num_blendshapes):
        bs_id = struct.unpack_from("<H", data, offset)[0]; offset += 2
        num_ranges = struct.unpack_from("<H", data, offset)[0]; offset += 2

        # Read all range headers
        ranges: list[tuple[int, int]] = []
        for _ in range(num_ranges):
            first = struct.unpack_from("<H", data, offset)[0]; offset += 2
            size = struct.unpack_from("<H", data, offset)[0]; offset += 2
            ranges.append((first, size))

        # Initialize all weights to zero
        weights = [0.0] * num_frames

        # Read weight values for each range
        for first, size in ranges:
            for j in range(size):
                raw = struct.unpack_from("<H", data, offset)[0]; offset += 2
                frame_idx = first + j
                if frame_idx < num_frames:
                    weights[frame_idx] = raw / 65535.0

        blendshape_weights[bs_id] = weights

    return {
        "num_frames": num_frames,
        "frame_times": frame_times,
        "num_blendshapes": num_blendshapes,
        "blendshape_weights": blendshape_weights,
    }


# ---------------------------------------------------------------------------
# MotionBundle parser
# ---------------------------------------------------------------------------

def parse_motion_bundle(data: bytes) -> dict[str, bytes]:
    """Parse a MotionBundle into its constituent elements.

    Args:
        data: Raw MotionBundle bytes (decompressed).

    Returns:
        Dictionary with keys 'title', 'body', 'face' mapping to
        the raw payload bytes of each element.

    Raises:
        ValueError: If the bundle structure is invalid or the SLMB
            title signature is missing.
    """
    result: dict[str, bytes] = {}
    offset = 0
    length = len(data)

    while offset < length:
        if offset >= length:
            break

        header = data[offset]; offset += 1
        key_len = ((header >> 5) & 0x07) + 1
        payload_config = header & 0x1F

        if offset + key_len > length:
            raise ValueError(
                f"MotionBundle truncated at offset {offset}: "
                f"expected {key_len} key bytes"
            )

        key = data[offset:offset + key_len]; offset += key_len

        if payload_config == 0x1F:
            if offset + 4 > length:
                raise ValueError(
                    f"MotionBundle truncated at offset {offset}: "
                    f"expected 4-byte payload size"
                )
            payload_size = struct.unpack_from("<I", data, offset)[0]
            offset += 4
        else:
            payload_size = payload_config

        if offset + payload_size > length:
            raise ValueError(
                f"MotionBundle truncated at offset {offset}: "
                f"expected {payload_size} payload bytes"
            )

        payload = data[offset:offset + payload_size]
        offset += payload_size

        # Identify element by key
        if key == bytes([0x53, 0x4C, 0x4D, 0x42]):
            result["title"] = payload
        elif key == bytes([0x01, 0x01]):
            result["body"] = payload
        elif key == bytes([0x02, 0x01]):
            result["face"] = payload
        else:
            # Store unknown elements by hex key
            result[f"unknown_{key.hex()}"] = payload

    if "title" not in result:
        raise ValueError("MotionBundle missing SLMB title element")

    return result


# ---------------------------------------------------------------------------
# Roundtrip validation
# ---------------------------------------------------------------------------

def _quaternion_distance(q1: np.ndarray, q2: np.ndarray) -> float:
    """Compute the angular distance between two unit quaternions.

    Uses the formula: distance = 1 - |dot(q1, q2)|
    Returns a value in [0, 1] where 0 means identical rotations.
    """
    dot = abs(np.dot(quaternion.normalize(q1), quaternion.normalize(q2)))
    return 1.0 - min(dot, 1.0)


def validate_roundtrip(
    original_clip: Any,
    slmb_path: str,
    max_quat_error: float = 0.01,
) -> dict[str, Any]:
    """Full roundtrip validation of an SLMB file against original data.

    Steps:
        1. Read and decompress .slmb.xz
        2. Parse MotionBundle
        3. Decode Body/Face blocks
        4. Re-retarget the original clip
        5. Compare quaternion rotations per joint per frame
        6. Report error statistics

    Args:
        original_clip: AnimationClipData from the parsing module.
        slmb_path: Path to the .slmb.xz file to validate.
        max_quat_error: Maximum acceptable quaternion distance.

    Returns:
        Dictionary with validation results:
            - 'max_quat_error': float (worst error across all joints/frames)
            - 'mean_quat_error': float
            - 'per_joint_max_error': dict[str, float]
            - 'passed': bool
    """
    from ..encoding.slmb_writer import read_slmb
    from ..retarget.body_retarget import retarget_body

    raw = read_slmb(slmb_path)
    bundle = parse_motion_bundle(raw)

    if "body" not in bundle:
        return {
            "max_quat_error": float("inf"),
            "mean_quat_error": float("inf"),
            "per_joint_max_error": {},
            "passed": False,
            "error": "No body block in MotionBundle",
        }

    decoded = decode_body_motion_block(bundle["body"])
    original = retarget_body(original_clip)

    per_joint_max: dict[str, float] = {}
    all_errors: list[float] = []

    for _idx, joint_name, _jtype in JOINT_ENCODING_ORDER:
        orig_rots = original.joint_rotations.get(joint_name, [])
        dec_rots = decoded["joint_rotations"].get(joint_name, [])

        num_compare = min(len(orig_rots), len(dec_rots))
        joint_max = 0.0

        for f in range(num_compare):
            err = _quaternion_distance(orig_rots[f], dec_rots[f])
            all_errors.append(err)
            joint_max = max(joint_max, err)

        per_joint_max[joint_name] = joint_max

    overall_max = max(all_errors) if all_errors else 0.0
    overall_mean = float(np.mean(all_errors)) if all_errors else 0.0

    return {
        "max_quat_error": overall_max,
        "mean_quat_error": overall_mean,
        "per_joint_max_error": per_joint_max,
        "passed": overall_max < max_quat_error,
    }
