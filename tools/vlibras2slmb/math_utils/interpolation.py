"""Keyframe resampling utilities for VLibras-to-SLMB conversion.

VLibras AnimationClip data contains variable-rate keyframes: each bone
may have a different number of keyframes at irregular time stamps.
SLMB requires uniform frames at a fixed ``frame_time`` interval.

This module provides resampling functions that convert variable keyframes
to a uniform time grid using appropriate interpolation (SLERP for
quaternions, linear for positions and blendshape weights).
"""

import math
from typing import List, Tuple

import numpy as np

from . import quaternion as qops


def calculate_num_frames(sample_rate: float, duration: float) -> int:
    """Calculate the number of uniform frames for a given sample rate and duration.

    The formula is ``ceil(sample_rate * duration) + 1`` so that the last
    frame falls at or just past the animation end time.

    Args:
        sample_rate: Frames per second (e.g. 30.0 for 30 fps).
        duration: Total animation duration in seconds.

    Returns:
        Number of frames (always >= 1).

    Raises:
        ValueError: If *sample_rate* or *duration* is not positive.
    """
    if sample_rate <= 0.0:
        raise ValueError(f"sample_rate must be positive, got {sample_rate}")
    if duration < 0.0:
        raise ValueError(f"duration must be non-negative, got {duration}")
    if duration == 0.0:
        return 1
    return math.ceil(sample_rate * duration) + 1


def _find_surrounding_keyframes(
    keyframes: List[Tuple[float, np.ndarray]],
    t: float,
) -> Tuple[int, int]:
    """Return indices of the two keyframes surrounding time *t*.

    If *t* is before the first keyframe, returns (0, 0).
    If *t* is after the last keyframe, returns (last, last).
    """
    n = len(keyframes)
    if n == 0:
        raise ValueError("keyframes list is empty")
    if n == 1 or t <= keyframes[0][0]:
        return (0, 0)
    if t >= keyframes[-1][0]:
        return (n - 1, n - 1)

    # Binary search for the interval containing t.
    lo, hi = 0, n - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if keyframes[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    return (lo, hi)


def _lerp_factor(t: float, t0: float, t1: float) -> float:
    """Compute the linear interpolation factor for *t* in [t0, t1]."""
    span = t1 - t0
    if abs(span) < 1e-12:
        return 0.0
    return (t - t0) / span


def resample_quaternions(
    keyframes: List[Tuple[float, np.ndarray]],
    num_frames: int,
    duration: float,
) -> List[np.ndarray]:
    """Resample variable quaternion keyframes to a uniform frame grid.

    Uses SLERP interpolation between surrounding keyframes.  Each
    quaternion is expected in ``(w, x, y, z)`` convention.

    Args:
        keyframes: List of ``(time, quaternion)`` pairs sorted by time.
            Each quaternion is a numpy array ``[w, x, y, z]``.
        num_frames: Number of output frames on the uniform grid.
        duration: Total animation duration in seconds.

    Returns:
        List of *num_frames* quaternion arrays ``[w, x, y, z]``.

    Raises:
        ValueError: If *keyframes* is empty or *num_frames* < 1.
    """
    if not keyframes:
        raise ValueError("keyframes list must not be empty")
    if num_frames < 1:
        raise ValueError(f"num_frames must be >= 1, got {num_frames}")

    # Single frame or single keyframe: constant output.
    if num_frames == 1 or len(keyframes) == 1:
        value = qops.normalize(np.asarray(keyframes[0][1], dtype=np.float64))
        return [value.copy() for _ in range(num_frames)]

    frame_time = duration / (num_frames - 1) if num_frames > 1 else 0.0
    result: List[np.ndarray] = []

    for i in range(num_frames):
        t = i * frame_time
        lo, hi = _find_surrounding_keyframes(keyframes, t)

        if lo == hi:
            q = qops.normalize(np.asarray(keyframes[lo][1], dtype=np.float64))
        else:
            alpha = _lerp_factor(t, keyframes[lo][0], keyframes[hi][0])
            q1 = np.asarray(keyframes[lo][1], dtype=np.float64)
            q2 = np.asarray(keyframes[hi][1], dtype=np.float64)
            q = qops.slerp(q1, q2, alpha)

        result.append(q)

    return result


def resample_positions(
    keyframes: List[Tuple[float, np.ndarray]],
    num_frames: int,
    duration: float,
) -> List[np.ndarray]:
    """Resample variable position keyframes to a uniform frame grid.

    Uses linear interpolation between surrounding keyframes.

    Args:
        keyframes: List of ``(time, position)`` pairs sorted by time.
            Each position is a numpy array ``[x, y, z]``.
        num_frames: Number of output frames on the uniform grid.
        duration: Total animation duration in seconds.

    Returns:
        List of *num_frames* position arrays ``[x, y, z]``.

    Raises:
        ValueError: If *keyframes* is empty or *num_frames* < 1.
    """
    if not keyframes:
        raise ValueError("keyframes list must not be empty")
    if num_frames < 1:
        raise ValueError(f"num_frames must be >= 1, got {num_frames}")

    if num_frames == 1 or len(keyframes) == 1:
        value = np.asarray(keyframes[0][1], dtype=np.float64)
        return [value.copy() for _ in range(num_frames)]

    frame_time = duration / (num_frames - 1) if num_frames > 1 else 0.0
    result: List[np.ndarray] = []

    for i in range(num_frames):
        t = i * frame_time
        lo, hi = _find_surrounding_keyframes(keyframes, t)

        if lo == hi:
            pos = np.asarray(keyframes[lo][1], dtype=np.float64).copy()
        else:
            alpha = _lerp_factor(t, keyframes[lo][0], keyframes[hi][0])
            p1 = np.asarray(keyframes[lo][1], dtype=np.float64)
            p2 = np.asarray(keyframes[hi][1], dtype=np.float64)
            pos = p1 + alpha * (p2 - p1)

        result.append(pos)

    return result


def resample_weights(
    keyframes: List[Tuple[float, float]],
    num_frames: int,
    duration: float,
) -> List[float]:
    """Resample variable blendshape weight keyframes to a uniform frame grid.

    Uses linear interpolation between surrounding keyframes.

    Args:
        keyframes: List of ``(time, weight)`` pairs sorted by time.
        num_frames: Number of output frames on the uniform grid.
        duration: Total animation duration in seconds.

    Returns:
        List of *num_frames* float weight values.

    Raises:
        ValueError: If *keyframes* is empty or *num_frames* < 1.
    """
    if not keyframes:
        raise ValueError("keyframes list must not be empty")
    if num_frames < 1:
        raise ValueError(f"num_frames must be >= 1, got {num_frames}")

    if num_frames == 1 or len(keyframes) == 1:
        return [float(keyframes[0][1])] * num_frames

    frame_time = duration / (num_frames - 1) if num_frames > 1 else 0.0
    result: List[float] = []

    for i in range(num_frames):
        t = i * frame_time
        lo, hi = _find_surrounding_keyframes(keyframes, t)

        if lo == hi:
            w = float(keyframes[lo][1])
        else:
            alpha = _lerp_factor(t, keyframes[lo][0], keyframes[hi][0])
            w1 = float(keyframes[lo][1])
            w2 = float(keyframes[hi][1])
            w = w1 + alpha * (w2 - w1)

        result.append(w)

    return result
