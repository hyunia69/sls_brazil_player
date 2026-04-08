"""Batch conversion of VLibras AssetBundles to SLMB format.

Provides parallel batch processing using a thread pool for concurrent
conversion of multiple gloss animations.
"""

from __future__ import annotations

import concurrent.futures
import os
from pathlib import Path
from typing import Any


def convert_one(gloss_path: str | Path) -> tuple[str, bool, str | None]:
    """Convert a single VLibras AssetBundle or JSON file to SLMB.

    Args:
        gloss_path: Path to the input file (AssetBundle or JSON).

    Returns:
        Tuple of (name, success, error_message).
        On success, error_message is None.
    """
    from ..parsing.asset_bundle import load_asset_bundle
    from ..parsing.animation_clip import AnimationClipData
    from ..retarget.body_retarget import retarget_body
    from ..retarget.face_retarget import retarget_face
    from ..encoding.body_encoder import encode_body_motion
    from ..encoding.face_encoder import encode_face_motion
    from ..encoding.motion_bundle import build_motion_bundle
    from ..encoding.slmb_writer import write_slmb

    gloss_path = Path(gloss_path)

    try:
        if gloss_path.suffix == ".json":
            clip = AnimationClipData.from_json(str(gloss_path))
        else:
            clip = load_asset_bundle(str(gloss_path))

        body = retarget_body(clip)
        face = retarget_face(clip)
        body_block = encode_body_motion(body)
        face_block = encode_face_motion(face)
        bundle = build_motion_bundle(body_block, face_block)

        out = gloss_path.with_suffix(".slmb.xz")
        write_slmb(bundle, str(out))

        return clip.name, True, None
    except Exception as e:
        return gloss_path.stem, False, str(e)


def batch_convert(
    gloss_paths: list[str | Path],
    output_dir: str | Path,
    workers: int = 4,
) -> list[tuple[str, bool, str | None]]:
    """Batch convert multiple gloss files to SLMB format.

    Uses a thread pool for parallel conversion.  Each file is
    independently loaded, retargeted, encoded, and written.

    Args:
        gloss_paths: List of paths to input files.
        output_dir: Directory for output .slmb.xz files.
        workers: Maximum number of parallel conversion threads.

    Returns:
        List of (name, success, error_message) tuples, one per input.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, bool, str | None]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(convert_one, p): p for p in gloss_paths
        }

        for future in concurrent.futures.as_completed(future_map):
            name, success, error = future.result()
            results.append((name, success, error))

            status = "OK" if success else f"FAIL: {error}"
            print(f"  {name}: {status}")

    return results
