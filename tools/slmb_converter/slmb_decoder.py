"""
SLMB Decoder: .slmb.xz -> decompress -> parse MotionBundle -> BodyMotionBlock + FaceMotionBlock
Based on ABNT NBR 25606 Annex D.
"""

import struct
import lzma
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from .constants import (
    SLMB_TITLE_KEY, BODY_MOTION_KEY, FACE_MOTION_KEY,
    JOINT_ORDER, NUM_JOINTS, BLENDSHAPE_ID_TO_NAME,
    get_rotation_axes,
)


@dataclass
class JointFrameData:
    """Decoded data for one joint at one frame."""
    # Translation (Type-0 only)
    tx: float = 0.0
    ty: float = 0.0
    tz: float = 0.0
    # Quaternion (Type-0, Type-1) or converted from euler
    qw: float = 1.0
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0
    # Euler angles in degrees (Type-2, Type-3, Type-4) - raw decoded
    euler_x: float = 0.0
    euler_y: float = 0.0
    euler_z: float = 0.0


@dataclass
class BodyMotionBlock:
    """Decoded BodyMotionBlock."""
    num_frames: int = 0
    frame_time: float = 0.0
    # joint_data[slmb_joint_index][frame_index] = JointFrameData
    joint_data: List[List[JointFrameData]] = field(default_factory=list)


@dataclass
class BlendshapeData:
    """Decoded data for one blendshape."""
    blend_shape_id: int = 0
    # frame_index -> weight (0.0 ~ 1.0)
    weights: Dict[int, float] = field(default_factory=dict)


@dataclass
class FaceMotionBlock:
    """Decoded FaceMotionBlock."""
    num_frames: int = 0
    frame_times: List[float] = field(default_factory=list)
    blendshapes: List[BlendshapeData] = field(default_factory=list)


@dataclass
class SLMBData:
    """Complete decoded SLMB data."""
    body: BodyMotionBlock = field(default_factory=BodyMotionBlock)
    face: FaceMotionBlock = field(default_factory=FaceMotionBlock)


# ─── Decompression ───

def decompress_slmb(filepath: str) -> bytes:
    """Decompress .slmb.xz file."""
    with open(filepath, 'rb') as f:
        compressed = f.read()
    return lzma.decompress(compressed, format=lzma.FORMAT_XZ)


# ─── MotionBundle Parser ───

def _parse_bundle_element(data: bytes, offset: int) -> Tuple[bytes, bytes, int]:
    """
    Parse one MotionBundle element.
    Returns (key, payload, new_offset).
    """
    header = data[offset]
    offset += 1

    key_length = ((header >> 5) & 0x07) + 1
    payload_config = header & 0x1F

    key = data[offset:offset + key_length]
    offset += key_length

    if payload_config == 0x1F:
        payload_size = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        payload = data[offset:offset + payload_size]
        offset += payload_size
    elif payload_config == 0:
        payload = b''
    else:
        payload = data[offset:offset + payload_config]
        offset += payload_config

    return key, payload, offset


def parse_motion_bundle(data: bytes) -> Tuple[bytes, bytes]:
    """
    Parse MotionBundle, extract body and face payloads.
    Returns (body_payload, face_payload).
    """
    offset = 0
    body_payload = b''
    face_payload = b''

    while offset < len(data):
        key, payload, offset = _parse_bundle_element(data, offset)

        if key == SLMB_TITLE_KEY:
            continue  # Title element, skip
        elif key == BODY_MOTION_KEY:
            body_payload = payload
        elif key == FACE_MOTION_KEY:
            face_payload = payload

    if not body_payload:
        raise ValueError("MotionBundle missing BodyMotion element")
    if not face_payload:
        raise ValueError("MotionBundle missing FaceMotion element")

    return body_payload, face_payload


# ─── BodyMotionBlock Decoder ───

def decode_body_motion_block(data: bytes) -> BodyMotionBlock:
    """Decode BodyMotionBlock binary (Table D.8)."""
    offset = 0
    bmb = BodyMotionBlock()

    # Header
    bmb.num_frames = struct.unpack_from('<I', data, offset)[0]
    offset += 4
    bmb.frame_time = struct.unpack_from('<f', data, offset)[0]
    offset += 4

    # Initialize joint data
    bmb.joint_data = [[] for _ in range(NUM_JOINTS)]

    # Read each joint's frames in SLMB order
    for slmb_idx, (joint_name, joint_type) in enumerate(JOINT_ORDER):
        frames = []
        for f in range(bmb.num_frames):
            jfd = JointFrameData()

            if joint_type == 0:
                # Type-0: Tx(16), Ty(16), Tz(16), Qx(16s), Qy(16s), Qz(16s)
                tx_raw, ty_raw, tz_raw = struct.unpack_from('<HHH', data, offset)
                offset += 6
                qx_raw, qy_raw, qz_raw = struct.unpack_from('<hhh', data, offset)
                offset += 6

                jfd.tx = tx_raw / 65535.0 - 0.5
                jfd.ty = ty_raw / 65535.0 - 0.5
                jfd.tz = tz_raw / 65535.0 - 0.5
                jfd.qx = qx_raw / 32767.0
                jfd.qy = qy_raw / 32767.0
                jfd.qz = qz_raw / 32767.0
                sum_sq = jfd.qx**2 + jfd.qy**2 + jfd.qz**2
                jfd.qw = math.sqrt(max(0.0, 1.0 - sum_sq))

            elif joint_type == 1:
                # Type-1: Qx(16s), Qy(16s), Qz(16s)
                qx_raw, qy_raw, qz_raw = struct.unpack_from('<hhh', data, offset)
                offset += 6

                jfd.qx = qx_raw / 32767.0
                jfd.qy = qy_raw / 32767.0
                jfd.qz = qz_raw / 32767.0
                sum_sq = jfd.qx**2 + jfd.qy**2 + jfd.qz**2
                jfd.qw = math.sqrt(max(0.0, 1.0 - sum_sq))

            elif joint_type == 2:
                # Type-2: E2(32) = E2x(10) + E2y(10) + E2z(12)
                e2_raw = struct.unpack_from('<I', data, offset)[0]
                offset += 4

                e2x = (e2_raw >> 22) & 0x3FF
                e2y = (e2_raw >> 12) & 0x3FF
                e2z = e2_raw & 0xFFF

                jfd.euler_x = e2x * 180.0 / 1023.0 - 90.0
                jfd.euler_y = e2y * 180.0 / 1023.0 - 90.0
                jfd.euler_z = e2z * 360.0 / 4095.0 - 180.0

                # Convert to quaternion using custom rotation axes
                from .math_utils import euler2quaternion_xyz
                rx, ry, rz = get_rotation_axes(joint_name)
                qw, qx, qy, qz = euler2quaternion_xyz(
                    jfd.euler_x, jfd.euler_y, jfd.euler_z, rx, ry, rz)
                jfd.qw, jfd.qx, jfd.qy, jfd.qz = qw, qx, qy, qz

            elif joint_type == 3:
                # Type-3: E3(8) = z-axis only
                e3_raw = struct.unpack_from('<B', data, offset)[0]
                offset += 1

                jfd.euler_z = e3_raw * 360.0 / 255.0 - 180.0
                jfd.euler_x = 0.0
                jfd.euler_y = 0.0

                # Convert to quaternion
                from .math_utils import euler2quaternion_xyz
                rx, ry, rz = get_rotation_axes(joint_name)
                qw, qx, qy, qz = euler2quaternion_xyz(0, 0, jfd.euler_z, rx, ry, rz)
                jfd.qw, jfd.qx, jfd.qy, jfd.qz = qw, qx, qy, qz

            elif joint_type == 4:
                # Type-4: E4(16) = E4x(8) + E4y(8)
                e4_raw = struct.unpack_from('<H', data, offset)[0]
                offset += 2

                e4x = (e4_raw >> 8) & 0xFF
                e4y = e4_raw & 0xFF

                jfd.euler_x = e4x * 180.0 / 255.0 - 90.0
                jfd.euler_y = e4y * 180.0 / 255.0 - 90.0
                jfd.euler_z = 0.0

                # Convert to quaternion (identity axes for eyes)
                from .math_utils import euler2quaternion_xyz
                qw, qx, qy, qz = euler2quaternion_xyz(
                    jfd.euler_x, jfd.euler_y, 0,
                    (1, 0, 0), (0, 1, 0), (0, 0, 1))
                jfd.qw, jfd.qx, jfd.qy, jfd.qz = qw, qx, qy, qz

            frames.append(jfd)

        bmb.joint_data[slmb_idx] = frames

    return bmb


# ─── FaceMotionBlock Decoder ───

def decode_face_motion_block(data: bytes) -> FaceMotionBlock:
    """Decode FaceMotionBlock binary (Table D.10)."""
    offset = 0
    fmb = FaceMotionBlock()

    # number_of_frames: 16-bit
    fmb.num_frames = struct.unpack_from('<H', data, offset)[0]
    offset += 2

    # frame_time array
    for _ in range(fmb.num_frames):
        t = struct.unpack_from('<f', data, offset)[0]
        offset += 4
        fmb.frame_times.append(t)

    # number_of_blend_shapes: 16-bit
    num_bs = struct.unpack_from('<H', data, offset)[0]
    offset += 2

    for _ in range(num_bs):
        bs = BlendshapeData()

        # blend_shape_id: 16-bit
        bs.blend_shape_id = struct.unpack_from('<H', data, offset)[0]
        offset += 2

        # number_of_frame_ranges: 16-bit
        num_ranges = struct.unpack_from('<H', data, offset)[0]
        offset += 2

        # Read ranges
        ranges = []
        total_frames_in_ranges = 0
        for _ in range(num_ranges):
            first = struct.unpack_from('<H', data, offset)[0]
            offset += 2
            size = struct.unpack_from('<H', data, offset)[0]
            offset += 2
            ranges.append((first, size))
            total_frames_in_ranges += size

        # Read weights for all frames in ranges
        weight_idx = 0
        for first, size in ranges:
            for fi in range(size):
                w_raw = struct.unpack_from('<H', data, offset)[0]
                offset += 2
                frame_idx = first + fi
                bs.weights[frame_idx] = w_raw / 65535.0

        fmb.blendshapes.append(bs)

    return fmb


# ─── High-Level API ───

def decode_slmb_file(filepath: str) -> SLMBData:
    """
    Decode .slmb.xz file to SLMBData.
    Steps: decompress -> parse bundle -> decode body + face blocks.
    """
    # Decompress
    raw = decompress_slmb(filepath)

    # Parse bundle
    body_payload, face_payload = parse_motion_bundle(raw)

    # Decode blocks
    result = SLMBData()
    result.body = decode_body_motion_block(body_payload)
    result.face = decode_face_motion_block(face_payload)

    return result


def decode_slmb_bytes(data: bytes) -> SLMBData:
    """Decode raw (already decompressed) MotionBundle bytes."""
    body_payload, face_payload = parse_motion_bundle(data)
    result = SLMBData()
    result.body = decode_body_motion_block(body_payload)
    result.face = decode_face_motion_block(face_payload)
    return result
