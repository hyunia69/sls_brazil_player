"""
BVH Writer: SLMB decoded data -> BVH file output.
Based on SBTVD OG-06 Annex D.2.4.4 (SLMB -> BVH conversion).
"""

import math
from typing import List, TextIO

from .constants import (
    JOINT_ORDER, SKELETON_HIERARCHY, REFPOSE_FROM_PARENT, REFPOSE_END,
    get_rotation_axes, IDENTITY_AXES,
)
from .slmb_decoder import SLMBData, BodyMotionBlock
from .math_utils import (
    quaternion2euler_yxz, euler2quaternion_xyz,
    rotationaxis_to_quaternion, quaternion_multiply, quaternion_inverse,
)


# BVH hierarchy traversal order (depth-first from hips_JNT)
def _get_bvh_joint_order() -> List[str]:
    """Get joints in BVH hierarchy declaration order (depth-first)."""
    order = []

    def _traverse(name: str):
        order.append(name)
        children = SKELETON_HIERARCHY.get(name, [])
        for child in children:
            _traverse(child)

    _traverse("hips_JNT")
    return order


BVH_JOINT_ORDER = _get_bvh_joint_order()

# Map joint name -> SLMB index
_JOINT_NAME_TO_SLMB_IDX = {name: idx for idx, (name, _) in enumerate(JOINT_ORDER)}


def _is_leaf(joint_name: str) -> bool:
    """Check if joint is a leaf (no children in hierarchy)."""
    return joint_name not in SKELETON_HIERARCHY or len(SKELETON_HIERARCHY[joint_name]) == 0


def _write_hierarchy(f: TextIO, joint_name: str, indent: int, is_root: bool = False):
    """Write HIERARCHY section recursively."""
    prefix = "  " * indent
    offset = REFPOSE_FROM_PARENT.get(joint_name, (0, 0, 0))
    # BVH offsets are in centimeters (the sample file uses cm-scale values)
    # The ABNT spec uses meters, but the provided BVH sample has values ~100x larger
    # We'll use the ABNT meter values scaled to cm for consistency with the sample BVH
    ox, oy, oz = offset[0] * 100, offset[1] * 100, offset[2] * 100

    if is_root:
        f.write(f"{prefix}ROOT {joint_name}\n")
    else:
        f.write(f"{prefix}JOINT {joint_name}\n")

    f.write(f"{prefix}{{\n")
    f.write(f"{prefix}  OFFSET {ox:.6f} {oy:.6f} {oz:.6f}\n")
    f.write(f"{prefix}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")

    children = SKELETON_HIERARCHY.get(joint_name, [])
    if not children:
        # Leaf joint - write End Site
        end_offset = REFPOSE_END.get(joint_name, (0, 0, 0))
        ex, ey, ez = end_offset[0] * 100, end_offset[1] * 100, end_offset[2] * 100
        f.write(f"{prefix}  End Site\n")
        f.write(f"{prefix}  {{\n")
        f.write(f"{prefix}    OFFSET {ex:.6f} {ey:.6f} {ez:.6f}\n")
        f.write(f"{prefix}  }}\n")
    else:
        for child in children:
            _write_hierarchy(f, child, indent + 1)

    f.write(f"{prefix}}}\n")


def slmb_to_bvh(slmb_data: SLMBData, output_path: str):
    """
    Convert decoded SLMB data to BVH file.
    Implements OG-06 D.2.4.4 SLMB -> BVH conversion.
    """
    bmb = slmb_data.body

    with open(output_path, 'w') as f:
        # ─── HIERARCHY Section ───
        f.write("HIERARCHY\n")
        _write_hierarchy(f, "hips_JNT", 0, is_root=True)

        # ─── MOTION Section ───
        f.write("MOTION\n")
        f.write(f"Frames: {bmb.num_frames}\n")
        f.write(f"Frame Time: {bmb.frame_time:.6f}\n")

        for frame_idx in range(bmb.num_frames):
            values = []

            for joint_name in BVH_JOINT_ORDER:
                slmb_idx = _JOINT_NAME_TO_SLMB_IDX.get(joint_name)
                if slmb_idx is None:
                    # Joint not in SLMB, write defaults
                    offset = REFPOSE_FROM_PARENT.get(joint_name, (0, 0, 0))
                    values.extend([offset[0] * 100, offset[1] * 100, offset[2] * 100,
                                   0.0, 0.0, 0.0])
                    continue

                joint_type = JOINT_ORDER[slmb_idx][1]
                jfd = bmb.joint_data[slmb_idx][frame_idx]

                # Position
                if joint_type == 0:
                    # Type-0: decoded translation
                    x_pos = jfd.tx
                    y_pos = jfd.ty
                    z_pos = jfd.tz
                else:
                    # Non-root: reference pose position (in meters, but BVH uses the offset)
                    offset = REFPOSE_FROM_PARENT.get(joint_name, (0, 0, 0))
                    x_pos = offset[0] * 100
                    y_pos = offset[1] * 100
                    z_pos = offset[2] * 100

                # Rotation
                if joint_type == 0 or joint_type == 1:
                    # Type-0/1: quaternion -> y/x/z euler
                    x_rot, y_rot, z_rot = quaternion2euler_yxz(
                        jfd.qw, jfd.qx, jfd.qy, jfd.qz,
                        (1, 0, 0), (0, 1, 0), (0, 0, 1))

                elif joint_type == 2:
                    # Type-2: euler (custom axes) -> Q_enc -> Q = Q_enc * inv(Qr) -> BVH euler
                    rx, ry, rz = get_rotation_axes(joint_name)
                    qw, qx, qy, qz = euler2quaternion_xyz(
                        jfd.euler_x, jfd.euler_y, jfd.euler_z, rx, ry, rz)
                    # Undo Qr: encoder did Q_enc = Q_bvh * Qr, so Q_bvh = Q_enc * inv(Qr)
                    qr = rotationaxis_to_quaternion(rx, ry, rz)
                    qr_inv = quaternion_inverse(qr)
                    q_bvh = quaternion_multiply((qw, qx, qy, qz), qr_inv)
                    x_rot, y_rot, z_rot = quaternion2euler_yxz(
                        q_bvh[0], q_bvh[1], q_bvh[2], q_bvh[3],
                        (1, 0, 0), (0, 1, 0), (0, 0, 1))

                elif joint_type == 3:
                    # Type-3: z-axis only -> Q_enc -> Q = Q_enc * inv(Qr) -> BVH euler
                    rx, ry, rz = get_rotation_axes(joint_name)
                    qw, qx, qy, qz = euler2quaternion_xyz(
                        0, 0, jfd.euler_z, rx, ry, rz)
                    qr = rotationaxis_to_quaternion(rx, ry, rz)
                    qr_inv = quaternion_inverse(qr)
                    q_bvh = quaternion_multiply((qw, qx, qy, qz), qr_inv)
                    x_rot, y_rot, z_rot = quaternion2euler_yxz(
                        q_bvh[0], q_bvh[1], q_bvh[2], q_bvh[3],
                        (1, 0, 0), (0, 1, 0), (0, 0, 1))

                elif joint_type == 4:
                    # Type-4: direct x/y euler
                    x_rot = jfd.euler_x
                    y_rot = jfd.euler_y
                    z_rot = 0.0

                # BVH channel order: Xposition Yposition Zposition Zrotation Xrotation Yrotation
                values.extend([x_pos, y_pos, z_pos, z_rot, x_rot, y_rot])

            f.write(" ".join(f"{v:.6f}" for v in values) + "\n")
