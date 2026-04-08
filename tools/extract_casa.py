"""Extract complete animation data from VLibras AssetBundle to JSON.

Reads Unity AssetBundle via UnityPy and outputs a JSON file with
ALL keyframes preserved (no simplification or truncation).

Usage:
    python extract_casa.py CASA                      # → CASA_full.json
    python extract_casa.py CASA -o output.json
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("UnityPy required: pip install UnityPy")
    sys.exit(1)


def extract(bundle_path, output_path=None):
    bundle_path = Path(bundle_path)
    if output_path is None:
        output_path = bundle_path.parent / f"{bundle_path.name}_full.json"
    else:
        output_path = Path(output_path)

    env = UnityPy.load(str(bundle_path))

    clip = None
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            clip = obj.read()
            break

    if clip is None:
        print(f"Error: No AnimationClip found in {bundle_path}")
        sys.exit(1)

    # ── Collect bone paths from all curve types ──
    bone_paths = []
    seen = set()

    def add_path(p):
        if p not in seen:
            bone_paths.append(p)
            seen.add(p)

    for rc in clip.m_RotationCurves:
        add_path(rc.path)
    for pc in clip.m_PositionCurves:
        add_path(pc.path)

    # ── Rotation curves ──
    rotation_curves = []
    for rc in clip.m_RotationCurves:
        keyframes = []
        for kf in rc.curve.m_Curve:
            keyframes.append({
                "time": kf.time,
                "value": [kf.value.x, kf.value.y, kf.value.z, kf.value.w],
            })
        rotation_curves.append({
            "path": rc.path,
            "keyframe_count": len(keyframes),
            "keyframes": keyframes,
        })

    # ── Position curves ──
    position_curves = []
    for pc in clip.m_PositionCurves:
        keyframes = []
        for kf in pc.curve.m_Curve:
            keyframes.append({
                "time": kf.time,
                "value": [kf.value.x, kf.value.y, kf.value.z],
            })
        position_curves.append({
            "path": pc.path,
            "keyframe_count": len(keyframes),
            "keyframes": keyframes,
        })

    # ── Scale curves ──
    scale_curves = []
    if hasattr(clip, 'm_ScaleCurves'):
        for sc in clip.m_ScaleCurves:
            add_path(sc.path)
            keyframes = []
            for kf in sc.curve.m_Curve:
                keyframes.append({
                    "time": kf.time,
                    "value": [kf.value.x, kf.value.y, kf.value.z],
                })
            scale_curves.append({
                "path": sc.path,
                "keyframe_count": len(keyframes),
                "keyframes": keyframes,
            })

    # ── Float curves (blendshapes) ──
    float_curves = []
    for fc in clip.m_FloatCurves:
        keyframes = []
        for kf in fc.curve.m_Curve:
            keyframes.append({
                "time": kf.time,
                "value": kf.value,
            })
        float_curves.append({
            "path": fc.path,
            "attribute": fc.attribute,
            "keyframe_count": len(keyframes),
            "keyframes": keyframes,
        })

    # ── Assemble output ──
    data = {
        "name": clip.m_Name,
        "sample_rate": clip.m_SampleRate,
        "legacy": getattr(clip, 'm_Legacy', False),
        "bone_paths": bone_paths,
        "rotation_curves": rotation_curves,
        "position_curves": position_curves,
        "scale_curves": scale_curves,
        "float_curves": float_curves,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # ── Stats ──
    rot_kfs = sum(len(rc["keyframes"]) for rc in rotation_curves)
    pos_kfs = sum(len(pc["keyframes"]) for pc in position_curves)
    sc_kfs = sum(len(sc["keyframes"]) for sc in scale_curves)
    fl_kfs = sum(len(fc["keyframes"]) for fc in float_curves)
    animated_rot = sum(1 for rc in rotation_curves if len(rc["keyframes"]) > 2)

    print(f"Extracted: {bundle_path.name} → {output_path.name}")
    print(f"  Clip: {clip.m_Name}, {clip.m_SampleRate} fps")
    print(f"  Bones: {len(bone_paths)}")
    print(f"  Rotation: {len(rotation_curves)} curves, {rot_kfs} keyframes ({animated_rot} animated)")
    print(f"  Position: {len(position_curves)} curves, {pos_kfs} keyframes")
    print(f"  Scale:    {len(scale_curves)} curves, {sc_kfs} keyframes")
    print(f"  Float:    {len(float_curves)} curves, {fl_kfs} keyframes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract VLibras AssetBundle to JSON")
    parser.add_argument("input", help="AssetBundle file path")
    parser.add_argument("-o", "--output", help="Output JSON path")
    args = parser.parse_args()
    extract(args.input, args.output)
