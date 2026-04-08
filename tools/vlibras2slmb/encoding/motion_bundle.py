"""SLMB MotionBundle assembly per ABNT NBR 25606 Table D.13.

Assembles the Title element, BodyMotionBlock, and FaceMotionBlock into
a single MotionBundle binary blob ready for LZMA compression.

Each MotionBundle element has:
    header:   1 byte
        upper 3 bits:  (key_length - 1)
        lower 5 bits:  payload_config
            if payload < 31 bytes:   payload_config = payload_size
            if payload >= 31 bytes:  payload_config = 0x1F
    key:      key_length bytes
    [if payload_config == 0x1F]:
        payload_size: uint32 LE
    payload:  payload_size bytes
"""

from __future__ import annotations

import struct

# SLMB well-known keys
_TITLE_KEY = bytes([0x53, 0x4C, 0x4D, 0x42])  # "SLMB"
_BODY_KEY = bytes([0x01, 0x01])
_FACE_KEY = bytes([0x02, 0x01])


def _encode_element(key: bytes, payload: bytes) -> bytes:
    """Encode a single MotionBundle element (header + key + payload).

    Args:
        key: Element key bytes (1-8 bytes long).
        payload: Element payload bytes (may be empty).

    Returns:
        Encoded element bytes.

    Raises:
        ValueError: If key length is outside [1, 8].
    """
    key_len = len(key)
    if not (1 <= key_len <= 8):
        raise ValueError(f"Key length must be 1-8, got {key_len}")

    payload_size = len(payload)
    key_bits = (key_len - 1) & 0x07  # 3 bits

    if payload_size < 31:
        payload_config = payload_size & 0x1F
        header = (key_bits << 5) | payload_config
        return struct.pack("B", header) + key + payload
    else:
        payload_config = 0x1F
        header = (key_bits << 5) | payload_config
        return (
            struct.pack("B", header)
            + key
            + struct.pack("<I", payload_size)
            + payload
        )


def build_motion_bundle(body_block: bytes, face_block: bytes) -> bytes:
    """Assemble a MotionBundle from Body and Face motion blocks.

    The MotionBundle contains three elements in order:
        1. Title element:  key="SLMB", no payload
        2. Body element:   key=[0x01, 0x01], payload=body_block
        3. Face element:   key=[0x02, 0x01], payload=face_block

    Args:
        body_block: Raw BodyMotionBlock bytes from encode_body_motion().
        face_block: Raw FaceMotionBlock bytes from encode_face_motion().

    Returns:
        Complete MotionBundle binary blob.
    """
    title = _encode_element(_TITLE_KEY, b"")
    body = _encode_element(_BODY_KEY, body_block)
    face = _encode_element(_FACE_KEY, face_block)

    return title + body + face
