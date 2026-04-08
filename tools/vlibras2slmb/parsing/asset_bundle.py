"""UnityPy-based AssetBundle parser for VLibras sign language animations.

VLibras distributes sign language animations as Unity AssetBundles
(UnityFS format, built with Unity 2018.3.1f1).  Each bundle contains
a single AnimationClip with rotation curves (body skeleton), position
curves (root motion), and float curves (blendshape weights).

Requires: pip install UnityPy
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .animation_clip import AnimationClipData


def load_asset_bundle(path: str) -> AnimationClipData:
    """Load a VLibras AssetBundle and extract its AnimationClip.

    Args:
        path: Filesystem path to the Unity AssetBundle file.

    Returns:
        Parsed AnimationClipData ready for retargeting.

    Raises:
        ImportError: If UnityPy is not installed.
        ValueError: If the bundle contains no AnimationClip.
    """
    try:
        import UnityPy
    except ImportError:
        raise ImportError(
            "UnityPy is required for AssetBundle parsing. "
            "Install: pip install UnityPy"
        )

    env = UnityPy.load(path)

    clip_data = None
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            clip = obj.read()
            clip_data = _convert_unity_clip(clip)
            break

    if clip_data is None:
        raise ValueError(f"No AnimationClip found in {path}")

    return clip_data


def _convert_unity_clip(clip: object) -> AnimationClipData:
    """Convert a UnityPy AnimationClip to our AnimationClipData format.

    Extracts rotation curves (quaternion wxyz), position curves (xyz),
    and float curves (blendshape weights) from the Unity clip object.

    Args:
        clip: UnityPy AnimationClip object with m_Name, m_SampleRate,
            m_RotationCurves, m_PositionCurves, m_FloatCurves attributes.

    Returns:
        Populated AnimationClipData instance.
    """
    from .animation_clip import AnimationClipData, Keyframe, AnimationCurve

    name = clip.m_Name
    sample_rate = clip.m_SampleRate

    rotation_curves: dict[str, AnimationCurve] = {}
    position_curves: dict[str, AnimationCurve] = {}
    float_curves: dict[str, AnimationCurve] = {}
    bone_paths: list[str] = []
    max_time = 0.0

    # Process rotation curves
    for rc in clip.m_RotationCurves:
        path = rc.path
        if path not in bone_paths:
            bone_paths.append(path)

        keyframes: list[Keyframe] = []
        for kf in rc.curve.m_Curve:
            t = kf.time
            # Unity quaternion value has X, Y, Z, W attributes
            x, y, z, w = kf.value.X, kf.value.Y, kf.value.Z, kf.value.W
            keyframes.append(Keyframe(time=t, value=np.array([w, x, y, z])))
            max_time = max(max_time, t)

        rotation_curves[path] = AnimationCurve(path=path, keyframes=keyframes)

    # Process position curves
    for pc in clip.m_PositionCurves:
        path = pc.path
        if path not in bone_paths:
            bone_paths.append(path)

        keyframes = []
        for kf in pc.curve.m_Curve:
            t = kf.time
            x, y, z = kf.value.X, kf.value.Y, kf.value.Z
            keyframes.append(Keyframe(time=t, value=np.array([x, y, z])))
            max_time = max(max_time, t)

        position_curves[path] = AnimationCurve(path=path, keyframes=keyframes)

    # Process float curves (blendshapes)
    for fc in clip.m_FloatCurves:
        attr = fc.attribute
        if attr.startswith("blendShape."):
            bs_name = attr.split(".", 1)[1]
        else:
            bs_name = attr

        keyframes = []
        for kf in fc.curve.m_Curve:
            t = kf.time
            keyframes.append(Keyframe(time=t, value=np.array([kf.value])))
            max_time = max(max_time, t)

        float_curves[bs_name] = AnimationCurve(
            path=fc.path, keyframes=keyframes
        )

    return AnimationClipData(
        name=name,
        sample_rate=sample_rate,
        duration=max_time,
        bone_paths=bone_paths,
        rotation_curves=rotation_curves,
        position_curves=position_curves,
        float_curves=float_curves,
    )
