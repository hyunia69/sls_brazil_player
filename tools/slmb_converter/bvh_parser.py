"""BVH (BioVision Hierarchy) file parser.

Parses BVH motion capture files into structured data objects.
BVH files consist of two sections:
  - HIERARCHY: skeleton tree with joint offsets and channel definitions
  - MOTION: per-frame channel values for all joints

Handles the known "OFFFET" typo found in some sample files.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class BVHJoint:
    """A single joint in the BVH skeleton hierarchy.

    Attributes:
        name: Joint name (e.g. "hips_JNT").
        offset: (x, y, z) offset from parent joint.
        channels: Channel names in declaration order,
            e.g. ["Xposition", "Yposition", "Zposition",
                   "Zrotation", "Xrotation", "Yrotation"].
        children: Child joints.
        end_site: End Site offset for leaf joints, or None.
    """

    name: str
    offset: Tuple[float, float, float]
    channels: List[str]
    children: List["BVHJoint"] = field(default_factory=list)
    end_site: Optional[Tuple[float, float, float]] = None


@dataclass
class BVHData:
    """Parsed BVH file data.

    Attributes:
        root: Root joint of the skeleton hierarchy.
        num_frames: Number of motion frames.
        frame_time: Duration of each frame in seconds.
        motion_data: motion_data[frame_idx][channel_flat_idx] gives
            the float value for that channel at that frame. Channels
            are ordered by depth-first joint traversal order.
        joint_list: Flattened list of all joints in declaration
            (depth-first) order.
    """

    root: BVHJoint
    num_frames: int
    frame_time: float
    motion_data: List[List[float]]
    joint_list: List[BVHJoint]


def parse_bvh(filepath: str) -> BVHData:
    """Parse a BVH file and return structured data.

    Args:
        filepath: Path to the BVH file. Both forward slashes and
            backslashes are accepted.

    Returns:
        BVHData with the parsed skeleton and motion data.

    Raises:
        ValueError: If the file format is invalid or unexpected
            tokens are encountered.
        FileNotFoundError: If the file does not exist.
    """
    # Normalize path separators
    filepath = filepath.replace("\\", "/")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    tokens: List[str] = []
    for line in lines:
        tokens.extend(line.strip().split())

    pos = 0

    def peek() -> str:
        return tokens[pos]

    def consume() -> str:
        nonlocal pos
        token = tokens[pos]
        pos += 1
        return token

    def expect(expected: str) -> None:
        token = consume()
        if token != expected:
            raise ValueError(
                f"Expected '{expected}', got '{token}' at token index {pos - 1}"
            )

    def parse_joint(is_root: bool = False) -> BVHJoint:
        """Parse a JOINT (or ROOT) block from the token stream."""
        if is_root:
            expect("ROOT")
        else:
            expect("JOINT")

        name = consume()
        expect("{")

        # OFFSET (handle "OFFFET" typo)
        offset_token = consume()
        if offset_token not in ("OFFSET", "OFFFET"):
            raise ValueError(
                f"Expected 'OFFSET' or 'OFFFET', got '{offset_token}'"
            )
        ox = float(consume())
        oy = float(consume())
        oz = float(consume())
        offset = (ox, oy, oz)

        # CHANNELS
        expect("CHANNELS")
        num_channels = int(consume())
        channels = [consume() for _ in range(num_channels)]

        joint = BVHJoint(name=name, offset=offset, channels=channels)

        # Parse children and End Site
        while peek() != "}":
            if peek() == "JOINT":
                joint.children.append(parse_joint(is_root=False))
            elif peek() == "End":
                # End Site block
                consume()  # "End"
                expect("Site")
                expect("{")
                end_offset_token = consume()
                if end_offset_token not in ("OFFSET", "OFFFET"):
                    raise ValueError(
                        f"Expected 'OFFSET' or 'OFFFET' in End Site, "
                        f"got '{end_offset_token}'"
                    )
                ex = float(consume())
                ey = float(consume())
                ez = float(consume())
                joint.end_site = (ex, ey, ez)
                expect("}")
            else:
                raise ValueError(
                    f"Unexpected token '{peek()}' inside joint '{name}'"
                )

        expect("}")  # closing brace of this joint
        return joint

    # Parse HIERARCHY section
    expect("HIERARCHY")
    root = parse_joint(is_root=True)

    # Build joint_list in depth-first declaration order
    joint_list: List[BVHJoint] = []

    def collect_joints(joint: BVHJoint) -> None:
        joint_list.append(joint)
        for child in joint.children:
            collect_joints(child)

    collect_joints(root)

    # Parse MOTION section
    expect("MOTION")

    expect("Frames:")
    num_frames = int(consume())

    expect("Frame")
    expect("Time:")
    frame_time = float(consume())

    # Total number of channels across all joints
    total_channels = sum(len(j.channels) for j in joint_list)

    motion_data: List[List[float]] = []
    for _ in range(num_frames):
        frame_values = [float(consume()) for _ in range(total_channels)]
        motion_data.append(frame_values)

    return BVHData(
        root=root,
        num_frames=num_frames,
        frame_time=frame_time,
        motion_data=motion_data,
        joint_list=joint_list,
    )


def get_joint_channels(bvh: BVHData, joint: BVHJoint, frame: int) -> dict:
    """Get channel values for a specific joint at a specific frame.

    Args:
        bvh: Parsed BVH data.
        joint: The joint to query (must be in bvh.joint_list).
        frame: Frame index (0-based).

    Returns:
        Dict mapping channel name to float value, e.g.
        {"Xposition": 0.0, "Yposition": 1.5, ...}.

    Raises:
        ValueError: If the joint is not found in the BVH data.
        IndexError: If the frame index is out of range.
    """
    if frame < 0 or frame >= bvh.num_frames:
        raise IndexError(
            f"Frame {frame} out of range [0, {bvh.num_frames - 1}]"
        )

    # Compute the starting channel index for the given joint by summing
    # channel counts of all preceding joints in declaration order.
    channel_offset = 0
    found = False
    for j in bvh.joint_list:
        if j is joint:
            found = True
            break
        channel_offset += len(j.channels)

    if not found:
        raise ValueError(f"Joint '{joint.name}' not found in BVH joint list")

    values = bvh.motion_data[frame]
    return {
        ch: values[channel_offset + i]
        for i, ch in enumerate(joint.channels)
    }


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        # Default to the sample file relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sample = os.path.join(script_dir, "..", "avatarModel.bvh")
        if not os.path.exists(sample):
            print("Usage: python bvh_parser.py <path_to_bvh_file>")
            sys.exit(1)
        path = sample
    else:
        path = sys.argv[1]

    bvh = parse_bvh(path)
    print(f"Root joint: {bvh.root.name}")
    print(f"Total joints: {len(bvh.joint_list)}")
    print(f"Frames: {bvh.num_frames}")
    print(f"Frame time: {bvh.frame_time}s ({1.0 / bvh.frame_time:.1f} fps)")
    print()
    print("Joint list (declaration order):")
    for i, j in enumerate(bvh.joint_list):
        leaf = " [leaf]" if j.end_site is not None else ""
        print(f"  {i:3d}: {j.name} ({len(j.channels)} ch){leaf}")

    print()
    print(f"Frame 0 root channels:")
    root_ch = get_joint_channels(bvh, bvh.root, 0)
    for ch_name, val in root_ch.items():
        print(f"  {ch_name}: {val}")
