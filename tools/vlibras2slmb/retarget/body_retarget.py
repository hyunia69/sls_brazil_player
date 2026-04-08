"""Body skeleton retargeting: VLibras 84-bone to ABNT 46-joint.

Converts VLibras animation data (84 bones, Portuguese naming, Unity
left-handed coordinate system) to the ABNT NBR 25606 standard skeleton
(46 joints, English naming, right-handed coordinate system).

Key retargeting operations:

- **Direct mapping**: VLibras bones that have a 1:1 ABNT counterpart
  (e.g. ``BnOmbro.L`` -> ``l_shoulder_JNT``).
- **Intermediate bone composition**: ``BnAntBraco.L.001`` and
  ``BnAntBraco.R.001`` have no ABNT equivalent; their rotation is
  composited into the child hand joint via quaternion multiplication.
- **Coordinate system conversion**: Unity left-hand to ABNT right-hand
  (negate X and Z components of quaternions and positions).
- **Root translation**: Extracted from ``BnBacia.001`` position data
  for ``hips_JNT`` (Type-0 joint).
- **Identity fill**: ABNT joints with no VLibras source get identity
  quaternion ``[1, 0, 0, 0]``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from ..data.joint_types import (
    JOINT_ENCODING_ORDER,
    JOINT_ORDER,
    JOINT_TYPE,
    NUM_JOINTS,
)
from ..data.rotation_axes import ROTATION_AXES
from ..data.vlibras_bind_pose import VLIBRAS_BIND_POSE
from ..data.skeleton_map import (
    AUXILIARY_BONES,
    FACE_BONES,
    INTERMEDIATE_BONES,
    UNMAPPED_BONES,
    VLIBRAS_TO_ABNT,
)
from ..math_utils.coordinate import (
    unity_position_to_abnt,
    unity_quat_to_abnt,
)
from ..math_utils.euler import rotationaxis_to_quaternion
from ..math_utils.interpolation import (
    calculate_num_frames,
    resample_positions,
    resample_quaternions,
)
from ..math_utils.quaternion import (
    ensure_positive_w,
    inverse,
    multiply,
    normalize,
)
from ..parsing.animation_clip import AnimationClipData

logger = logging.getLogger(__name__)

# Identity quaternion used for joints with no source data.
_IDENTITY_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

# Zero translation for frames without position data.
_ZERO_POS = np.array([0.0, 0.0, 0.0], dtype=np.float64)


@dataclass
class BodyMotionData:
    """Retargeted body motion data ready for SLMB encoding.

    Attributes:
        num_frames: Total number of uniform frames.
        frame_time: Duration of each frame in seconds (``1 / sample_rate``).
        joint_rotations: Mapping from ABNT joint name to a list of
            *num_frames* quaternion arrays ``[w, x, y, z]``.  All
            quaternions are normalized and have ``w >= 0``.
        root_translations: List of *num_frames* position arrays
            ``[x, y, z]`` for ``hips_JNT`` (the only Type-0 joint).
    """

    num_frames: int
    frame_time: float
    joint_rotations: Dict[str, List[np.ndarray]]
    root_translations: List[np.ndarray]

    def get_frame_rotations(self, frame_idx: int) -> Dict[str, np.ndarray]:
        """Return all joint rotations for a single frame.

        Args:
            frame_idx: Zero-based frame index.

        Returns:
            Dictionary mapping joint name to quaternion ``[w, x, y, z]``.

        Raises:
            IndexError: If *frame_idx* is out of range.
        """
        if frame_idx < 0 or frame_idx >= self.num_frames:
            raise IndexError(
                f"frame_idx {frame_idx} out of range [0, {self.num_frames})"
            )
        return {
            name: quats[frame_idx]
            for name, quats in self.joint_rotations.items()
        }


def _build_leaf_to_path_index(clip: AnimationClipData) -> Dict[str, str]:
    """Build a leaf-name to full-path index from the clip's rotation curves.

    This covers paths that actually have rotation data, which is more
    useful for retargeting than the full ``bone_paths`` list (which
    also includes bones that only have position/scale data).
    """
    index: Dict[str, str] = {}
    for path in clip.rotation_curves:
        leaf = AnimationClipData.get_leaf_name(path)
        index[leaf] = path
    return index


def _extract_keyframe_pairs(
    curve,
) -> List:
    """Convert an AnimationCurve's keyframes to (time, value) tuples.

    Args:
        curve: An :class:`AnimationCurve` with Keyframe objects.

    Returns:
        List of ``(time, numpy_array)`` tuples suitable for resampling.
    """
    return [(kf.time, kf.value) for kf in curve.keyframes]


def retarget_body(clip: AnimationClipData) -> BodyMotionData:
    """Retarget a VLibras animation clip to the ABNT 46-joint skeleton.

    Processing pipeline:

    1. Calculate uniform frame count from ``clip.sample_rate`` and
       ``clip.duration``.
    2. Build a leaf-name index for fast curve lookup.
    3. For each ABNT joint that has a VLibras source bone:
       a. Retrieve the rotation curve by leaf name.
       b. Resample to uniform frames using SLERP.
       c. Apply coordinate system conversion (Unity LH -> ABNT RH).
       d. Handle intermediate bone composition where needed.
    4. Extract ``hips_JNT`` root translation from ``BnBacia.001``
       position data.
    5. Fill unmapped ABNT joints with identity quaternions.
    6. Ensure all output quaternions have ``w >= 0`` (SLMB requirement).

    Args:
        clip: Parsed VLibras animation clip.

    Returns:
        :class:`BodyMotionData` with per-frame rotation and translation
        data for all 46 ABNT joints.
    """
    num_frames = calculate_num_frames(clip.sample_rate, clip.duration)
    frame_time = 1.0 / clip.sample_rate if clip.sample_rate > 0 else 0.0

    logger.info(
        "Retargeting body: %d frames, %.4f s frame_time (%.1f fps), "
        "%.3f s duration",
        num_frames,
        frame_time,
        clip.sample_rate,
        clip.duration,
    )

    # Build leaf-name -> full-path index for rotation curves.
    leaf_to_path = _build_leaf_to_path_index(clip)

    # Pre-resample intermediate bone rotations for composition.
    intermediate_resampled: Dict[str, List[np.ndarray]] = {}
    for inter_leaf, child_leaf in INTERMEDIATE_BONES.items():
        if inter_leaf in leaf_to_path:
            inter_path = leaf_to_path[inter_leaf]
            inter_curve = clip.rotation_curves[inter_path]
            kf_pairs = _extract_keyframe_pairs(inter_curve)
            if kf_pairs:
                intermediate_resampled[inter_leaf] = resample_quaternions(
                    kf_pairs, num_frames, clip.duration
                )
                logger.debug(
                    "Pre-resampled intermediate bone '%s' -> child '%s'",
                    inter_leaf,
                    child_leaf,
                )

    # Process each ABNT joint.
    joint_rotations: Dict[str, List[np.ndarray]] = {}

    for _idx, joint_name, _jtype in JOINT_ENCODING_ORDER:
        # Find the VLibras source bone for this ABNT joint.
        source_leaf: Optional[str] = None
        for vlibras_leaf, abnt_name in VLIBRAS_TO_ABNT.items():
            if abnt_name == joint_name:
                source_leaf = vlibras_leaf
                break

        if source_leaf is None:
            # No VLibras mapping -- fill with identity.
            joint_rotations[joint_name] = [
                _IDENTITY_QUAT.copy() for _ in range(num_frames)
            ]
            logger.debug(
                "Joint '%s' has no VLibras source, using identity",
                joint_name,
            )
            continue

        # Look up the rotation curve for this source bone.
        source_path = leaf_to_path.get(source_leaf)
        if source_path is None or source_path not in clip.rotation_curves:
            joint_rotations[joint_name] = [
                _IDENTITY_QUAT.copy() for _ in range(num_frames)
            ]
            logger.debug(
                "Joint '%s' (source='%s') has no rotation curve, "
                "using identity",
                joint_name,
                source_leaf,
            )
            continue

        curve = clip.rotation_curves[source_path]
        kf_pairs = _extract_keyframe_pairs(curve)

        if not kf_pairs:
            joint_rotations[joint_name] = [
                _IDENTITY_QUAT.copy() for _ in range(num_frames)
            ]
            continue

        # Resample to uniform frames.
        resampled = resample_quaternions(kf_pairs, num_frames, clip.duration)

        # Check if this bone receives intermediate bone composition.
        # The INTERMEDIATE_BONES dict maps intermediate_leaf -> child_leaf.
        # If source_leaf is a child of an intermediate bone, composite.
        composed_inter_leaf: Optional[str] = None
        for inter_leaf, child_leaf in INTERMEDIATE_BONES.items():
            if child_leaf == source_leaf:
                composed_inter_leaf = inter_leaf
                break

        if (
            composed_inter_leaf is not None
            and composed_inter_leaf in intermediate_resampled
        ):
            inter_frames = intermediate_resampled[composed_inter_leaf]
            logger.debug(
                "Compositing intermediate '%s' into joint '%s' "
                "(source='%s')",
                composed_inter_leaf,
                joint_name,
                source_leaf,
            )
            composed: List[np.ndarray] = []
            for i in range(num_frames):
                # q_final = q_intermediate * q_original
                # The intermediate bone's rotation is prepended because
                # it sits between the forearm and the hand in the hierarchy.
                q_composed = multiply(inter_frames[i], resampled[i])
                composed.append(normalize(q_composed))
            resampled = composed

        # Apply coordinate system conversion: Unity LH -> ABNT RH.
        converted: List[np.ndarray] = []
        for q in resampled:
            q_abnt = unity_quat_to_abnt(q)
            q_abnt = ensure_positive_w(normalize(q_abnt))
            converted.append(q_abnt)

        joint_rotations[joint_name] = converted

    # -- Root translation for hips_JNT --
    root_translations: List[np.ndarray] = []
    hips_source_leaf = "BnBacia.001"
    hips_pos_curve = clip.get_position_curve_by_leaf(hips_source_leaf)

    if hips_pos_curve is not None and hips_pos_curve.keyframes:
        pos_kf_pairs = _extract_keyframe_pairs(hips_pos_curve)
        resampled_pos = resample_positions(
            pos_kf_pairs, num_frames, clip.duration
        )
        for pos in resampled_pos:
            root_translations.append(unity_position_to_abnt(pos))
        logger.debug(
            "Extracted %d root translation frames from '%s'",
            len(root_translations),
            hips_source_leaf,
        )
    else:
        root_translations = [_ZERO_POS.copy() for _ in range(num_frames)]
        logger.debug(
            "No position data for '%s', using zero translation",
            hips_source_leaf,
        )

    # Validate output completeness.
    expected_joints = {name for _, name, _ in JOINT_ENCODING_ORDER}
    missing = expected_joints - set(joint_rotations.keys())
    if missing:
        logger.warning(
            "Missing %d joints in output (filling with identity): %s",
            len(missing),
            sorted(missing),
        )
        for joint_name in missing:
            joint_rotations[joint_name] = [
                _IDENTITY_QUAT.copy() for _ in range(num_frames)
            ]

    # -- Apply bind-pose correction and ABNT rest-pose rebase --
    #
    # VLibras animation curves store ABSOLUTE local rotations (including
    # the skeleton's bind-pose component).  The ABNT SLMB format expects
    # rotations relative to the ABNT rest pose defined by rotation axes.
    #
    # For Type-2/3 joints (euler-encoded), we must:
    #   1. Remove the VLibras bind-pose: Q_delta = Q * inv(Q_bind_abnt)
    #   2. Rebase to ABNT rest-pose:     Q_slmb = Q_delta * Qr_abnt
    # Combined:
    #   Q_slmb = Q_vlibras_abnt * inv(Q_bind_abnt) * Qr_abnt
    #          = Q_vlibras_abnt * Q_correction
    #
    # Without this, the VLibras bind-pose (especially for pinky: ~90°)
    # produces euler angles far outside the encoding range, causing
    # catastrophic roundtrip errors (up to 180°).
    #
    # Build reverse mapping: ABNT joint -> VLibras source bone leaf name.
    abnt_to_vlibras: Dict[str, str] = {
        abnt: vlibras for vlibras, abnt in VLIBRAS_TO_ABNT.items()
    }

    for joint_name, quats in joint_rotations.items():
        axes = ROTATION_AXES.get(joint_name)
        if axes is None:
            continue
        RX, RY, RZ = axes
        Qr = rotationaxis_to_quaternion(RX, RY, RZ)

        # Skip joints with identity Qr and near-identity bind pose
        # (Type-0, Type-1, Type-4) -- their encoding doesn't use euler
        # decomposition, so bind-pose doesn't cause encoding errors.
        if abs(abs(Qr[0]) - 1.0) < 1e-6:
            continue

        # Get VLibras bind-pose for this joint's source bone.
        source_leaf = abnt_to_vlibras.get(joint_name)
        if source_leaf and source_leaf in VLIBRAS_BIND_POSE:
            bp = VLIBRAS_BIND_POSE[source_leaf]
            Q_bind = np.array(bp, dtype=np.float64)
            # Convert bind-pose to ABNT coordinate system.
            Q_bind_abnt = unity_quat_to_abnt(Q_bind)
            Q_bind_abnt = normalize(Q_bind_abnt)
            # Q_correction = inv(Q_bind_abnt) * Qr
            Q_correction = multiply(inverse(Q_bind_abnt), Qr)
        else:
            # No bind-pose data: fall back to just Qr baking.
            Q_correction = Qr

        Q_correction = normalize(Q_correction)

        for i in range(len(quats)):
            q_corrected = multiply(quats[i], Q_correction)
            quats[i] = ensure_positive_w(normalize(q_corrected))

        logger.debug(
            "Applied bind-pose correction to '%s' "
            "(source='%s', Qr=[%.4f,%.4f,%.4f,%.4f])",
            joint_name,
            source_leaf or "N/A",
            Qr[0], Qr[1], Qr[2], Qr[3],
        )

    result = BodyMotionData(
        num_frames=num_frames,
        frame_time=frame_time,
        joint_rotations=joint_rotations,
        root_translations=root_translations,
    )

    # Log summary statistics.
    mapped_count = sum(
        1
        for name, quats in joint_rotations.items()
        if not all(np.allclose(q, _IDENTITY_QUAT) for q in quats)
    )
    logger.info(
        "Body retarget complete: %d frames, %d/%d joints have motion data",
        num_frames,
        mapped_count,
        NUM_JOINTS,
    )

    return result
