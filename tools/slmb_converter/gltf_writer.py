"""
glTF Writer: SLMB decoded data -> glTF 2.0 animation.
Based on SBTVD OG-06 Annex D.2.6.3 (SLMB -> glTF conversion).
"""

import json
import struct
import math
from typing import List, Dict, Tuple, Optional

from .constants import (
    JOINT_ORDER, SKELETON_HIERARCHY, REFPOSE_FROM_PARENT,
    BLENDSHAPE_ID_TO_NAME, MESH_BLENDSHAPE_MAP,
    get_rotation_axes, NUM_JOINTS,
)
from .slmb_decoder import SLMBData, BodyMotionBlock, FaceMotionBlock
from .math_utils import (
    euler2quaternion_xyz, rotationaxis_to_quaternion,
    quaternion_multiply, quaternion_inverse,
)


def _build_skeleton_nodes() -> Tuple[List[dict], Dict[str, int]]:
    """Build glTF nodes for the skeleton."""
    nodes = []
    name_to_idx = {}

    # First pass: create all nodes
    all_joints = [name for name, _ in JOINT_ORDER]
    for joint_name in all_joints:
        idx = len(nodes)
        name_to_idx[joint_name] = idx
        offset = REFPOSE_FROM_PARENT.get(joint_name, (0, 0, 0))
        node = {
            "name": joint_name,
            "translation": list(offset),
            "rotation": [0, 0, 0, 1],  # identity quaternion (x,y,z,w in glTF)
        }
        nodes.append(node)

    # Second pass: set children
    for joint_name in all_joints:
        children = SKELETON_HIERARCHY.get(joint_name, [])
        if children:
            child_indices = [name_to_idx[c] for c in children if c in name_to_idx]
            if child_indices:
                nodes[name_to_idx[joint_name]]["children"] = child_indices

    return nodes, name_to_idx


def slmb_to_gltf(slmb_data: SLMBData, output_path: str):
    """
    Convert decoded SLMB data to glTF 2.0 file with animation.
    Implements OG-06 D.2.6.3 SLMB -> glTF conversion.
    """
    bmb = slmb_data.body
    fmb = slmb_data.face

    # Build skeleton
    nodes, name_to_idx = _build_skeleton_nodes()

    # Prepare binary buffer
    bin_data = bytearray()
    buffer_views = []
    accessors = []
    samplers = []
    channels = []

    def _add_buffer_view(data: bytes) -> int:
        """Add data to binary buffer, return bufferView index."""
        # Align to 4 bytes
        while len(bin_data) % 4 != 0:
            bin_data.append(0)
        offset = len(bin_data)
        bin_data.extend(data)
        idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": len(data),
        })
        return idx

    def _add_accessor(bv_idx: int, component_type: int, count: int,
                      type_str: str, min_val=None, max_val=None) -> int:
        """Add accessor, return accessor index."""
        idx = len(accessors)
        acc = {
            "bufferView": bv_idx,
            "componentType": component_type,
            "count": count,
            "type": type_str,
        }
        if min_val is not None:
            acc["min"] = min_val
        if max_val is not None:
            acc["max"] = max_val
        accessors.append(acc)
        return idx

    # ─── Body Motion: Translation & Rotation Channels ───

    num_frames = bmb.num_frames
    frame_time = bmb.frame_time

    # Time accessor (shared for body motion)
    time_data = bytearray()
    for f in range(num_frames):
        time_data.extend(struct.pack('<f', f * frame_time))
    time_bv = _add_buffer_view(bytes(time_data))
    time_max = (num_frames - 1) * frame_time if num_frames > 0 else 0
    body_time_acc = _add_accessor(time_bv, 5126, num_frames, "SCALAR",
                                  [0.0], [time_max])  # 5126 = FLOAT

    for slmb_idx, (joint_name, joint_type) in enumerate(JOINT_ORDER):
        if joint_name not in name_to_idx:
            continue
        node_idx = name_to_idx[joint_name]

        # Translation channel (Type-0 only)
        if joint_type == 0:
            trans_data = bytearray()
            for f in range(num_frames):
                jfd = bmb.joint_data[slmb_idx][f]
                trans_data.extend(struct.pack('<fff', jfd.tx, jfd.ty, jfd.tz))

            trans_bv = _add_buffer_view(bytes(trans_data))
            trans_acc = _add_accessor(trans_bv, 5126, num_frames, "VEC3")

            sampler_idx = len(samplers)
            samplers.append({
                "input": body_time_acc,
                "interpolation": "LINEAR",
                "output": trans_acc,
            })
            channels.append({
                "sampler": sampler_idx,
                "target": {"node": node_idx, "path": "translation"},
            })

        # Rotation channel (all joints)
        # SLMB decoded quaternions include Qr (custom rotation axes).
        # The glTF skeleton has identity rest poses, so we must remove Qr
        # to output Q_delta = Q_bvh (the original rotation without Qr basis).
        # This ensures the direct skeleton's world quaternions match BVH original.
        rx, ry, rz = get_rotation_axes(joint_name)
        qr = rotationaxis_to_quaternion(rx, ry, rz)
        qr_inv = quaternion_inverse(qr)

        rot_data = bytearray()
        for f in range(num_frames):
            jfd = bmb.joint_data[slmb_idx][f]
            q_abs = (jfd.qw, jfd.qx, jfd.qy, jfd.qz)
            q_delta = quaternion_multiply(q_abs, qr_inv)
            # glTF quaternion order: x, y, z, w
            rot_data.extend(struct.pack('<ffff', q_delta[1], q_delta[2], q_delta[3], q_delta[0]))

        rot_bv = _add_buffer_view(bytes(rot_data))
        rot_acc = _add_accessor(rot_bv, 5126, num_frames, "VEC4")

        sampler_idx = len(samplers)
        samplers.append({
            "input": body_time_acc,
            "interpolation": "LINEAR",
            "output": rot_acc,
        })
        channels.append({
            "sampler": sampler_idx,
            "target": {"node": node_idx, "path": "rotation"},
        })

    # ─── Face Motion: Weights Channels ───

    if fmb.num_frames > 0 and fmb.blendshapes:
        # Face time accessor
        face_time_data = bytearray()
        for t in fmb.frame_times:
            face_time_data.extend(struct.pack('<f', t))
        face_time_bv = _add_buffer_view(bytes(face_time_data))
        face_time_max = fmb.frame_times[-1] if fmb.frame_times else 0
        face_time_acc = _add_accessor(face_time_bv, 5126, fmb.num_frames, "SCALAR",
                                      [0.0], [face_time_max])

        # Group blendshapes by mesh
        mesh_bs: Dict[str, List[Tuple[str, Dict[int, float]]]] = {}
        for bs in fmb.blendshapes:
            if bs.blend_shape_id in BLENDSHAPE_ID_TO_NAME:
                mesh_name, bs_name = BLENDSHAPE_ID_TO_NAME[bs.blend_shape_id]
                if mesh_name not in mesh_bs:
                    mesh_bs[mesh_name] = []
                mesh_bs[mesh_name].append((bs_name, bs.weights))

        # Create mesh nodes and weight channels
        for mesh_name, bs_list in mesh_bs.items():
            # Get all target names for this mesh from the spec
            all_targets = list(MESH_BLENDSHAPE_MAP.get(mesh_name, {}).values())
            if not all_targets:
                continue

            # Create mesh node (no mesh reference - skeleton-only animation)
            mesh_node_idx = len(nodes)
            node = {
                "name": mesh_name,
            }
            nodes.append(node)

            # Build weight data: for each frame, weights for ALL targets of this mesh
            num_targets = len(all_targets)
            target_name_to_idx = {name: i for i, name in enumerate(all_targets)}

            weights_data = bytearray()
            for f in range(fmb.num_frames):
                for t_idx in range(num_targets):
                    w = 0.0
                    # Find if any blendshape matches this target at this frame
                    for bs_name, bs_weights in bs_list:
                        if all_targets[t_idx] == bs_name:
                            w = bs_weights.get(f, 0.0)
                            break
                    weights_data.extend(struct.pack('<f', w))

            weights_bv = _add_buffer_view(bytes(weights_data))
            weights_acc = _add_accessor(weights_bv, 5126,
                                        fmb.num_frames * num_targets, "SCALAR")

            sampler_idx = len(samplers)
            samplers.append({
                "input": face_time_acc,
                "interpolation": "LINEAR",
                "output": weights_acc,
            })
            channels.append({
                "sampler": sampler_idx,
                "target": {"node": mesh_node_idx, "path": "weights"},
            })

    # ─── Build glTF JSON ───

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "SLMB Converter v1.0 (ABNT NBR 25606)",
        },
        "scene": 0,
        "scenes": [{"nodes": [name_to_idx["hips_JNT"]]}],
        "nodes": nodes,
        "animations": [{
            "name": "sign_language_motion",
            "samplers": samplers,
            "channels": channels,
        }] if samplers else [],
        "buffers": [{
            "byteLength": len(bin_data),
        }],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }

    # Write as .gltf + .bin or embedded
    if output_path.endswith('.gltf'):
        bin_path = output_path.replace('.gltf', '.bin')
        gltf["buffers"][0]["uri"] = bin_path.split('/')[-1].split('\\')[-1]
        with open(output_path, 'w') as f:
            json.dump(gltf, f, indent=2)
        with open(bin_path, 'wb') as f:
            f.write(bin_data)
    elif output_path.endswith('.glb'):
        _write_glb(output_path, gltf, bytes(bin_data))
    else:
        output_path += '.gltf'
        bin_path = output_path.replace('.gltf', '.bin')
        gltf["buffers"][0]["uri"] = bin_path.split('/')[-1].split('\\')[-1]
        with open(output_path, 'w') as f:
            json.dump(gltf, f, indent=2)
        with open(bin_path, 'wb') as f:
            f.write(bin_data)


def _write_glb(filepath: str, gltf_json: dict, bin_data: bytes):
    """Write GLB (binary glTF) file."""
    json_str = json.dumps(gltf_json, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')

    # Pad JSON to 4-byte boundary
    while len(json_bytes) % 4 != 0:
        json_bytes += b' '

    # Pad binary to 4-byte boundary
    bin_padded = bytearray(bin_data)
    while len(bin_padded) % 4 != 0:
        bin_padded.append(0)

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_padded)

    with open(filepath, 'wb') as f:
        # GLB header
        f.write(struct.pack('<III', 0x46546C67, 2, total_length))  # magic, version, length
        # JSON chunk
        f.write(struct.pack('<II', len(json_bytes), 0x4E4F534A))  # length, type=JSON
        f.write(json_bytes)
        # BIN chunk
        f.write(struct.pack('<II', len(bin_padded), 0x004E4942))  # length, type=BIN
        f.write(bin_padded)
