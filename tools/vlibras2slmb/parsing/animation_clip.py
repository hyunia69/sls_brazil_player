"""VLibras AnimationClip JSON loader.

Parses the JSON format exported from VLibras Unity AssetBundle files
(e.g. ``CASA_full.json``).  Handles the conversion from Unity quaternion
order ``[x, y, z, w]`` to the internal ``[w, x, y, z]`` convention used
throughout the pipeline.

The JSON structure contains:
- ``rotation_curves``: per-bone quaternion keyframes (Unity xyzw order)
- ``position_curves``: per-bone position keyframes (xyz)
- ``float_curves``: per-mesh blendshape weight keyframes
- ``scale_curves``: per-bone scale keyframes (ignored)
- ``bone_paths``: complete skeleton hierarchy paths
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Keyframe:
    """A single animation keyframe with a timestamp and value.

    Attributes:
        time: Timestamp in seconds.
        value: Numpy array holding the keyframe value.
            - Quaternion rotation: ``[w, x, y, z]`` (4 elements)
            - Position: ``[x, y, z]`` (3 elements)
            - Blendshape weight: ``[weight]`` (1 element, scalar)
    """

    time: float
    value: np.ndarray


@dataclass
class AnimationCurve:
    """A sequence of keyframes for a single bone or blendshape attribute.

    Attributes:
        path: Full bone path (e.g. ``"Armature.001/BnBacia.001/BnCol-01"``)
              or mesh path for float curves.
        keyframes: Chronologically ordered list of :class:`Keyframe` instances.
    """

    path: str
    keyframes: List[Keyframe] = field(default_factory=list)


@dataclass
class AnimationClipData:
    """Parsed VLibras animation clip ready for retargeting.

    Rotation quaternions are stored in ``[w, x, y, z]`` convention
    (converted from Unity's ``[x, y, z, w]`` during parsing).

    Attributes:
        name: Animation clip name (e.g. ``"CASA"``).
        sample_rate: Frames per second from the source file.
        duration: Calculated from the maximum keyframe timestamp across
            all curves.
        bone_paths: Complete list of bone path strings from the source.
        rotation_curves: Mapping from full bone path to its rotation
            :class:`AnimationCurve`.  Quaternions are in ``[w, x, y, z]``.
        position_curves: Mapping from full bone path to its position
            :class:`AnimationCurve`.
        float_curves: Mapping from blendshape name (e.g. ``"Sorriso"``)
            to its weight :class:`AnimationCurve`.
    """

    name: str
    sample_rate: float
    duration: float
    bone_paths: List[str]
    rotation_curves: Dict[str, AnimationCurve]
    position_curves: Dict[str, AnimationCurve]
    float_curves: Dict[str, AnimationCurve]

    @staticmethod
    def get_leaf_name(path: str) -> str:
        """Extract the leaf bone name from a hierarchical path.

        Args:
            path: Slash-separated bone path.

        Returns:
            The rightmost component of the path.

        Examples:
            >>> AnimationClipData.get_leaf_name("Armature.001/BnBacia.001/BnCol-01")
            'BnCol-01'
            >>> AnimationClipData.get_leaf_name("Armature.001")
            'Armature.001'
        """
        return path.rsplit("/", maxsplit=1)[-1] if "/" in path else path

    @classmethod
    def from_json(cls, json_path: Union[str, Path]) -> AnimationClipData:
        """Load an animation clip from a VLibras-exported JSON file.

        Performs the following conversions during parsing:

        - **Quaternion reorder**: Unity stores quaternions as
          ``[x, y, z, w]``.  This method converts them to
          ``[w, x, y, z]`` for internal use.
        - **Blendshape name extraction**: The ``attribute`` field in
          float curves uses the format ``"blendShape.Sorriso"``.
          The prefix is stripped to yield ``"Sorriso"``.
        - **Duration calculation**: Scanned from the maximum keyframe
          timestamp across rotation, position, and float curves.
        - **Empty curve handling**: Float curves that lack keyframe
          data are logged and skipped.

        Args:
            json_path: Path to the JSON file (e.g. ``CASA_full.json``).

        Returns:
            A fully populated :class:`AnimationClipData` instance.

        Raises:
            FileNotFoundError: If *json_path* does not exist.
            KeyError: If required top-level keys are missing.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        json_path = Path(json_path)
        with json_path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)

        name: str = raw["name"]
        sample_rate: float = float(raw["sample_rate"])
        bone_paths: List[str] = list(raw.get("bone_paths", []))

        rotation_curves: Dict[str, AnimationCurve] = {}
        position_curves: Dict[str, AnimationCurve] = {}
        float_curves: Dict[str, AnimationCurve] = {}

        max_time: float = 0.0

        # -- Parse rotation curves (Unity [x,y,z,w] -> internal [w,x,y,z]) --
        for entry in raw.get("rotation_curves", []):
            path = entry["path"]
            kf_count = entry.get("keyframe_count", 0)
            raw_keyframes = entry.get("keyframes", [])

            if not raw_keyframes:
                logger.debug(
                    "Rotation curve '%s' has no keyframes (count=%d), skipping",
                    path,
                    kf_count,
                )
                continue

            keyframes: List[Keyframe] = []
            for kf in raw_keyframes:
                t = float(kf["time"])
                vals = kf["value"]
                # Unity quaternion order: [x, y, z, w] -> [w, x, y, z]
                x, y, z, w = vals[0], vals[1], vals[2], vals[3]
                q = np.array([w, x, y, z], dtype=np.float64)
                keyframes.append(Keyframe(time=t, value=q))
                if t > max_time:
                    max_time = t

            rotation_curves[path] = AnimationCurve(
                path=path, keyframes=keyframes
            )

        # -- Parse position curves --
        for entry in raw.get("position_curves", []):
            path = entry["path"]
            raw_keyframes = entry.get("keyframes", [])

            if not raw_keyframes:
                continue

            keyframes = []
            for kf in raw_keyframes:
                t = float(kf["time"])
                vals = kf["value"]
                pos = np.array(
                    [float(vals[0]), float(vals[1]), float(vals[2])],
                    dtype=np.float64,
                )
                keyframes.append(Keyframe(time=t, value=pos))
                if t > max_time:
                    max_time = t

            position_curves[path] = AnimationCurve(
                path=path, keyframes=keyframes
            )

        # -- Parse float curves (blendshape weights) --
        for entry in raw.get("float_curves", []):
            attribute: str = entry.get("attribute", "")
            raw_keyframes = entry.get("keyframes", [])

            # Extract blendshape name: "blendShape.Sorriso" -> "Sorriso"
            if "." in attribute:
                bs_name = attribute.rsplit(".", maxsplit=1)[-1]
            else:
                bs_name = attribute

            if not bs_name:
                logger.warning(
                    "Float curve with empty attribute, skipping: %s", entry
                )
                continue

            if not raw_keyframes:
                logger.debug(
                    "Float curve '%s' has no keyframes, registering empty curve",
                    bs_name,
                )
                # Register the blendshape name with an empty curve so the
                # face retargeter knows this shape exists in the clip even
                # if it carries no animation data.
                float_curves[bs_name] = AnimationCurve(
                    path=entry.get("path", ""), keyframes=[]
                )
                continue

            keyframes = []
            for kf in raw_keyframes:
                t = float(kf["time"])
                vals = kf["value"]
                # Weight is a scalar, but may arrive as a list of length 1
                # or as a plain float.
                if isinstance(vals, (list, tuple)):
                    weight = float(vals[0])
                else:
                    weight = float(vals)
                keyframes.append(
                    Keyframe(time=t, value=np.array([weight], dtype=np.float64))
                )
                if t > max_time:
                    max_time = t

            float_curves[bs_name] = AnimationCurve(
                path=entry.get("path", ""), keyframes=keyframes
            )

        duration = max_time

        clip = cls(
            name=name,
            sample_rate=sample_rate,
            duration=duration,
            bone_paths=bone_paths,
            rotation_curves=rotation_curves,
            position_curves=position_curves,
            float_curves=float_curves,
        )

        logger.info(
            "Loaded clip '%s': %.1f fps, %.3f s duration, "
            "%d rotation curves, %d position curves, %d float curves",
            clip.name,
            clip.sample_rate,
            clip.duration,
            len(clip.rotation_curves),
            len(clip.position_curves),
            len(clip.float_curves),
        )

        return clip

    def get_rotation_curve_by_leaf(
        self, leaf_name: str
    ) -> Optional[AnimationCurve]:
        """Look up a rotation curve by its leaf bone name.

        Iterates over all rotation curves and returns the first whose
        path ends with *leaf_name*.

        Args:
            leaf_name: Leaf bone name (e.g. ``"BnCol-02"``).

        Returns:
            The matching :class:`AnimationCurve`, or ``None`` if no
            curve matches.
        """
        for path, curve in self.rotation_curves.items():
            if self.get_leaf_name(path) == leaf_name:
                return curve
        return None

    def get_position_curve_by_leaf(
        self, leaf_name: str
    ) -> Optional[AnimationCurve]:
        """Look up a position curve by its leaf bone name.

        Args:
            leaf_name: Leaf bone name (e.g. ``"BnBacia.001"``).

        Returns:
            The matching :class:`AnimationCurve`, or ``None``.
        """
        for path, curve in self.position_curves.items():
            if self.get_leaf_name(path) == leaf_name:
                return curve
        return None

    def build_leaf_index(self) -> Dict[str, str]:
        """Build a reverse lookup from leaf bone name to full path.

        Scans ``bone_paths`` and creates a dictionary mapping each
        leaf name to its full path.  If multiple paths share the same
        leaf name, the last occurrence wins (with a warning logged).

        Returns:
            Dictionary mapping leaf bone name to full bone path.
        """
        index: Dict[str, str] = {}
        for path in self.bone_paths:
            leaf = self.get_leaf_name(path)
            if leaf in index:
                logger.warning(
                    "Duplicate leaf name '%s': '%s' overwrites '%s'",
                    leaf,
                    path,
                    index[leaf],
                )
            index[leaf] = path
        return index
