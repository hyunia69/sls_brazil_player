"""
JSON Writer: SLMBData -> JSON file for web player consumption.
Outputs quaternions in BVH space (Qr removed for Type-2/3 joints).
"""

import json
from .slmb_decoder import SLMBData
from .constants import JOINT_ORDER, BLENDSHAPE_ID_TO_NAME, get_rotation_axes
from .math_utils import (
    euler2quaternion_xyz, rotationaxis_to_quaternion,
    quaternion_multiply, quaternion_inverse,
)


def _get_bvh_quaternion(jfd, joint_name, joint_type):
    """
    Get the BVH-space quaternion for a joint frame.
    For Type-0/1: quat is already in BVH space.
    For Type-2/3: quat is Q_enc = Q_bvh * Qr, need to undo Qr.
    For Type-4: quat is in identity axes (same as BVH space).
    """
    if joint_type in (0, 1, 4):
        return (jfd.qw, jfd.qx, jfd.qy, jfd.qz)

    # Type-2 and Type-3: Q_enc from decoder includes Qr
    # Reconstruct Q_enc from stored euler (more precise than using jfd.q)
    rx, ry, rz = get_rotation_axes(joint_name)
    if joint_type == 2:
        q_enc = euler2quaternion_xyz(jfd.euler_x, jfd.euler_y, jfd.euler_z, rx, ry, rz)
    else:  # Type-3
        q_enc = euler2quaternion_xyz(0, 0, jfd.euler_z, rx, ry, rz)

    # Q_bvh = Q_enc * inv(Qr)
    qr = rotationaxis_to_quaternion(rx, ry, rz)
    qr_inv = quaternion_inverse(qr)
    q_bvh = quaternion_multiply(q_enc, qr_inv)
    return q_bvh


def slmb_to_json(slmb_data: SLMBData, output_path: str, pretty: bool = False):
    """Convert decoded SLMBData to JSON file."""
    bmb = slmb_data.body
    fmb = slmb_data.face

    result = {
        "format": "SLMBData",
        "version": "1.0",
        "body": {
            "num_frames": bmb.num_frames,
            "frame_time": round(bmb.frame_time, 8),
            "joints": []
        },
        "face": {
            "num_frames": fmb.num_frames,
            "frame_times": [round(t, 6) for t in fmb.frame_times],
            "blendshapes": []
        }
    }

    # Body joints
    for slmb_idx, (joint_name, joint_type) in enumerate(JOINT_ORDER):
        joint_entry = {
            "name": joint_name,
            "type": joint_type,
            "frames": []
        }

        for f in range(bmb.num_frames):
            jfd = bmb.joint_data[slmb_idx][f]
            qw, qx, qy, qz = _get_bvh_quaternion(jfd, joint_name, joint_type)
            frame_data = {
                "q": [
                    round(qw, 6),
                    round(qx, 6),
                    round(qy, 6),
                    round(qz, 6),
                ]
            }
            # Only include translation for Type-0 (root)
            if joint_type == 0:
                frame_data["t"] = [
                    round(jfd.tx, 6),
                    round(jfd.ty, 6),
                    round(jfd.tz, 6),
                ]

            joint_entry["frames"].append(frame_data)

        result["body"]["joints"].append(joint_entry)

    # Face blendshapes
    for bs in fmb.blendshapes:
        name_info = BLENDSHAPE_ID_TO_NAME.get(bs.blend_shape_id, ("unknown", "unknown"))
        bs_entry = {
            "id": bs.blend_shape_id,
            "mesh": name_info[0],
            "name": name_info[1],
            "weights": {}
        }
        for frame_idx, weight in sorted(bs.weights.items()):
            bs_entry["weights"][str(frame_idx)] = round(weight, 5)

        result["face"]["blendshapes"].append(bs_entry)

    with open(output_path, 'w') as f:
        if pretty:
            json.dump(result, f, indent=2)
        else:
            json.dump(result, f, separators=(',', ':'))

    return output_path
