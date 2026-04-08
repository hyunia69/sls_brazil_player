#!/usr/bin/env python3
"""
Convert *_ik_fixed.json (Unity/Blender coordinate space) to *.anim.json (Three.js/GLTF space).

Usage:
  python convert_anim.py gloss/CASA_ik_fixed.json -o gloss/CASA.anim.json
  python convert_anim.py gloss/CASA_ik_fixed.json  # outputs to gloss/CASA.anim.json automatically

Coordinate conversion rules (verified against working avatar_old/player.html):
  - Quaternion: [x, y, z, w] → [x, -y, -z, w]  (Unity Z-up → GLTF Y-up)
  - Position:   delta from frame 0, Z negated: [dx, dy, -dz]
  - Bone names: dots stripped (BnBraco.L → BnBracoL) to match Three.js GLTF loader
  - Root bone (Armature.001): excluded
  - Aux bones (BnMaoOrient*, BnPolyV*, ik_FK*): excluded

Output format: Three.js KeyframeTrack JSON, directly loadable as AnimationClip.
Position tracks contain deltas — the player adds GLB rest position at load time.
"""
import json
import argparse
import math
import os
import sys

try:
    import UnityPy
    HAS_UNITYPY = True
except ImportError:
    HAS_UNITYPY = False

# Resample sparse curves at this fps for smoother interpolation
RESAMPLE_FPS = 30
RESAMPLE_THRESHOLD = 10  # curves with fewer keyframes get resampled

# Bones to skip (root + spine root + IK helpers)
# BnBacia.001 rotation is frozen at GLB rest (old player: mode='root', copies glbRest)
SKIP_PATHS = {'Armature.001'}
# BnBacia.001 rotation: skip → GLB rest pose has the correct Z-up→Y-up conversion
# convQuat can't produce this value (it's a coordinate system transform, not a bone rotation)
SKIP_ROTATION_LEAVES = {'Armature.001', 'BnBacia.001'}
AUX_PREFIXES = ('BnMaoOrient', 'BnPolyV', 'ik_FK')


def strip_dots(name):
    return name.replace('.', '')


def conv_quat(x, y, z, w):
    """Unity/Blender → GLTF quaternion: negate Y and Z, normalize sign (w >= 0)."""
    cx, cy, cz, cw = x, -y, -z, w
    # Ensure consistent sign convention (w >= 0) to prevent long-path slerp
    if cw < 0:
        cx, cy, cz, cw = -cx, -cy, -cz, -cw
    return (cx, cy, cz, cw)


def should_skip(path):
    """Check if a bone path should be excluded entirely."""
    if path in SKIP_PATHS:
        return True
    leaf = path.split('/')[-1]
    return any(leaf.startswith(p) for p in AUX_PREFIXES)


def should_skip_rotation(path):
    """Check if rotation should be excluded (keeps GLB rest pose)."""
    if should_skip(path):
        return True
    leaf = path.split('/')[-1]
    return leaf in SKIP_ROTATION_LEAVES


def quat_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2] + a[3]*b[3]


def quat_normalize(q):
    n = math.sqrt(sum(c*c for c in q))
    return [c/n for c in q] if n > 1e-10 else [0, 0, 0, 1]


def quat_slerp(a, b, t):
    """Spherical linear interpolation between two quaternions [x,y,z,w]."""
    dot = quat_dot(a, b)
    # Ensure shortest path
    if dot < 0:
        b = [-c for c in b]
        dot = -dot
    if dot > 0.9995:
        # Linear fallback for very close quaternions
        result = [a[i] + (b[i] - a[i]) * t for i in range(4)]
        return quat_normalize(result)
    theta = math.acos(min(dot, 1.0))
    sin_theta = math.sin(theta)
    wa = math.sin((1 - t) * theta) / sin_theta
    wb = math.sin(t * theta) / sin_theta
    return quat_normalize([wa * a[i] + wb * b[i] for i in range(4)])


def catmull_rom_quat(keyframes, sample_rate, duration):
    """Resample sparse quaternion keyframes using Catmull-Rom-like slerp interpolation.
    Returns dense (times, flat_values) at the given sample rate.
    """
    if len(keyframes) <= 1:
        return [kf['time'] for kf in keyframes], [v for kf in keyframes for v in kf['value']]

    times_out = []
    values_out = []
    dt = 1.0 / sample_rate
    t = keyframes[0]['time']
    end_t = min(keyframes[-1]['time'], duration)

    while t <= end_t + dt * 0.5:
        # Find surrounding keyframe segment
        seg = 0
        while seg < len(keyframes) - 2 and keyframes[seg + 1]['time'] < t:
            seg += 1
        kf0 = keyframes[seg]
        kf1 = keyframes[seg + 1] if seg + 1 < len(keyframes) else kf0
        seg_dur = kf1['time'] - kf0['time']
        alpha = (t - kf0['time']) / seg_dur if seg_dur > 0 else 0
        alpha = max(0, min(1, alpha))

        q = quat_slerp(kf0['value'], kf1['value'], alpha)
        times_out.append(round(t, 6))
        values_out.extend(q)
        t += dt

    return times_out, values_out


def catmull_rom_vec(keyframes, sample_rate, duration):
    """Resample sparse vector keyframes using linear interpolation at given sample rate."""
    if len(keyframes) <= 1:
        return [kf['time'] for kf in keyframes], [v for kf in keyframes for v in kf['value']]

    times_out = []
    values_out = []
    dt = 1.0 / sample_rate
    t = keyframes[0]['time']
    end_t = min(keyframes[-1]['time'], duration)
    dim = len(keyframes[0]['value'])

    while t <= end_t + dt * 0.5:
        seg = 0
        while seg < len(keyframes) - 2 and keyframes[seg + 1]['time'] < t:
            seg += 1
        kf0 = keyframes[seg]
        kf1 = keyframes[seg + 1] if seg + 1 < len(keyframes) else kf0
        seg_dur = kf1['time'] - kf0['time']
        alpha = (t - kf0['time']) / seg_dur if seg_dur > 0 else 0
        alpha = max(0, min(1, alpha))

        v = [kf0['value'][i] + (kf1['value'][i] - kf0['value'][i]) * alpha for i in range(dim)]
        times_out.append(round(t, 6))
        values_out.extend(v)
        t += dt

    return times_out, values_out


def load_assetbundle_curves(ab_path):
    """Load rotation/position curves from Unity AssetBundle for supplementing ik_fixed data."""
    if not HAS_UNITYPY or not ab_path or not os.path.exists(ab_path):
        return {}, {}

    env = UnityPy.load(ab_path)
    rot_curves = {}  # bone_leaf_name -> [{'time': t, 'value': [x,y,z,w]}, ...]
    pos_curves = {}

    for path, obj in env.container.items():
        if obj.type.name == 'AnimationClip':
            tree = obj.read_typetree()
            for rc in tree.get('m_RotationCurves', []):
                leaf = rc['path'].split('/')[-1]
                kfs = []
                for kf in rc['curve']['m_Curve']:
                    v = kf['value']
                    kfs.append({'time': kf['time'], 'value': [v['x'], v['y'], v['z'], v['w']]})
                rot_curves[leaf] = kfs
            for pc in tree.get('m_PositionCurves', []):
                leaf = pc['path'].split('/')[-1]
                kfs = []
                for kf in pc['curve']['m_Curve']:
                    v = kf['value']
                    kfs.append({'time': kf['time'], 'value': [v['x'], v['y'], v['z']]})
                pos_curves[leaf] = kfs
            break

    return rot_curves, pos_curves


def supplement_keyframes(ikf_kfs, ab_kfs):
    """Supplement ik_fixed keyframes with AssetBundle keyframes if ik_fixed is incomplete.
    Use ik_fixed data when it has MORE keyframes (IK-baked), otherwise use AssetBundle."""
    if not ab_kfs:
        return ikf_kfs
    # If ik_fixed has more or equal keyframes, it's IK-baked — keep it
    if len(ikf_kfs) >= len(ab_kfs):
        return ikf_kfs
    # ik_fixed has fewer keyframes — use AssetBundle (has full animation range)
    return ab_kfs


def convert_rotation_curves(curves, duration, ab_rot_curves=None):
    """Convert rotation curves to Three.js quaternion tracks."""
    if ab_rot_curves is None:
        ab_rot_curves = {}
    tracks = []
    for curve in curves:
        path = curve.get('path', '')
        if should_skip_rotation(path):
            continue
        keyframes = curve.get('keyframes', [])
        if not keyframes:
            continue

        leaf_name = path.split('/')[-1]
        bone_name = strip_dots(leaf_name)

        # Supplement with AssetBundle data if ik_fixed is incomplete
        ab_kfs = ab_rot_curves.get(leaf_name, [])
        keyframes = supplement_keyframes(keyframes, ab_kfs)

        times = []
        values = []

        # Resample sparse curves for smoother interpolation
        if len(keyframes) < RESAMPLE_THRESHOLD and len(keyframes) > 2:
            times, values = catmull_rom_quat(keyframes, RESAMPLE_FPS, duration)
            # Apply convQuat to all resampled values
            conv_values = []
            for i in range(0, len(values), 4):
                cx, cy, cz, cw = conv_quat(values[i], values[i+1], values[i+2], values[i+3])
                conv_values.extend([cx, cy, cz, cw])
            values = conv_values
        else:
            for kf in keyframes:
                times.append(kf['time'])
                v = kf['value']  # [x, y, z, w]
                cx, cy, cz, cw = conv_quat(v[0], v[1], v[2], v[3])
                values.extend([cx, cy, cz, cw])

        # Rest pose (first keyframe) for return-to-rest
        rest_v = keyframes[0]['value']
        rest_cx, rest_cy, rest_cz, rest_cw = conv_quat(rest_v[0], rest_v[1], rest_v[2], rest_v[3])

        # If last keyframe ends before duration, add return-to-rest keyframe
        if times[-1] < duration - 0.01:
            times.append(duration)
            values.extend([rest_cx, rest_cy, rest_cz, rest_cw])

        tracks.append({
            'name': f'{bone_name}.quaternion',
            'type': 'quaternion',
            'times': times,
            'values': values,
        })

    return tracks


def convert_position_curves(curves, duration, ab_pos_curves=None):
    """Convert position curves to Three.js vector tracks (delta + Z negate)."""
    if ab_pos_curves is None:
        ab_pos_curves = {}
    tracks = []
    for curve in curves:
        path = curve.get('path', '')
        if should_skip(path):
            continue
        keyframes = curve.get('keyframes', [])
        if not keyframes:
            continue

        leaf_name = path.split('/')[-1]
        bone_name = strip_dots(leaf_name)

        # Supplement with AssetBundle data if ik_fixed is incomplete
        ab_kfs = ab_pos_curves.get(leaf_name, [])
        keyframes = supplement_keyframes(keyframes, ab_kfs)

        # Frame 0 as reference (animRest)
        rest = keyframes[0]['value']
        rest_x, rest_y, rest_z = rest[0], rest[1], rest[2]

        times = []
        values = []

        # Resample sparse position curves
        if len(keyframes) < RESAMPLE_THRESHOLD and len(keyframes) > 2:
            r_times, r_values = catmull_rom_vec(keyframes, RESAMPLE_FPS, duration)
            times = r_times
            values = []
            for i in range(0, len(r_values), 3):
                dx = r_values[i] - rest_x
                dy = r_values[i+1] - rest_y
                dz = r_values[i+2] - rest_z
                values.extend([dx, dy, -dz])
        else:
            for kf in keyframes:
                times.append(kf['time'])
                v = kf['value']
                dx = v[0] - rest_x
                dy = v[1] - rest_y
                dz = v[2] - rest_z
                values.extend([dx, dy, -dz])

        # If last keyframe ends before duration, add return-to-rest (delta=0)
        if times[-1] < duration - 0.01:
            times.append(duration)
            values.extend([0.0, 0.0, 0.0])

        tracks.append({
            'name': f'{bone_name}.position',
            'type': 'vector',
            'times': times,
            'values': values,
        })

    return tracks


def convert(input_path, output_path=None, assetbundle_path=None):
    """Convert an ik_fixed.json file to Three.js anim.json format."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load AssetBundle curves for supplementing incomplete ik_fixed data
    ab_rot, ab_pos = {}, {}
    if assetbundle_path:
        ab_rot, ab_pos = load_assetbundle_curves(assetbundle_path)
        if ab_rot:
            print(f'  AssetBundle loaded: {len(ab_rot)} rot + {len(ab_pos)} pos curves')

    # Compute duration
    duration = 0
    for curve_set in [data.get('rotation_curves', []), data.get('position_curves', [])]:
        for curve in curve_set:
            for kf in curve.get('keyframes', []):
                if kf['time'] > duration:
                    duration = kf['time']
    # Also check AssetBundle for duration
    for kfs in list(ab_rot.values()) + list(ab_pos.values()):
        for kf in kfs:
            if kf['time'] > duration:
                duration = kf['time']

    # Convert curves
    tracks = []
    tracks.extend(convert_rotation_curves(data.get('rotation_curves', []), duration, ab_rot))
    tracks.extend(convert_position_curves(data.get('position_curves', []), duration, ab_pos))

    # Build output
    output = {
        'name': data.get('name', os.path.splitext(os.path.basename(input_path))[0]),
        'duration': duration,
        'sample_rate': data.get('sample_rate', 30),
        'tracks': tracks,
        '_source': os.path.basename(input_path),
        '_coordinate_space': 'gltf',
        '_position_encoding': 'delta_from_frame0',
    }

    # Auto-generate output path
    if output_path is None:
        base = input_path.replace('_ik_fixed.json', '').replace('_ik_fixed', '')
        output_path = base + '.anim.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f)

    # Stats
    rot_tracks = sum(1 for t in tracks if t['type'] == 'quaternion')
    pos_tracks = sum(1 for t in tracks if t['type'] == 'vector')
    size_kb = os.path.getsize(output_path) / 1024

    print(f'Converted: {os.path.basename(input_path)} → {os.path.basename(output_path)}')
    print(f'  Name: {output["name"]}, Duration: {duration:.3f}s')
    print(f'  Tracks: {rot_tracks} rotation + {pos_tracks} position = {len(tracks)} total')
    print(f'  Size: {size_kb:.1f} KB')

    return output_path


def main():
    parser = argparse.ArgumentParser(description='Convert ik_fixed.json to Three.js anim.json')
    parser.add_argument('input', help='Input *_ik_fixed.json file or directory for batch')
    parser.add_argument('-o', '--output', help='Output file path (auto-generated if omitted)')
    parser.add_argument('-a', '--assetbundle', help='Unity AssetBundle file to supplement missing keyframes')
    parser.add_argument('--batch', action='store_true', help='Batch convert all *_ik_fixed.json in directory')
    args = parser.parse_args()

    if args.batch or os.path.isdir(args.input):
        directory = args.input
        files = [f for f in os.listdir(directory) if f.endswith('_ik_fixed.json')]
        if not files:
            print(f'No *_ik_fixed.json files found in {directory}')
            sys.exit(1)
        for f in sorted(files):
            # Auto-detect matching AssetBundle
            ab_name = f.replace('_ik_fixed.json', '')
            ab_path = os.path.join(directory, ab_name)
            ab = ab_path if os.path.exists(ab_path) else args.assetbundle
            convert(os.path.join(directory, f), assetbundle_path=ab)
            print()
    else:
        convert(args.input, args.output, args.assetbundle)


if __name__ == '__main__':
    main()
