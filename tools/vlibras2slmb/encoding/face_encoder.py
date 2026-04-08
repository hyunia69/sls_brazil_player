"""SLMB FaceMotionBlock binary encoder per ABNT NBR 25606 Table D.11.

Encodes retargeted face motion data (blendshape weights at uniform
timestamps) into the compact binary representation used inside a
MotionBundle.

The format uses frame-range compression: for each active blendshape,
only consecutive non-zero weight ranges are stored.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol

    class FaceMotionData(Protocol):
        num_frames: int
        frame_times: list[float]
        blendshape_weights: dict[int, list[float]]


def _find_frame_ranges(
    weights: list[float],
    threshold: float = 1e-6,
) -> list[tuple[int, int]]:
    """Find consecutive ranges of non-zero weights.

    Scans the weight array and groups consecutive frames where
    ``abs(weight) > threshold`` into (first_frame, size) tuples.

    Args:
        weights: Per-frame blendshape weight values.
        threshold: Minimum absolute weight to consider non-zero.

    Returns:
        List of (first_frame_index, range_size) tuples.

    Examples:
        >>> _find_frame_ranges([0, 0.5, 0.8, 0, 0.3])
        [(1, 2), (4, 1)]
        >>> _find_frame_ranges([0, 0, 0])
        []
        >>> _find_frame_ranges([0.1, 0.2, 0.3])
        [(0, 3)]
    """
    ranges: list[tuple[int, int]] = []
    n = len(weights)
    i = 0

    while i < n:
        if abs(weights[i]) > threshold:
            start = i
            while i < n and abs(weights[i]) > threshold:
                i += 1
            ranges.append((start, i - start))
        else:
            i += 1

    return ranges


def encode_face_motion(face_data: FaceMotionData) -> bytes:
    """Encode FaceMotionData to FaceMotionBlock binary.

    The binary layout is:
        - number_of_frames:       uint16 LE
        - frame_time[]:           float32 LE x number_of_frames
        - number_of_blend_shapes: uint16 LE (only active shapes)
        - Per active blendshape:
            - blend_shape_id:           uint16 LE
            - number_of_frame_ranges:   uint16 LE
            - Per frame_range:
                - frame_range_first:    uint16 LE
                - frame_range_size:     uint16 LE
            - Per frame in all ranges (concatenated):
                - blend_shape_weight:   uint16 LE  (weight * 65535)

    A blendshape is "active" if it has at least one frame range with
    non-zero weights.  Inactive blendshapes are omitted entirely.

    Args:
        face_data: Retargeted face motion data containing:
            - num_frames: total uniform frames
            - frame_times: list of float timestamps per frame
            - blendshape_weights: blendshape_id -> list of weights [0..1]

    Returns:
        Raw bytes of the FaceMotionBlock (uncompressed).

    Raises:
        ValueError: If frame_times length does not match num_frames.
    """
    num_frames = face_data.num_frames
    frame_times = face_data.frame_times

    if len(frame_times) != num_frames:
        raise ValueError(
            f"frame_times has {len(frame_times)} entries, "
            f"expected {num_frames}"
        )

    buf = bytearray()

    # Header: number of frames
    buf += struct.pack("<H", num_frames)

    # Frame timestamps
    for t in frame_times:
        buf += struct.pack("<f", t)

    # Collect active blendshapes (those with at least one non-zero range)
    active_shapes: list[tuple[int, list[float], list[tuple[int, int]]]] = []

    for bs_id in sorted(face_data.blendshape_weights.keys()):
        weights = face_data.blendshape_weights[bs_id]
        if len(weights) != num_frames:
            raise ValueError(
                f"Blendshape {bs_id} has {len(weights)} weight frames, "
                f"expected {num_frames}"
            )
        ranges = _find_frame_ranges(weights)
        if ranges:
            active_shapes.append((bs_id, weights, ranges))

    # Number of active blendshapes
    buf += struct.pack("<H", len(active_shapes))

    # Encode each active blendshape
    for bs_id, weights, ranges in active_shapes:
        buf += struct.pack("<H", bs_id)
        buf += struct.pack("<H", len(ranges))

        # Write all range headers first
        for first_frame, size in ranges:
            buf += struct.pack("<H", first_frame)
            buf += struct.pack("<H", size)

        # Write all weight values for all ranges (concatenated)
        for first_frame, size in ranges:
            for offset in range(size):
                w = weights[first_frame + offset]
                quantized = int(round(max(0.0, min(1.0, w)) * 65535.0))
                buf += struct.pack("<H", quantized)

    return bytes(buf)
