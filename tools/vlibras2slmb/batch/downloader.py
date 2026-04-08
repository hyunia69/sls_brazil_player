"""VLibras AssetBundle downloader.

Downloads sign language animation bundles from the VLibras dictionary
server for batch processing.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

VLIBRAS_BASE_URL = "https://dicionario2.vlibras.gov.br/2018.3.1/WEBGL/"
VLIBRAS_BUNDLE_LIST_URL = "https://dicionario2.vlibras.gov.br/bundles"

# Default request timeout in seconds
_DEFAULT_TIMEOUT = 30


def download_gloss(
    gloss_name: str,
    output_dir: str | Path,
    timeout: int = _DEFAULT_TIMEOUT,
) -> str:
    """Download a VLibras AssetBundle for a given gloss.

    The file is saved to ``output_dir/gloss_name`` with no extension
    (matching VLibras server convention).

    Args:
        gloss_name: Gloss identifier (e.g. "CASA", "ESCOLA").
        output_dir: Directory to save the downloaded bundle.
        timeout: HTTP request timeout in seconds.

    Returns:
        Absolute path to the downloaded file.

    Raises:
        requests.HTTPError: If the server returns a non-2xx status.
        requests.ConnectionError: If the server is unreachable.
    """
    url = VLIBRAS_BASE_URL + gloss_name
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / gloss_name

    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    output_path.write_bytes(resp.content)
    return str(output_path.resolve())


def fetch_gloss_list(timeout: int = _DEFAULT_TIMEOUT) -> list[str]:
    """Fetch the complete gloss list from the VLibras dictionary server.

    Args:
        timeout: HTTP request timeout in seconds.

    Returns:
        List of gloss name strings.

    Raises:
        requests.HTTPError: If the server returns a non-2xx status.
    """
    resp = requests.get(VLIBRAS_BUNDLE_LIST_URL, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def load_gloss_list_file(path: str | Path) -> list[str]:
    """Load a gloss list from a local JSON file.

    The file should contain a JSON array of gloss name strings,
    matching the format of ``brazil_gloss_list.txt``.

    Args:
        path: Path to the JSON gloss list file.

    Returns:
        List of gloss name strings.
    """
    import json

    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {path}, got {type(data).__name__}")

    return [str(g) for g in data]
