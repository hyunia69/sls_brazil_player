"""VLibras AssetBundle / JSON → glTF 2.0 converter.

Reads directly from Unity AssetBundle (via UnityPy) or CASA_full.json,
and outputs a glTF 2.0 GLB with the VLibras 84-bone skeleton and animation.

Coordinate conversion (Z-axis flip, LH→RH):
  Position:   [x, y, z] → [x, y, -z]
  Quaternion: [x, y, z, w] → [-x, -y, z, w]
"""

import json
import struct
import sys
from pathlib import Path


def load_from_asset_bundle(bundle_path):
    """Load animation data directly from Unity AssetBundle."""
    import UnityPy

    env = UnityPy.load(str(bundle_path))
    clip = None
    for obj in env.objects:
        if obj.type.name == 'AnimationClip':
            clip = obj.read()
            break
    if clip is None:
        raise ValueError(f'No AnimationClip found in {bundle_path}')

    data = {
        'name': clip.m_Name,
        'sample_rate': clip.m_SampleRate,
        'bone_paths': [],
        'rotation_curves': [],
        'position_curves': [],
        'float_curves': [],
    }

    seen_paths = set()

    for rc in clip.m_RotationCurves:
        path = rc.path
        if path not in seen_paths:
            data['bone_paths'].append(path)
            seen_paths.add(path)
        keyframes = []
        for kf in rc.curve.m_Curve:
            keyframes.append({
                'time': kf.time,
                'value': [kf.value.x, kf.value.y, kf.value.z, kf.value.w]
            })
        data['rotation_curves'].append({
            'path': path,
            'keyframe_count': len(keyframes),
            'keyframes': keyframes,
        })

    for pc in clip.m_PositionCurves:
        path = pc.path
        if path not in seen_paths:
            data['bone_paths'].append(path)
            seen_paths.add(path)
        keyframes = []
        for kf in pc.curve.m_Curve:
            keyframes.append({
                'time': kf.time,
                'value': [kf.value.x, kf.value.y, kf.value.z]
            })
        data['position_curves'].append({
            'path': path,
            'keyframe_count': len(keyframes),
            'keyframes': keyframes,
        })

    for fc in clip.m_FloatCurves:
        keyframes = []
        for kf in fc.curve.m_Curve:
            keyframes.append({'time': kf.time, 'value': kf.value})
        data['float_curves'].append({
            'path': fc.path,
            'attribute': fc.attribute,
            'keyframe_count': len(keyframes),
            'keyframes': keyframes,
        })

    return data


def load_from_json(json_path):
    """Load from CASA_full.json (may have incomplete keyframes)."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert(input_path, output_path=None, scale=100.0):
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_suffix('.gltf')
    else:
        output_path = Path(output_path)

    # Detect input type
    if input_path.suffix == '.json':
        print(f'Loading from JSON: {input_path.name}')
        data = load_from_json(input_path)
    else:
        print(f'Loading from AssetBundle: {input_path.name}')
        data = load_from_asset_bundle(input_path)

    bone_paths = data['bone_paths']
    rotation_curves = data['rotation_curves']
    position_curves = data['position_curves']
    clip_name = data.get('name', 'animation')

    # Print keyframe stats
    total_kfs = sum(len(rc.get('keyframes', [])) for rc in rotation_curves)
    animated = sum(1 for rc in rotation_curves if len(rc.get('keyframes', [])) > 2)
    print(f'  Total rotation keyframes: {total_kfs} ({animated} animated bones)')

    # ── Build hierarchy ──
    path_to_index = {}
    nodes = []
    children_map = {}

    for bp in bone_paths:
        idx = len(nodes)
        path_to_index[bp] = idx
        leaf_name = bp.rsplit('/', 1)[-1] if '/' in bp else bp
        nodes.append({
            'name': leaf_name,
            'translation': [0, 0, 0],
            'rotation': [0, 0, 0, 1],
        })
        if '/' in bp:
            parent_path = bp.rsplit('/', 1)[0]
            if parent_path not in children_map:
                children_map[parent_path] = []
            children_map[parent_path].append(bp)

    for parent_path, child_paths in children_map.items():
        if parent_path in path_to_index:
            parent_idx = path_to_index[parent_path]
            nodes[parent_idx]['children'] = [path_to_index[cp] for cp in child_paths]

    # Set rest positions: [x, y, z] → [x, y, -z]
    for pc in position_curves:
        path = pc['path']
        kfs = pc.get('keyframes', [])
        if not kfs or path not in path_to_index:
            continue
        idx = path_to_index[path]
        p = kfs[0]['value']
        nodes[idx]['translation'] = [p[0] * scale, p[1] * scale, -p[2] * scale]

    # Set rest rotations: Unity [x,y,z,w] → glTF [-x,-y,z,w]
    for rc in rotation_curves:
        path = rc['path']
        kfs = rc.get('keyframes', [])
        if not kfs or path not in path_to_index:
            continue
        idx = path_to_index[path]
        v = kfs[0]['value']
        nodes[idx]['rotation'] = [-v[0], -v[1], v[2], v[3]]

    # ── Build animation ──
    bin_data = bytearray()
    buffer_views = []
    accessors = []
    samplers = []
    channels = []

    def add_buffer_view(raw_bytes):
        while len(bin_data) % 4 != 0:
            bin_data.append(0)
        offset = len(bin_data)
        bin_data.extend(raw_bytes)
        idx = len(buffer_views)
        buffer_views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(raw_bytes)})
        return idx

    def add_accessor(bv_idx, comp_type, count, type_str, min_val=None, max_val=None):
        idx = len(accessors)
        acc = {'bufferView': bv_idx, 'componentType': comp_type, 'count': count, 'type': type_str}
        if min_val is not None: acc['min'] = min_val
        if max_val is not None: acc['max'] = max_val
        accessors.append(acc)
        return idx

    # Rotation channels
    for rc in rotation_curves:
        path = rc['path']
        kfs = rc.get('keyframes', [])
        if len(kfs) < 2 or path not in path_to_index:
            continue
        node_idx = path_to_index[path]

        time_bytes = bytearray()
        for kf in kfs:
            time_bytes.extend(struct.pack('<f', kf['time']))
        time_bv = add_buffer_view(bytes(time_bytes))
        time_acc = add_accessor(time_bv, 5126, len(kfs), 'SCALAR',
                                [kfs[0]['time']], [kfs[-1]['time']])

        # Unity [x,y,z,w] → glTF [-x,-y,z,w]
        rot_bytes = bytearray()
        for kf in kfs:
            v = kf['value']
            rot_bytes.extend(struct.pack('<ffff', -v[0], -v[1], v[2], v[3]))
        rot_bv = add_buffer_view(bytes(rot_bytes))
        rot_acc = add_accessor(rot_bv, 5126, len(kfs), 'VEC4')

        sampler_idx = len(samplers)
        samplers.append({'input': time_acc, 'interpolation': 'LINEAR', 'output': rot_acc})
        channels.append({'sampler': sampler_idx, 'target': {'node': node_idx, 'path': 'rotation'}})

    # Position channels (animated, >2 keyframes)
    for pc in position_curves:
        path = pc['path']
        kfs = pc.get('keyframes', [])
        if len(kfs) <= 2 or path not in path_to_index:
            continue
        node_idx = path_to_index[path]

        time_bytes = bytearray()
        for kf in kfs:
            time_bytes.extend(struct.pack('<f', kf['time']))
        time_bv = add_buffer_view(bytes(time_bytes))
        time_acc = add_accessor(time_bv, 5126, len(kfs), 'SCALAR',
                                [kfs[0]['time']], [kfs[-1]['time']])

        pos_bytes = bytearray()
        for kf in kfs:
            p = kf['value']
            pos_bytes.extend(struct.pack('<fff', p[0] * scale, p[1] * scale, -p[2] * scale))
        pos_bv = add_buffer_view(bytes(pos_bytes))
        pos_acc = add_accessor(pos_bv, 5126, len(kfs), 'VEC3')

        sampler_idx = len(samplers)
        samplers.append({'input': time_acc, 'interpolation': 'LINEAR', 'output': pos_acc})
        channels.append({'sampler': sampler_idx, 'target': {'node': node_idx, 'path': 'translation'}})

    # Root nodes
    child_set = set()
    for n in nodes:
        for ci in n.get('children', []):
            child_set.add(ci)
    root_nodes = [i for i in range(len(nodes)) if i not in child_set]

    duration = 0
    for rc in rotation_curves:
        kfs = rc.get('keyframes', [])
        if kfs:
            duration = max(duration, kfs[-1]['time'])

    gltf = {
        'asset': {'version': '2.0', 'generator': 'VLibras-to-glTF'},
        'scene': 0,
        'scenes': [{'name': clip_name, 'nodes': root_nodes}],
        'nodes': nodes,
        'buffers': [{'byteLength': len(bin_data)}],
        'bufferViews': buffer_views,
        'accessors': accessors,
    }
    if samplers:
        gltf['animations'] = [{'name': clip_name, 'samplers': samplers, 'channels': channels}]

    # Write .gltf + .bin or .glb
    if str(output_path).endswith('.glb'):
        # GLB (single binary file)
        json_str = json.dumps(gltf, separators=(',', ':'))
        json_bytes = json_str.encode('utf-8')
        while len(json_bytes) % 4 != 0:
            json_bytes += b' '
        bin_padded = bytearray(bin_data)
        while len(bin_padded) % 4 != 0:
            bin_padded.append(0)
        total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_padded)
        with open(output_path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, total_length))
            f.write(struct.pack('<II', len(json_bytes), 0x4E4F534A))
            f.write(json_bytes)
            f.write(struct.pack('<II', len(bin_padded), 0x004E4942))
            f.write(bytes(bin_padded))
        print(f'Output: {output_path.name} (GLB)')
    else:
        # .gltf + .bin (separate files)
        bin_path = output_path.with_suffix('.bin')
        gltf['buffers'][0]['uri'] = bin_path.name
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(gltf, f, indent=2)
        with open(bin_path, 'wb') as f:
            f.write(bin_data)
        print(f'Output: {output_path.name} + {bin_path.name} (glTF)')

    print(f'  Bones: {len(nodes)}, Channels: {len(channels)}, Duration: {duration:.3f}s')
    print(f'  Scale: {scale}x')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: python {sys.argv[0]} <CASA|CASA_full.json> [output.glb] [scale]')
        sys.exit(1)
    in_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    sc = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
    convert(in_file, out_file, scale=sc)
