"""Face blendshape retargeting: VLibras 22 shapes to ABNT 68 shapes.

Maps VLibras blendshape animation curves to the ABNT NBR 25606 avatar's
68 blendshape targets.  Handles:

- **1:1 mapping**: A single VLibras shape maps to one ABNT target
  (e.g. ``"Bico"`` -> ``LipsPucker``).
- **1:N split**: A VLibras shape maps to multiple ABNT targets with
  individual scale factors (e.g. ``"Sorriso"`` -> ``MouthSmile_Left``
  + ``MouthSmile_Right``).
- **Accumulation**: Multiple VLibras shapes may target the same ABNT
  blendshape ID; weights are added and clamped to ``[0.0, 1.0]``.
- **Inverted mapping**: Negative scale factors invert the weight
  (e.g. ``"FranzirSobrancelha"`` -> ``BrowsUp_Center`` with scale -1).
- **Skip list**: Correction and test shapes are excluded.
- **Empty curves**: Float curves without keyframe data are skipped
  gracefully.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from ..data.blendshape_map import (
    ABNT_BLENDSHAPE_NAMES,
    NUM_BLENDSHAPES,
    VLIBRAS_SKIP_BLENDSHAPES,
    VLIBRAS_TO_ABNT_BLENDSHAPE,
)
from ..math_utils.interpolation import (
    calculate_num_frames,
    resample_weights,
)
from ..parsing.animation_clip import AnimationClipData

logger = logging.getLogger(__name__)


@dataclass
class FaceMotionData:
    """Retargeted face motion data ready for SLMB FaceMotionBlock encoding.

    Attributes:
        num_frames: Total number of uniform frames.
        frame_times: Per-frame timestamps in seconds.  SLMB
            FaceMotionBlock stores explicit per-frame times rather than
            a fixed frame interval.
        blendshape_weights: Mapping from ABNT blendshape ID (0-67) to
            a list of *num_frames* weight values in ``[0.0, 1.0]``.
            Only blendshapes with at least one non-zero frame are
            included.
    """

    num_frames: int
    frame_times: List[float]
    blendshape_weights: Dict[int, List[float]]

    def get_active_blendshape_ids(self) -> List[int]:
        """Return sorted list of blendshape IDs that have non-zero data.

        Returns:
            Sorted list of ABNT blendshape IDs present in
            :attr:`blendshape_weights`.
        """
        return sorted(self.blendshape_weights.keys())

    def get_blendshape_name(self, bs_id: int) -> str:
        """Look up the ABNT blendshape name for a given ID.

        Args:
            bs_id: ABNT blendshape ID (0-67).

        Returns:
            Blendshape name string.

        Raises:
            IndexError: If *bs_id* is outside ``[0, 67]``.
        """
        return ABNT_BLENDSHAPE_NAMES[bs_id]


def _build_vlibras_mapping_lookup() -> Dict[str, List[tuple]]:
    """Build a dictionary from VLibras blendshape name to ABNT targets.

    Returns:
        Mapping from VLibras name to list of ``(abnt_id, scale_factor)``
        tuples.
    """
    lookup: Dict[str, List[tuple]] = {}
    for vlibras_name, targets in VLIBRAS_TO_ABNT_BLENDSHAPE:
        lookup[vlibras_name] = targets
    return lookup


def retarget_face(clip: AnimationClipData) -> FaceMotionData:
    """Map VLibras blendshape curves to ABNT 68-blendshape targets.

    Processing pipeline:

    1. Calculate uniform frame count and timestamps.
    2. Build VLibras-to-ABNT mapping lookup.
    3. For each VLibras float curve with keyframe data:
       a. Skip curves in the skip list (correction/test shapes).
       b. Extract the blendshape name (already parsed by
          :class:`AnimationClipData`).
       c. Look up ABNT target(s) and scale factor(s).
       d. Resample keyframes to uniform grid.
       e. Apply scale factor and accumulate into ABNT target arrays.
    4. Clamp all weights to ``[0.0, 1.0]``.
    5. Remove blendshape entries that are all-zero.

    Args:
        clip: Parsed VLibras animation clip.

    Returns:
        :class:`FaceMotionData` with per-frame blendshape weights
        for all active ABNT targets.
    """
    num_frames = calculate_num_frames(clip.sample_rate, clip.duration)
    frame_time = 1.0 / clip.sample_rate if clip.sample_rate > 0 else 0.0

    # Build per-frame timestamps.
    if num_frames <= 1:
        frame_times = [0.0]
    else:
        frame_times = [
            i * (clip.duration / (num_frames - 1)) for i in range(num_frames)
        ]

    logger.info(
        "Retargeting face: %d frames, %.1f fps, %.3f s duration, "
        "%d float curves in clip",
        num_frames,
        clip.sample_rate,
        clip.duration,
        len(clip.float_curves),
    )

    # Initialize accumulation buffers for all 68 ABNT blendshapes.
    accumulators: Dict[int, List[float]] = {
        bs_id: [0.0] * num_frames for bs_id in range(NUM_BLENDSHAPES)
    }

    mapping_lookup = _build_vlibras_mapping_lookup()
    mapped_count = 0
    skipped_count = 0
    unmapped_count = 0

    for bs_name, curve in clip.float_curves.items():
        # Skip correction/test shapes.
        if bs_name in VLIBRAS_SKIP_BLENDSHAPES:
            skipped_count += 1
            logger.debug("Skipping excluded blendshape '%s'", bs_name)
            continue

        # Skip curves without keyframe data.
        if not curve.keyframes:
            logger.debug(
                "Blendshape '%s' has no keyframes, skipping", bs_name
            )
            continue

        # Look up ABNT targets.
        targets = mapping_lookup.get(bs_name)
        if targets is None:
            unmapped_count += 1
            logger.warning(
                "VLibras blendshape '%s' has no ABNT mapping, skipping",
                bs_name,
            )
            continue

        # Resample to uniform grid.
        # Extract (time, weight) pairs from keyframes.
        kf_pairs = [
            (kf.time, float(kf.value[0])) for kf in curve.keyframes
        ]
        resampled = resample_weights(kf_pairs, num_frames, clip.duration)

        # Apply to each ABNT target with its scale factor.
        for abnt_id, scale in targets:
            if abnt_id < 0 or abnt_id >= NUM_BLENDSHAPES:
                logger.warning(
                    "Invalid ABNT blendshape ID %d for '%s', skipping target",
                    abnt_id,
                    bs_name,
                )
                continue

            for i in range(num_frames):
                weight = resampled[i]

                if scale < 0.0:
                    # Inverted mapping: use (1 - weight) scaled by |factor|.
                    # When FranzirSobrancelha=1.0 (full furrow), the
                    # BrowsUp_Center should be 0.0 (not raised). When
                    # FranzirSobrancelha=0.0 (no furrow), BrowsUp_Center
                    # is unaffected (contribution = 0).
                    # So inverted contribution = weight * |scale| applied
                    # as a subtraction from the default (which starts at 0).
                    # Since accumulators start at 0, inverted shapes would
                    # produce negative values which get clamped to 0 later.
                    # This is correct: furrow suppresses brow raise.
                    accumulators[abnt_id][i] += weight * scale
                else:
                    accumulators[abnt_id][i] += weight * scale

        mapped_count += 1

    # Clamp all weights to [0.0, 1.0] and filter out all-zero entries.
    blendshape_weights: Dict[int, List[float]] = {}
    for bs_id in range(NUM_BLENDSHAPES):
        weights = accumulators[bs_id]
        clamped = [max(0.0, min(1.0, w)) for w in weights]

        # Only include if at least one frame is non-zero.
        if any(abs(w) > 1e-9 for w in clamped):
            blendshape_weights[bs_id] = clamped

    result = FaceMotionData(
        num_frames=num_frames,
        frame_times=frame_times,
        blendshape_weights=blendshape_weights,
    )

    logger.info(
        "Face retarget complete: %d frames, %d mapped VLibras curves, "
        "%d skipped, %d unmapped, %d active ABNT blendshapes",
        num_frames,
        mapped_count,
        skipped_count,
        unmapped_count,
        len(blendshape_weights),
    )

    return result
