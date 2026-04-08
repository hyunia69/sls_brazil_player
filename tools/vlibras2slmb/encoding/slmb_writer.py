"""SLMB file I/O with LZMA/xz compression.

SLMB files use the ``.slmb.xz`` extension and contain a MotionBundle
compressed with LZMA in xz container format (RFC 7932).
"""

from __future__ import annotations

import lzma
from pathlib import Path


def write_slmb(motion_bundle: bytes, output_path: str | Path) -> None:
    """Compress a MotionBundle with LZMA/xz and write to disk.

    Args:
        motion_bundle: Raw MotionBundle bytes from build_motion_bundle().
        output_path: Destination file path (should end in .slmb.xz).

    Raises:
        OSError: If the file cannot be written.
    """
    compressed = lzma.compress(motion_bundle, format=lzma.FORMAT_XZ)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(compressed)


def read_slmb(input_path: str | Path) -> bytes:
    """Read and decompress a .slmb.xz file.

    Args:
        input_path: Path to the .slmb.xz file.

    Returns:
        Raw MotionBundle bytes (decompressed).

    Raises:
        FileNotFoundError: If the file does not exist.
        lzma.LZMAError: If the file is not valid xz data.
    """
    input_path = Path(input_path)
    compressed = input_path.read_bytes()
    return lzma.decompress(compressed, format=lzma.FORMAT_XZ)
