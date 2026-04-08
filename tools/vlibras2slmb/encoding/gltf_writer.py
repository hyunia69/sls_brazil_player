"""glTF 2.0 writer for decoded SLMB data.

Produces a glTF file with embedded skeleton animation suitable for playback
in Three.js (signlanguagePC ABNTPlayer).

Output structure:
    - Nodes: 46 bone nodes following ABNT skeleton hierarchy
    - Skin:  Single skin referencing all 46 joints
    - Mesh:  Minimal placeholder (single triangle) -- real avatar loaded separately
    - Animation: One clip with quaternion tracks per joint + root translation

The glTF uses embedded base64 buffers (no separate .bin file) for portability.
"""

from __future__ import annotations

import base64
import json
import struct
from pathlib import Path
from typing import Any, Optional

import numpy as np

import numpy as np_np

from ..data.joint_types import JOINT_ENCODING_ORDER
from ..data.blendshape_map import ABNT_BLENDSHAPE_NAMES
from ..data.skeleton_map import VLIBRAS_TO_ABNT
from ..data.vlibras_bind_pose import VLIBRAS_BIND_POSE
from ..math_utils.coordinate import unity_quat_to_abnt
from ..math_utils.quaternion import normalize as q_normalize, inverse as q_inverse, multiply as q_multiply


# ---------------------------------------------------------------------------
# ABNT skeleton hierarchy (parent relationships)
# ---------------------------------------------------------------------------

_PARENT_MAP: dict[str, Optional[str]] = {
    "hips_JNT": None,
    "spine_JNT": "hips_JNT",
    "spine1_JNT": "spine_JNT",
    "spine2_JNT": "spine1_JNT",
    "neck_JNT": "spine2_JNT",
    "head_JNT": "neck_JNT",
    "l_eye_LOC": "head_JNT",
    "r_eye_LOC": "head_JNT",
    "l_shoulder_JNT": "spine2_JNT",
    "l_arm_JNT": "l_shoulder_JNT",
    "l_forearm_JNT": "l_arm_JNT",
    "l_hand_JNT": "l_forearm_JNT",
    "r_shoulder_JNT": "spine2_JNT",
    "r_arm_JNT": "r_shoulder_JNT",
    "r_forearm_JNT": "r_arm_JNT",
    "r_hand_JNT": "r_forearm_JNT",
    # Left hand
    "l_handThumb1_JNT": "l_hand_JNT",
    "l_handThumb2_JNT": "l_handThumb1_JNT",
    "l_handThumb3_JNT": "l_handThumb2_JNT",
    "l_handIndex1_JNT": "l_hand_JNT",
    "l_handIndex2_JNT": "l_handIndex1_JNT",
    "l_handIndex3_JNT": "l_handIndex2_JNT",
    "l_handMiddle1_JNT": "l_hand_JNT",
    "l_handMiddle2_JNT": "l_handMiddle1_JNT",
    "l_handMiddle3_JNT": "l_handMiddle2_JNT",
    "l_handRing1_JNT": "l_hand_JNT",
    "l_handRing2_JNT": "l_handRing1_JNT",
    "l_handRing3_JNT": "l_handRing2_JNT",
    "l_handPinky1_JNT": "l_hand_JNT",
    "l_handPinky2_JNT": "l_handPinky1_JNT",
    "l_handPinky3_JNT": "l_handPinky2_JNT",
    # Right hand
    "r_handThumb1_JNT": "r_hand_JNT",
    "r_handThumb2_JNT": "r_handThumb1_JNT",
    "r_handThumb3_JNT": "r_handThumb2_JNT",
    "r_handIndex1_JNT": "r_hand_JNT",
    "r_handIndex2_JNT": "r_handIndex1_JNT",
    "r_handIndex3_JNT": "r_handIndex2_JNT",
    "r_handMiddle1_JNT": "r_hand_JNT",
    "r_handMiddle2_JNT": "r_handMiddle1_JNT",
    "r_handMiddle3_JNT": "r_handMiddle2_JNT",
    "r_handRing1_JNT": "r_hand_JNT",
    "r_handRing2_JNT": "r_handRing1_JNT",
    "r_handRing3_JNT": "r_handRing2_JNT",
    "r_handPinky1_JNT": "r_hand_JNT",
    "r_handPinky2_JNT": "r_handPinky1_JNT",
    "r_handPinky3_JNT": "r_handPinky2_JNT",
}


def _build_abnt_rest_pose() -> dict[str, np_np.ndarray]:
    """Build the decoded rest-pose quaternion for each joint.

    The "rest quaternion" is the value that the SLMB decoder returns when
    the character is in the neutral standing pose:

    - Type-0/1 joints: The SLMB stores absolute rotations.  At rest these
      equal the VLibras bind-pose after coordinate conversion.
      → rest = unity_quat_to_abnt(Q_bind_vlibras)

    - Type-2/3/4 joints: The encoder applied bind-pose removal and rebased
      to the ABNT custom rotation axes (Qr).  At rest the Euler angles are
      all zero, so the decoder reconstructs Qr.
      → rest = rotationaxis_to_quaternion(RX, RY, RZ)

    Returns:
        Dict mapping ABNT joint name to decoded rest quaternion [w, x, y, z].
    """
    from ..data.rotation_axes import ROTATION_AXES
    from ..math_utils.euler import rotationaxis_to_quaternion

    abnt_to_vlibras = {abnt: vl for vl, abnt in VLIBRAS_TO_ABNT.items()}
    rest_pose: dict[str, np_np.ndarray] = {}

    for _idx, joint_name, jtype in JOINT_ENCODING_ORDER:
        if jtype in (2, 3, 4):
            # Type-2/3/4: bind-pose was removed during encoding, replaced with Qr
            axes = ROTATION_AXES.get(joint_name)
            if axes:
                RX, RY, RZ = axes
                rest_pose[joint_name] = q_normalize(
                    rotationaxis_to_quaternion(RX, RY, RZ)
                )
            else:
                rest_pose[joint_name] = np_np.array([1.0, 0.0, 0.0, 0.0])
        else:
            # Type-0/1: absolute rotation, rest = bind pose in ABNT space
            vl_bone = abnt_to_vlibras.get(joint_name)
            if vl_bone and vl_bone in VLIBRAS_BIND_POSE:
                bp = VLIBRAS_BIND_POSE[vl_bone]
                q_bind = np_np.array(bp, dtype=np_np.float64)
                q_abnt = unity_quat_to_abnt(q_bind)
                rest_pose[joint_name] = q_normalize(q_abnt)
            else:
                rest_pose[joint_name] = np_np.array([1.0, 0.0, 0.0, 0.0])

    return rest_pose


def _build_buffer(data: bytes) -> dict:
    """Create a glTF buffer with embedded base64 data."""
    encoded = base64.b64encode(data).decode("ascii")
    return {
        "uri": f"data:application/octet-stream;base64,{encoded}",
        "byteLength": len(data),
    }


def write_gltf(
    body_data: dict[str, Any],
    face_data: Optional[dict[str, Any]],
    output_path: str,
    animation_name: str = "sign_animation",
) -> None:
    """Write decoded SLMB data as a glTF 2.0 file with animation.

    Args:
        body_data: Decoded body motion (from decode_body_motion_block).
            Keys: 'num_frames', 'frame_time', 'joint_rotations', 'root_translations'
        face_data: Decoded face motion (from decode_face_motion_block), or None.
            Keys: 'num_frames', 'frame_times', 'blendshape_weights'
        output_path: Path for output .gltf file.
        animation_name: Name for the animation clip.
    """
    num_frames = body_data["num_frames"]
    frame_time = body_data["frame_time"]
    joint_rotations = body_data["joint_rotations"]
    root_translations = body_data["root_translations"]

    # Collect all joint names in hierarchy order (BFS from root)
    joint_names = _get_hierarchy_order()
    name_to_node_idx: dict[str, int] = {}
    for i, name in enumerate(joint_names):
        name_to_node_idx[name] = i

    # -----------------------------------------------------------------------
    # Build binary buffer: timestamps + rotation data + translation data
    # -----------------------------------------------------------------------
    buf = bytearray()
    accessor_list: list[dict] = []
    buffer_view_list: list[dict] = []

    # --- Time accessor (shared by all channels) ---
    time_offset = len(buf)
    time_min = 0.0
    time_max = (num_frames - 1) * frame_time
    for f in range(num_frames):
        buf += struct.pack("<f", f * frame_time)
    time_byte_length = len(buf) - time_offset

    buffer_view_list.append({
        "buffer": 0,
        "byteOffset": time_offset,
        "byteLength": time_byte_length,
    })
    time_bv_idx = len(buffer_view_list) - 1

    accessor_list.append({
        "bufferView": time_bv_idx,
        "componentType": 5126,  # FLOAT
        "count": num_frames,
        "type": "SCALAR",
        "min": [time_min],
        "max": [time_max],
    })
    time_acc_idx = len(accessor_list) - 1

    # --- Animation channels and samplers ---
    channels: list[dict] = []
    samplers: list[dict] = []

    # Build ABNT rest pose for delta computation
    abnt_rest = _build_abnt_rest_pose()

    # Rotation tracks for each joint
    # Store DELTA rotations: Q_delta = Q_anim * inv(Q_rest_abnt)
    # This makes the animation relative to identity (rest pose).
    # The target player (ABNTPlayer) applies: Q_final = Q_rest_target * Q_delta
    for joint_name in joint_names:
        rotations = joint_rotations.get(joint_name)
        if rotations is None:
            continue

        node_idx = name_to_node_idx[joint_name]
        data_offset = len(buf)

        q_rest = abnt_rest.get(joint_name, np_np.array([1., 0., 0., 0.]))
        q_rest_inv = q_inverse(q_rest)

        for f in range(num_frames):
            q = rotations[f]  # [w, x, y, z] in ABNT space (absolute)
            # Compute delta: Q_delta = Q_anim * inv(Q_rest)
            q_delta = q_multiply(q, q_rest_inv)
            q_delta = q_normalize(q_delta)
            # Write in glTF [x, y, z, w] order (raw ABNT space)
            buf += struct.pack("<ffff",
                               float(q_delta[1]), float(q_delta[2]),
                               float(q_delta[3]), float(q_delta[0]))

        data_byte_length = len(buf) - data_offset

        buffer_view_list.append({
            "buffer": 0,
            "byteOffset": data_offset,
            "byteLength": data_byte_length,
        })
        rot_bv_idx = len(buffer_view_list) - 1

        accessor_list.append({
            "bufferView": rot_bv_idx,
            "componentType": 5126,  # FLOAT
            "count": num_frames,
            "type": "VEC4",
        })
        rot_acc_idx = len(accessor_list) - 1

        sampler_idx = len(samplers)
        samplers.append({
            "input": time_acc_idx,
            "output": rot_acc_idx,
            "interpolation": "LINEAR",
        })
        channels.append({
            "sampler": sampler_idx,
            "target": {
                "node": node_idx,
                "path": "rotation",
            },
        })

    # Translation track for root (hips_JNT)
    if root_translations and len(root_translations) == num_frames:
        root_node_idx = name_to_node_idx.get("hips_JNT", 0)
        data_offset = len(buf)

        for f in range(num_frames):
            pos = root_translations[f]  # [x, y, z] in ABNT space
            # Write raw position; coordinate conversion handled by player
            buf += struct.pack("<fff", float(pos[0]), float(pos[1]), float(pos[2]))

        data_byte_length = len(buf) - data_offset

        buffer_view_list.append({
            "buffer": 0,
            "byteOffset": data_offset,
            "byteLength": data_byte_length,
        })
        pos_bv_idx = len(buffer_view_list) - 1

        accessor_list.append({
            "bufferView": pos_bv_idx,
            "componentType": 5126,
            "count": num_frames,
            "type": "VEC3",
        })
        pos_acc_idx = len(accessor_list) - 1

        sampler_idx = len(samplers)
        samplers.append({
            "input": time_acc_idx,
            "output": pos_acc_idx,
            "interpolation": "LINEAR",
        })
        channels.append({
            "sampler": sampler_idx,
            "target": {
                "node": root_node_idx,
                "path": "translation",
            },
        })

    # -----------------------------------------------------------------------
    # Build node hierarchy
    # -----------------------------------------------------------------------
    nodes: list[dict] = []
    for joint_name in joint_names:
        node: dict[str, Any] = {"name": joint_name}
        # Find children
        children_indices = []
        for child_name, parent_name in _PARENT_MAP.items():
            if parent_name == joint_name:
                children_indices.append(name_to_node_idx[child_name])
        if children_indices:
            node["children"] = sorted(children_indices)
        nodes.append(node)

    # -----------------------------------------------------------------------
    # Assemble glTF document
    # -----------------------------------------------------------------------
    bin_data = bytes(buf)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.suffix.lower() == ".glb":
        # Write GLB (binary glTF) -- avoids data URI resolution issues
        _write_glb(
            nodes, name_to_node_idx, animation_name,
            channels, samplers, buffer_view_list, accessor_list,
            bin_data, out,
        )
    else:
        # Write .gltf with embedded base64 buffer
        gltf: dict[str, Any] = {
            "asset": {
                "version": "2.0",
                "generator": "vlibras2slmb glTF writer",
            },
            "scene": 0,
            "scenes": [{"nodes": [name_to_node_idx["hips_JNT"]]}],
            "nodes": nodes,
            "animations": [{
                "name": animation_name,
                "channels": channels,
                "samplers": samplers,
            }],
            "buffers": [_build_buffer(bin_data)],
            "bufferViews": buffer_view_list,
            "accessors": accessor_list,
        }

        with open(out, "w", encoding="utf-8") as f:
            json.dump(gltf, f, indent=2)

    print(f"[glTF] Written: {out} ({len(bin_data)} bytes animation data, "
          f"{num_frames} frames, {len(channels)} channels)")


def _write_glb(
    nodes: list[dict],
    name_to_node_idx: dict[str, int],
    animation_name: str,
    channels: list[dict],
    samplers: list[dict],
    buffer_view_list: list[dict],
    accessor_list: list[dict],
    bin_data: bytes,
    out: Path,
) -> None:
    """Write a GLB (binary glTF) file.

    GLB format (spec section 6.2):
        Header: magic(4) + version(4) + length(4)
        Chunk 0 (JSON): length(4) + type(4) + data (padded to 4-byte with spaces)
        Chunk 1 (BIN):  length(4) + type(4) + data (padded to 4-byte with 0x00)
    """
    gltf: dict[str, Any] = {
        "asset": {
            "version": "2.0",
            "generator": "vlibras2slmb glTF writer",
        },
        "scene": 0,
        "scenes": [{"nodes": [name_to_node_idx["hips_JNT"]]}],
        "nodes": nodes,
        "animations": [{
            "name": animation_name,
            "channels": channels,
            "samplers": samplers,
        }],
        "buffers": [{"byteLength": len(bin_data)}],
        "bufferViews": buffer_view_list,
        "accessors": accessor_list,
    }

    json_str = json.dumps(gltf, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")

    # Pad JSON chunk to 4-byte alignment with spaces (0x20)
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b" " * json_pad

    # Pad BIN chunk to 4-byte alignment with null bytes
    bin_pad = (4 - len(bin_data) % 4) % 4
    bin_padded = bin_data + b"\x00" * bin_pad

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_padded)

    with open(out, "wb") as f:
        # GLB header
        f.write(struct.pack("<I", 0x46546C67))  # magic: "glTF"
        f.write(struct.pack("<I", 2))            # version: 2
        f.write(struct.pack("<I", total_length))

        # JSON chunk
        f.write(struct.pack("<I", len(json_bytes)))
        f.write(struct.pack("<I", 0x4E4F534A))  # type: "JSON"
        f.write(json_bytes)

        # BIN chunk
        f.write(struct.pack("<I", len(bin_padded)))
        f.write(struct.pack("<I", 0x004E4942))  # type: "BIN\0"
        f.write(bin_padded)


def _get_hierarchy_order() -> list[str]:
    """Return joint names in breadth-first hierarchy order."""
    # Start with root, then BFS
    order: list[str] = []
    queue = ["hips_JNT"]

    while queue:
        current = queue.pop(0)
        order.append(current)
        # Find children in stable order
        children = sorted(
            [name for name, parent in _PARENT_MAP.items() if parent == current]
        )
        queue.extend(children)

    return order
