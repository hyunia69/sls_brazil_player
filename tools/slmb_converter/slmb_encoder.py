"""
SLMB Encoder: BVH + FaceData -> SLMB binary -> .slmb.xz
Based on ABNT NBR 25606 Annex D and SBTVD OG-06 Annex D.
"""

import struct
import lzma
import math
from typing import List, Dict, Tuple, Optional

from .constants import (
    SLMB_TITLE_KEY, BODY_MOTION_KEY, FACE_MOTION_KEY,
    JOINT_ORDER, JOINT_NAME_TO_ORDER, NUM_JOINTS,
    ROTATION_AXES, IDENTITY_AXES, get_rotation_axes,
)
from .math_utils import (
    euler2quaternion_yxz, quaternion2euler_xyz,
    rotationaxis_to_quaternion, quaternion_multiply,
)
from .bvh_parser import BVHData, BVHJoint, get_joint_channels
from .face_data import FaceMotionData


# ─── BodyMotionBlock Encoding ───

def _encode_type0_translation(x: float, y: float, z: float) -> Tuple[int, int, int]:
    """Encode Type-0 translation: [-0.5, 0.5] -> [0, 65535]"""
    tx = int(round((x + 0.5) * 65535))
    ty = int(round((y + 0.5) * 65535))
    tz = int(round((z + 0.5) * 65535))
    return (
        max(0, min(65535, tx)),
        max(0, min(65535, ty)),
        max(0, min(65535, tz)),
    )


def _encode_quaternion(qx: float, qy: float, qz: float) -> Tuple[int, int, int]:
    """Encode quaternion components: [-1, 1] -> [-32767, 32767] as signed 16-bit."""
    iqx = int(round(qx * 32767))
    iqy = int(round(qy * 32767))
    iqz = int(round(qz * 32767))
    return (
        max(-32767, min(32767, iqx)),
        max(-32767, min(32767, iqy)),
        max(-32767, min(32767, iqz)),
    )


def _normalize_euler_xyz_for_type2(ex: float, ey: float, ez: float):
    """
    Normalize XYZ Euler angles so Ex and Ey are within [-90, 90].
    For intrinsic XYZ rotation, if Ex is outside [-90, 90], an equivalent
    representation exists: (180-Ex, 180+Ey, 180+Ez) wrapped to ranges.
    This handles right-hand joints whose custom axes create a 180-deg offset.
    """
    # Wrap to [-180, 180]
    def wrap180(a):
        a = a % 360.0
        if a > 180.0:
            a -= 360.0
        return a

    ex = wrap180(ex)
    ey = wrap180(ey)
    ez = wrap180(ez)

    if ex > 90.0:
        ex = 180.0 - ex
        ey = wrap180(ey + 180.0)
        ez = wrap180(ez + 180.0)
    elif ex < -90.0:
        ex = -180.0 - ex
        ey = wrap180(ey + 180.0)
        ez = wrap180(ez + 180.0)

    return ex, ey, ez


def _encode_type2_euler(ex: float, ey: float, ez: float) -> int:
    """Encode Type-2 euler: E2x(10bit), E2y(10bit), E2z(12bit) packed into 32-bit."""
    ex, ey, ez = _normalize_euler_xyz_for_type2(ex, ey, ez)
    e2x = int(round((ex + 90.0) / 180.0 * 1023))
    e2y = int(round((ey + 90.0) / 180.0 * 1023))
    e2z = int(round((ez + 180.0) / 360.0 * 4095))
    e2x = max(0, min(1023, e2x))
    e2y = max(0, min(1023, e2y))
    e2z = max(0, min(4095, e2z))
    return (e2x << 22) | (e2y << 12) | e2z


def _encode_type3_euler(ez: float) -> int:
    """Encode Type-3 euler: z-axis only, [-180, 180] -> [0, 255]."""
    e3 = int(round((ez + 180.0) / 360.0 * 255))
    return max(0, min(255, e3))


def _encode_type4_euler(ex: float, ey: float) -> int:
    """Encode Type-4 euler: E4x(8bit), E4y(8bit) packed into 16-bit."""
    e4x = int(round((ex + 90.0) / 180.0 * 255))
    e4y = int(round((ey + 90.0) / 180.0 * 255))
    e4x = max(0, min(255, e4x))
    e4y = max(0, min(255, e4y))
    return (e4x << 8) | e4y


def encode_body_motion_block(bvh: BVHData) -> bytes:
    """
    Encode BVH data into BodyMotionBlock binary (Table D.8).
    BVH rotation order: Z, X, Y channels -> applied as Y, X, Z.
    """
    num_frames = bvh.num_frames
    frame_time = bvh.frame_time

    # Build BVH joint name -> joint index mapping
    bvh_joint_map: Dict[str, int] = {}
    for idx, joint in enumerate(bvh.joint_list):
        bvh_joint_map[joint.name] = idx

    # Calculate channel offsets for each BVH joint
    channel_offsets: List[int] = []
    offset = 0
    for joint in bvh.joint_list:
        channel_offsets.append(offset)
        offset += len(joint.channels)

    buf = bytearray()
    # Header: number_of_frames (32-bit uilsbf) + frame_time (32-bit float)
    buf.extend(struct.pack('<I', num_frames))
    buf.extend(struct.pack('<f', frame_time))

    # For each joint in SLMB order (Table D.9), for each frame
    for slmb_idx, (joint_name, joint_type) in enumerate(JOINT_ORDER):
        if joint_name not in bvh_joint_map:
            # Joint not in BVH - write zeros for all frames
            for f in range(num_frames):
                if joint_type == 0:
                    buf.extend(struct.pack('<HHH', 32768, 32768, 32768))  # zero position
                    buf.extend(struct.pack('<hhh', 0, 0, 0))  # identity rotation
                elif joint_type == 1:
                    buf.extend(struct.pack('<hhh', 0, 0, 0))
                elif joint_type == 2:
                    buf.extend(struct.pack('<I', _encode_type2_euler(0, 0, 0)))
                elif joint_type == 3:
                    buf.extend(struct.pack('<B', _encode_type3_euler(0)))
                elif joint_type == 4:
                    buf.extend(struct.pack('<H', _encode_type4_euler(0, 0)))
            continue

        bvh_idx = bvh_joint_map[joint_name]
        bvh_joint = bvh.joint_list[bvh_idx]
        ch_offset = channel_offsets[bvh_idx]

        for f in range(num_frames):
            frame_data = bvh.motion_data[f]

            # Extract channel values
            channels = {}
            for ci, ch_name in enumerate(bvh_joint.channels):
                channels[ch_name] = frame_data[ch_offset + ci]

            x_pos = channels.get("Xposition", 0.0)
            y_pos = channels.get("Yposition", 0.0)
            z_pos = channels.get("Zposition", 0.0)
            x_rot = channels.get("Xrotation", 0.0)
            y_rot = channels.get("Yrotation", 0.0)
            z_rot = channels.get("Zrotation", 0.0)

            if joint_type == 0:
                # Type-0: translation + quaternion
                tx, ty, tz = _encode_type0_translation(x_pos, y_pos, z_pos)
                buf.extend(struct.pack('<HHH', tx, ty, tz))

                qw, qx, qy, qz = euler2quaternion_yxz(
                    x_rot, y_rot, z_rot,
                    (1, 0, 0), (0, 1, 0), (0, 0, 1))
                if qw < 0:
                    qx, qy, qz = -qx, -qy, -qz
                iqx, iqy, iqz = _encode_quaternion(qx, qy, qz)
                buf.extend(struct.pack('<hhh', iqx, iqy, iqz))

            elif joint_type == 1:
                # Type-1: quaternion only
                qw, qx, qy, qz = euler2quaternion_yxz(
                    x_rot, y_rot, z_rot,
                    (1, 0, 0), (0, 1, 0), (0, 0, 1))
                if qw < 0:
                    qx, qy, qz = -qx, -qy, -qz
                iqx, iqy, iqz = _encode_quaternion(qx, qy, qz)
                buf.extend(struct.pack('<hhh', iqx, iqy, iqz))

            elif joint_type == 2:
                # Type-2: BVH euler -> quaternion -> custom-axis euler -> packed 32-bit
                # Pre-multiply Q_bvh * Qr so that quaternion2euler_xyz decomposes
                # Q_rel = (Q_bvh * Qr) * inv(Qr) = Q_bvh, giving small Euler angles
                # even for right-hand joints (whose Qr ≈ 180° Y).
                qw, qx, qy, qz = euler2quaternion_yxz(
                    x_rot, y_rot, z_rot,
                    (1, 0, 0), (0, 1, 0), (0, 0, 1))
                rx, ry, rz = get_rotation_axes(joint_name)
                qr = rotationaxis_to_quaternion(rx, ry, rz)
                q_enc = quaternion_multiply((qw, qx, qy, qz), qr)
                ex, ey, ez = quaternion2euler_xyz(q_enc[0], q_enc[1], q_enc[2], q_enc[3], rx, ry, rz)
                packed = _encode_type2_euler(ex, ey, ez)
                buf.extend(struct.pack('<I', packed))

            elif joint_type == 3:
                # Type-3: BVH euler -> quaternion -> custom-axis euler -> z only 8-bit
                # Same pre-multiply as Type-2.
                qw, qx, qy, qz = euler2quaternion_yxz(
                    x_rot, y_rot, z_rot,
                    (1, 0, 0), (0, 1, 0), (0, 0, 1))
                rx, ry, rz = get_rotation_axes(joint_name)
                qr = rotationaxis_to_quaternion(rx, ry, rz)
                q_enc = quaternion_multiply((qw, qx, qy, qz), qr)
                ex, ey, ez = quaternion2euler_xyz(q_enc[0], q_enc[1], q_enc[2], q_enc[3], rx, ry, rz)
                e3 = _encode_type3_euler(ez)
                buf.extend(struct.pack('<B', e3))

            elif joint_type == 4:
                # Type-4: direct x/y euler encoding
                e4 = _encode_type4_euler(x_rot, y_rot)
                buf.extend(struct.pack('<H', e4))

    return bytes(buf)


# ─── FaceMotionBlock Encoding ───

def encode_face_motion_block(face_data: FaceMotionData) -> bytes:
    """
    Encode FaceMotionData into FaceMotionBlock binary (Table D.10).
    Uses sparse encoding: only non-zero blendshapes and frame ranges.
    """
    buf = bytearray()

    num_frames = face_data.num_frames
    # number_of_frames: 16-bit
    buf.extend(struct.pack('<H', num_frames))

    # frame_time array: each 32-bit float
    for frame in face_data.frames:
        buf.extend(struct.pack('<f', frame.time))

    # Collect all active blendshapes across all frames
    # blendshape_id -> [(frame_idx, weight), ...]
    bs_data: Dict[int, List[Tuple[int, float]]] = {}
    for f_idx, frame in enumerate(face_data.frames):
        for bs_id, weight in frame.weights.items():
            if weight > 0.0:
                if bs_id not in bs_data:
                    bs_data[bs_id] = []
                bs_data[bs_id].append((f_idx, weight))

    # number_of_blend_shapes: 16-bit
    buf.extend(struct.pack('<H', len(bs_data)))

    for bs_id in sorted(bs_data.keys()):
        frame_weights = bs_data[bs_id]

        # blend_shape_id: 16-bit
        buf.extend(struct.pack('<H', bs_id))

        # Build frame ranges from non-zero frame indices
        frame_indices = sorted(set(fw[0] for fw in frame_weights))
        ranges = _build_frame_ranges(frame_indices)

        # number_of_frame_ranges: 16-bit
        buf.extend(struct.pack('<H', len(ranges)))

        # Write ranges
        for first, size in ranges:
            buf.extend(struct.pack('<HH', first, size))

        # Build a lookup for weights
        weight_map = {fw[0]: fw[1] for fw in frame_weights}

        # Write weights for all frames in all ranges
        for first, size in ranges:
            for fi in range(first, first + size):
                w = weight_map.get(fi, 0.0)
                encoded_w = int(round(w * 65535))
                encoded_w = max(0, min(65535, encoded_w))
                buf.extend(struct.pack('<H', encoded_w))

    return bytes(buf)


def _build_frame_ranges(sorted_indices: List[int]) -> List[Tuple[int, int]]:
    """Convert sorted frame indices to (first, size) ranges."""
    if not sorted_indices:
        return []

    ranges = []
    first = sorted_indices[0]
    prev = first

    for idx in sorted_indices[1:]:
        if idx == prev + 1:
            prev = idx
        else:
            ranges.append((first, prev - first + 1))
            first = idx
            prev = idx

    ranges.append((first, prev - first + 1))
    return ranges


# ─── MotionBundle Encoding (Table D.12, D.13) ───

def _encode_bundle_element(key: bytes, payload: bytes) -> bytes:
    """Encode a single MotionBundle element with header, key, and payload."""
    key_length = len(key)
    payload_size = len(payload)

    # Header byte: upper 3 bits = key_length - 1, lower 5 bits = payload config
    key_size_field = (key_length - 1) & 0x07

    if payload_size == 0:
        # Empty payload
        header = (key_size_field << 5) | 0x00
        return bytes([header]) + key
    elif payload_size < 31:
        header = (key_size_field << 5) | (payload_size & 0x1F)
        return bytes([header]) + key + payload
    else:
        # payload_config = 0x1F, followed by 32-bit payload size
        header = (key_size_field << 5) | 0x1F
        buf = bytes([header]) + key
        buf += struct.pack('<I', payload_size)
        buf += payload
        return buf


def encode_motion_bundle(body_block: bytes, face_block: bytes) -> bytes:
    """
    Encode MotionBundle: Title + BodyMotion + FaceMotion.
    """
    bundle = bytearray()

    # Title element: key="SLMB", empty payload
    bundle.extend(_encode_bundle_element(SLMB_TITLE_KEY, b''))

    # Body motion element: key={0x01, 0x01}, payload=BodyMotionBlock
    bundle.extend(_encode_bundle_element(BODY_MOTION_KEY, body_block))

    # Face motion element: key={0x02, 0x01}, payload=FaceMotionBlock
    bundle.extend(_encode_bundle_element(FACE_MOTION_KEY, face_block))

    return bytes(bundle)


# ─── LZMA/xz Compression ───

def compress_slmb(motion_bundle: bytes) -> bytes:
    """Compress MotionBundle with LZMA in xz format."""
    return lzma.compress(motion_bundle, format=lzma.FORMAT_XZ)


# ─── High-Level API ───

def bvh_to_slmb(bvh: BVHData, face_data: FaceMotionData, output_path: str) -> str:
    """
    Convert BVH + face data to .slmb.xz file.
    Returns the output file path.
    """
    # Encode body motion
    body_block = encode_body_motion_block(bvh)

    # Encode face motion
    face_block = encode_face_motion_block(face_data)

    # Bundle
    bundle = encode_motion_bundle(body_block, face_block)

    # Compress
    compressed = compress_slmb(bundle)

    # Write file
    if not output_path.endswith('.slmb.xz'):
        output_path += '.slmb.xz'

    with open(output_path, 'wb') as f:
        f.write(compressed)

    return output_path
