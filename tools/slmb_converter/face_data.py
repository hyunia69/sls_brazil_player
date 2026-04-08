"""Generate sample face animation data for testing SLMB encoding.

The SLMB FaceMotionBlock stores blendshape weights (0.0~1.0) for 68
possible blendshapes per frame across multiple meshes. This module
provides functions to generate realistic face animation data that
simulates sign language facial expressions.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class FaceFrame:
    """A single frame of face animation data.

    Attributes:
        time: Timestamp in seconds.
        weights: Mapping of blendshape_id to weight (0.0~1.0).
            Only non-zero entries are stored.
    """
    time: float
    weights: Dict[int, float]


@dataclass
class FaceMotionData:
    """Container for a sequence of face animation frames.

    Attributes:
        num_frames: Total number of frames.
        frames: Ordered list of FaceFrame instances.
    """
    num_frames: int
    frames: List[FaceFrame]


# ---------------------------------------------------------------------------
# Blendshape ID constants
# ---------------------------------------------------------------------------

# head_GEO blendshapes
BS_EYE_BLINK_LEFT = 0
BS_EYE_BLINK_RIGHT = 1
BS_EYE_OPEN_LEFT = 8
BS_EYE_OPEN_RIGHT = 9
BS_BROWS_DOWN_LEFT = 14
BS_BROWS_DOWN_RIGHT = 15
BS_BROWS_UP_CENTER = 16
BS_BROWS_UP_LEFT = 17
BS_BROWS_UP_RIGHT = 18
BS_JAW_OPEN = 21
BS_MOUTH_SMILE_LEFT = 28
BS_MOUTH_SMILE_RIGHT = 29
BS_LIPS_PUCKER = 41
BS_HAPPY = 48

# mouth_GEO blendshapes (offset 1000)
BS_MOUTH_JAW_OPEN = 1021

# eyelash_GEO blendshapes (offset 2000)
BS_EYELASH_BLINK_LEFT = 2000
BS_EYELASH_BLINK_RIGHT = 2001


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _smooth_pulse(t: float, center: float, half_width: float) -> float:
    """Return a smooth pulse (0..1) peaking at *center* with given half-width.

    Uses a raised-cosine shape so the transition is never abrupt.
    Returns 0.0 when ``|t - center| >= half_width``.
    """
    d = abs(t - center)
    if d >= half_width:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * d / half_width))


def _smooth_wave(t: float, period: float, phase: float = 0.0) -> float:
    """Return a smooth oscillation (0..1) based on a sine wave."""
    return 0.5 * (1.0 + math.sin(2.0 * math.pi * t / period + phase))


def _clamp01(v: float) -> float:
    """Clamp a value to the [0.0, 1.0] range."""
    return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_sample_face_data(
    num_frames: int,
    frame_time: float,
) -> FaceMotionData:
    """Generate realistic face animation data simulating sign language.

    The animation includes:
    - Eye blinks at natural intervals (~every 3-4 seconds, ~5 frames).
    - Eyebrow raises (questioning / emphasis).
    - Mouth movements (lips pucker, smile, jaw open).
    - Emotional expressions (HAPPY blendshape).

    Multi-mesh blendshapes (mouth_GEO jaw, eyelash_GEO blinks) are kept
    in sync with their head_GEO counterparts.

    Args:
        num_frames: Number of frames to generate.
        frame_time: Interval between frames in seconds (e.g. 1/30 for 30 fps).

    Returns:
        A :class:`FaceMotionData` instance with the generated frames.
    """
    total_duration = num_frames * frame_time

    # --- Schedule eye blinks (every ~3.5 s, duration ~5 frames) ---
    blink_interval = 3.5  # seconds between blink centres
    blink_half_dur = 2.5 * frame_time  # half-width in seconds (~5 frames total)
    blink_centres: List[float] = []
    t_blink = blink_interval * 0.8  # first blink slightly early
    while t_blink < total_duration:
        blink_centres.append(t_blink)
        t_blink += blink_interval

    # --- Eyebrow raise schedule (two events) ---
    # Place brow raises at ~30 % and ~70 % of the animation.
    brow_raise_centres: List[float] = []
    if total_duration > 1.0:
        brow_raise_centres.append(total_duration * 0.30)
        brow_raise_centres.append(total_duration * 0.70)
    brow_raise_half_dur = 0.4  # seconds

    # --- Mouth movement parameters ---
    # Jaw open: slow oscillation
    jaw_period = 1.8  # seconds
    # Lips pucker: different period so it doesn't perfectly sync with jaw
    pucker_period = 2.5
    # Smile: yet another period
    smile_period = 3.2

    # --- Happy expression: gentle presence in the middle portion ---
    happy_center = total_duration * 0.5
    happy_half_dur = total_duration * 0.25 if total_duration > 2.0 else total_duration * 0.4

    frames: List[FaceFrame] = []

    for i in range(num_frames):
        t = i * frame_time
        weights: Dict[int, float] = {}

        # -- Eye blinks --
        blink_val = 0.0
        for bc in blink_centres:
            blink_val = max(blink_val, _smooth_pulse(t, bc, blink_half_dur))
        if blink_val > 0.001:
            weights[BS_EYE_BLINK_LEFT] = _clamp01(blink_val)
            weights[BS_EYE_BLINK_RIGHT] = _clamp01(blink_val)
            # Eyelash mesh follows head blinks
            weights[BS_EYELASH_BLINK_LEFT] = _clamp01(blink_val)
            weights[BS_EYELASH_BLINK_RIGHT] = _clamp01(blink_val)

        # Eye openness is inverse of blink
        eye_open = 1.0 - blink_val
        if eye_open < 0.999:
            weights[BS_EYE_OPEN_LEFT] = _clamp01(eye_open)
            weights[BS_EYE_OPEN_RIGHT] = _clamp01(eye_open)

        # -- Eyebrow raises --
        brow_val = 0.0
        for brc in brow_raise_centres:
            brow_val = max(brow_val, _smooth_pulse(t, brc, brow_raise_half_dur))
        if brow_val > 0.001:
            brow_weight = _clamp01(brow_val * 0.7)
            weights[BS_BROWS_UP_CENTER] = brow_weight
            weights[BS_BROWS_UP_LEFT] = _clamp01(brow_weight * 0.9)
            weights[BS_BROWS_UP_RIGHT] = _clamp01(brow_weight * 0.9)

        # -- Jaw open --
        jaw_val = _smooth_wave(t, jaw_period, phase=0.0) * 0.5
        if jaw_val > 0.01:
            weights[BS_JAW_OPEN] = _clamp01(jaw_val)
            weights[BS_MOUTH_JAW_OPEN] = _clamp01(jaw_val)  # mouth_GEO sync

        # -- Lips pucker --
        pucker_val = _smooth_wave(t, pucker_period, phase=1.2) * 0.35
        # Pucker only when jaw is relatively closed
        pucker_val *= max(0.0, 1.0 - jaw_val * 2.0)
        if pucker_val > 0.01:
            weights[BS_LIPS_PUCKER] = _clamp01(pucker_val)

        # -- Smile --
        smile_val = _smooth_wave(t, smile_period, phase=0.7) * 0.45
        if smile_val > 0.01:
            weights[BS_MOUTH_SMILE_LEFT] = _clamp01(smile_val)
            weights[BS_MOUTH_SMILE_RIGHT] = _clamp01(smile_val * 0.95)

        # -- Happy expression --
        happy_val = _smooth_pulse(t, happy_center, happy_half_dur) * 0.6
        if happy_val > 0.01:
            weights[BS_HAPPY] = _clamp01(happy_val)

        frames.append(FaceFrame(time=round(t, 6), weights=weights))

    return FaceMotionData(num_frames=num_frames, frames=frames)


def generate_neutral_face_data(
    num_frames: int,
    frame_time: float,
) -> FaceMotionData:
    """Generate minimal face data with only periodic eye blinks.

    Useful for basic SLMB encoding tests where complex expressions
    are not needed.

    Args:
        num_frames: Number of frames to generate.
        frame_time: Interval between frames in seconds.

    Returns:
        A :class:`FaceMotionData` instance with sparse blink-only frames.
    """
    total_duration = num_frames * frame_time

    blink_interval = 3.5
    blink_half_dur = 2.5 * frame_time
    blink_centres: List[float] = []
    t_blink = blink_interval
    while t_blink < total_duration:
        blink_centres.append(t_blink)
        t_blink += blink_interval

    frames: List[FaceFrame] = []

    for i in range(num_frames):
        t = i * frame_time
        weights: Dict[int, float] = {}

        blink_val = 0.0
        for bc in blink_centres:
            blink_val = max(blink_val, _smooth_pulse(t, bc, blink_half_dur))

        if blink_val > 0.001:
            weights[BS_EYE_BLINK_LEFT] = _clamp01(blink_val)
            weights[BS_EYE_BLINK_RIGHT] = _clamp01(blink_val)
            weights[BS_EYELASH_BLINK_LEFT] = _clamp01(blink_val)
            weights[BS_EYELASH_BLINK_RIGHT] = _clamp01(blink_val)

        frames.append(FaceFrame(time=round(t, 6), weights=weights))

    return FaceMotionData(num_frames=num_frames, frames=frames)
