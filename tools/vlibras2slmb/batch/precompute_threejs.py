"""VLibras AssetBundle -> Three.js JSON batch precompute pipeline.

Reads a gloss list, downloads Unity AssetBundles from the VLibras
dictionary CDN, parses them, and writes browser-ready JSON files
compatible with ``public/players/vlibras-v3/index.html``.

The emitted schema (one JSON per gloss) mirrors
``public/animations/vlibras/CASA_threejs.json``::

    {
        "name": "CASA",
        "duration": 2.5,
        "sample_rate": 30,
        "tracks": [
            {"name": "BnMaoOrientR.position",  "type": "vector",     "times": [...], "values": [...]},
            {"name": "BnMaoOrientR.quaternion","type": "quaternion", "times": [...], "values": [...]},
            ...
        ]
    }

Quaternion values are emitted in Three.js order ``[x, y, z, w]``.  Bone
leaf names have dots stripped (``BnBacia.001`` -> ``BnBacia001``), matching
the transform used by the existing reference file.

**Two output modes**:

``--raw`` (default prior to Playwright validation): emit Unity-source
rotations and positions verbatim with only axis/name remapping.  Renders
incorrectly on the Blender-exported GLB avatars because their bind pose
differs from the Unity authoring rig.

``--match-legacy`` (default, enabled after validation): retarget each
rotation into the Icaro GLB bind-pose frame and replace position tracks
with constant Icaro bind-pose positions.  Produces JSON that drops into
the existing vlibras-v3 player without further changes.

Usage::

    python -m tools.vlibras2slmb.batch.precompute_threejs \\
        --gloss-list tools/vlibras2slmb/data/spike_glosses.txt \\
        --output-dir public/animations/vlibras/bundles

Notes on dependencies:
    - Re-uses :func:`vlibras2slmb.batch.downloader.download_gloss` for HTTP.
    - Does **not** re-use :func:`vlibras2slmb.parsing.asset_bundle.load_asset_bundle`
      because the shipped implementation uses upper-case attribute access
      (``kf.value.X``) that breaks with UnityPy >= 1.25 (lower-case API).
      Since M1 forbids editing existing parser files, this module ships
      its own minimal AssetBundle reader that matches the lower-case API.
    - Retarget math uses :data:`vlibras2slmb.data.vlibras_bind_pose.VLIBRAS_BIND_POSE`
      (Unity skeleton bind pose, stored as ``(w, x, y, z)``) and
      ``tools/vlibras2slmb/data/icaro_bind_pose.json`` (GLB bind pose
      captured via Playwright from ``public/avatars/vlibras/icaro/export/icaro.glb``).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Absolute import so the file can be executed as a module
# (``python -m tools.vlibras2slmb.batch.precompute_threejs``) regardless
# of the caller's working directory.  We also repair ``sys.path`` at
# runtime because the ``tools/`` directory is not a package on its own.
_HERE = Path(__file__).resolve()
_TOOLS_DIR = _HERE.parents[2]  # .../sls_brazil_player/tools
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from vlibras2slmb.batch.downloader import download_gloss  # noqa: E402

logger = logging.getLogger("precompute_threejs")


# ---------------------------------------------------------------------------
# Minimal clip container (intentionally decoupled from AnimationClipData
# in parsing/animation_clip.py because that class stores quaternions in
# ``[w, x, y, z]`` while Three.js needs ``[x, y, z, w]``).
# ---------------------------------------------------------------------------


@dataclass
class _RawCurve:
    """A single Unity animation curve with time/value lists."""

    path: str
    attribute: str = ""  # only meaningful for float curves
    times: list[float] = field(default_factory=list)
    values: list[list[float]] = field(default_factory=list)


@dataclass
class _RawClip:
    """Flat view of a Unity AnimationClip suitable for serialisation."""

    name: str
    sample_rate: float
    duration: float
    rotation_curves: list[_RawCurve] = field(default_factory=list)
    position_curves: list[_RawCurve] = field(default_factory=list)
    scale_curves: list[_RawCurve] = field(default_factory=list)
    float_curves: list[_RawCurve] = field(default_factory=list)


def _read_unity_clip(path: Path) -> _RawClip:
    """Parse a VLibras AssetBundle using UnityPy.

    This is a tight, self-contained implementation that mirrors
    ``tools/extract_casa.py`` but returns a typed container instead of
    emitting JSON.  Uses lower-case attribute access compatible with
    UnityPy 1.25+ to side-step the broken uppercase accessors in
    ``asset_bundle.py``.

    Args:
        path: Filesystem path to the Unity AssetBundle.

    Returns:
        Populated :class:`_RawClip` instance.

    Raises:
        ImportError: If UnityPy is not installed.
        ValueError: If the bundle contains no AnimationClip.
    """
    try:
        import UnityPy  # noqa: WPS433 (runtime import is intentional)
    except ImportError as exc:
        raise ImportError(
            "UnityPy is required. Install: pip install UnityPy"
        ) from exc

    env = UnityPy.load(str(path))
    unity_clip = None
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            unity_clip = obj.read()
            break

    if unity_clip is None:
        raise ValueError(f"No AnimationClip found in {path}")

    raw = _RawClip(
        name=str(unity_clip.m_Name),
        sample_rate=float(unity_clip.m_SampleRate),
        duration=0.0,
    )

    max_time = 0.0

    for rc in unity_clip.m_RotationCurves:
        curve = _RawCurve(path=str(rc.path))
        for kf in rc.curve.m_Curve:
            t = float(kf.time)
            # Unity quaternion: keep in (x, y, z, w) which is what
            # Three.js also expects.  No reordering needed here.
            curve.times.append(t)
            curve.values.append(
                [float(kf.value.x), float(kf.value.y),
                 float(kf.value.z), float(kf.value.w)]
            )
            if t > max_time:
                max_time = t
        raw.rotation_curves.append(curve)

    for pc in unity_clip.m_PositionCurves:
        curve = _RawCurve(path=str(pc.path))
        for kf in pc.curve.m_Curve:
            t = float(kf.time)
            curve.times.append(t)
            curve.values.append(
                [float(kf.value.x), float(kf.value.y), float(kf.value.z)]
            )
            if t > max_time:
                max_time = t
        raw.position_curves.append(curve)

    if hasattr(unity_clip, "m_ScaleCurves"):
        for sc in unity_clip.m_ScaleCurves:
            curve = _RawCurve(path=str(sc.path))
            for kf in sc.curve.m_Curve:
                t = float(kf.time)
                curve.times.append(t)
                curve.values.append(
                    [float(kf.value.x), float(kf.value.y), float(kf.value.z)]
                )
                if t > max_time:
                    max_time = t
            raw.scale_curves.append(curve)

    for fc in unity_clip.m_FloatCurves:
        curve = _RawCurve(path=str(fc.path), attribute=str(fc.attribute))
        for kf in fc.curve.m_Curve:
            t = float(kf.time)
            curve.times.append(t)
            curve.values.append([float(kf.value)])
            if t > max_time:
                max_time = t
        raw.float_curves.append(curve)

    raw.duration = max_time
    return raw


# ---------------------------------------------------------------------------
# Serialisation to Three.js JSON
# ---------------------------------------------------------------------------


# Bones whose full Unity path is entirely dropped from the emitted
# tracks.  Matches the existing CASA_threejs.json reference file, which
# filters the Armature root (it only carries a constant pre-bake rotation
# that is baked into the GLB itself and must not re-apply at runtime).
_BONE_BLACKLIST = {"Armature.001", "Armature"}


# Bones whose Unity animation curve does NOT match the yz-sign-flip
# convention used by the rest of the body skeleton.  For these bones
# the reference pipeline replaces the animation with a static
# 2-keyframe track at the Icaro/padrao_tex GLB bind-pose rotation.
#
# Discovered empirically by comparing every bone in
# ``public/animations/vlibras/CASA_threejs.json`` against
# ``(x, -y, -z, w)`` of the raw Unity keyframe values.  The list covers
# the root pelvis bone (whose GLB rotation bakes in Unity→Blender up-
# axis conversion) and the IK helper bones that live outside the skinned
# hierarchy in Unity:
#
#   BnBacia001    - root pelvis (Y-up → Z-up bake)
#   BnMaoOrient*  - hand-orient IK helpers
#   BnPolyV*      - pole vector targets
#   ik_FK*        - IK switch targets
_LEGACY_STATIC_OVERRIDE: frozenset[str] = frozenset({
    "BnBacia001",
    "BnMaoOrientR",
    "BnMaoOrientL",
    "BnPolyVR",
    "BnPolyVL",
    "ik_FKR",
    "ik_FKL",
})


def ascii_key(gloss: str) -> str:
    """Normalise a gloss identifier to its ASCII upper-case form.

    Used for on-disk filenames and for the ``key`` field of ``index.json``
    so that (a) Vercel/static servers never see non-ASCII path segments
    and (b) clients can look up glosses with a single deterministic
    transform (NFKD + combining-mark strip + upper).

    Examples:
        >>> ascii_key("CASA")
        'CASA'
        >>> ascii_key("ÁGUA")
        'AGUA'
        >>> ascii_key("VOCÊ")
        'VOCE'
        >>> ascii_key("POR_FAVOR")
        'POR_FAVOR'
    """
    nfkd = unicodedata.normalize("NFKD", gloss)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return stripped.upper()


# ---------------------------------------------------------------------------
# Bind-pose loader for legacy retargeting
# ---------------------------------------------------------------------------


def _load_icaro_bind_pose() -> dict[str, dict[str, list[float]]]:
    """Load the GLB bind-pose table captured from Icaro.

    Returns a mapping ``bone_leaf_name -> {'position': [x, y, z],
    'quaternion': [x, y, z, w]}``.  The JSON file was produced by a
    Playwright probe against ``/avatars/vlibras/icaro/export/icaro.glb``
    and is committed alongside the script for reproducibility.  The
    padrao_tex and casa_tex GLBs share the same bind pose for the
    bones used by this pipeline (verified via Playwright diff).
    """
    path = _TOOLS_DIR / "vlibras2slmb" / "data" / "icaro_bind_pose.json"
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data["bones"]


def _leaf_name(bone_path: str) -> str:
    """Convert a Unity bone path to the Three.js leaf name.

    Rules (derived from inspecting ``CASA_threejs.json``):
        - Keep only the component after the last ``/``.
        - Remove literal ``.`` characters.  Example: ``BnBacia.001`` ->
          ``BnBacia001``, ``ik_FK.L`` -> ``ik_FKL``.
        - Other delimiters (``-``, ``_``) are preserved.
    """
    leaf = bone_path.rsplit("/", 1)[-1] if "/" in bone_path else bone_path
    return leaf.replace(".", "")


def _mesh_leaf_name(mesh_path: str) -> str:
    """Convert a float-curve mesh path to the Three.js object name.

    Same rule as :func:`_leaf_name`.  Example: ``cabecaModifAlisson`` ->
    ``cabecaModifAlisson`` (unchanged).
    """
    return _leaf_name(mesh_path)


def _flatten(values: Iterable[list[float]]) -> list[float]:
    """Flatten a sequence of keyframe value vectors into one list."""
    out: list[float] = []
    for v in values:
        out.extend(v)
    return out


def clip_to_threejs_dict(
    clip: _RawClip,
    gloss_name: str,
    *,
    match_legacy: bool = True,
) -> dict:
    """Convert a :class:`_RawClip` into the Three.js JSON schema.

    Args:
        clip: Parsed Unity animation data.
        gloss_name: Gloss identifier used as the clip name in the
            output (overrides ``clip.name`` so downstream consumers
            can key by gloss rather than Unity clip label).
        match_legacy: When True (default), retarget rotations into the
            Icaro GLB bind-pose frame and replace position tracks with
            constant Icaro bind-pose positions.  The resulting JSON is
            drop-in compatible with ``vlibras-v3/index.html``.  When
            False, emit raw Unity values (useful only for debugging the
            upstream data; will not render correctly on the Blender GLB
            avatars).

    Returns:
        A dictionary with keys ``name``, ``duration``, ``sample_rate``,
        and ``tracks`` ready for :func:`json.dump`.
    """
    if match_legacy:
        return _clip_to_threejs_legacy(clip, gloss_name)
    return _clip_to_threejs_raw(clip, gloss_name)


def _clip_to_threejs_raw(clip: _RawClip, gloss_name: str) -> dict:
    """Pass-through conversion: emit Unity values with only leaf-name
    remapping and blacklist filtering.
    """
    tracks: list[dict] = []

    for curve in clip.rotation_curves:
        if curve.path in _BONE_BLACKLIST or not curve.times:
            continue
        tracks.append(
            {
                "name": f"{_leaf_name(curve.path)}.quaternion",
                "type": "quaternion",
                "times": list(curve.times),
                "values": _flatten(curve.values),
            }
        )

    for curve in clip.position_curves:
        if curve.path in _BONE_BLACKLIST or not curve.times:
            continue
        tracks.append(
            {
                "name": f"{_leaf_name(curve.path)}.position",
                "type": "vector",
                "times": list(curve.times),
                "values": _flatten(curve.values),
            }
        )

    for curve in clip.scale_curves:
        if curve.path in _BONE_BLACKLIST or not curve.times:
            continue
        tracks.append(
            {
                "name": f"{_leaf_name(curve.path)}.scale",
                "type": "vector",
                "times": list(curve.times),
                "values": _flatten(curve.values),
            }
        )

    for curve in clip.float_curves:
        if not curve.times:
            continue
        attr = curve.attribute or ""
        if attr.startswith("blendShape."):
            bs_name = attr[len("blendShape."):]
        else:
            bs_name = attr
        if not bs_name:
            continue
        mesh = _mesh_leaf_name(curve.path)
        scaled_values = [v[0] / 100.0 for v in curve.values]
        tracks.append(
            {
                "name": f"{mesh}.morphTargetInfluences[{bs_name}]",
                "type": "number",
                "times": list(curve.times),
                "values": scaled_values,
            }
        )

    return {
        "name": gloss_name,
        "duration": clip.duration,
        "sample_rate": clip.sample_rate,
        "tracks": tracks,
    }


def _clip_to_threejs_legacy(clip: _RawClip, gloss_name: str) -> dict:
    """Legacy-compatible conversion that renders correctly on the
    VLibras GLB avatars (padrao_tex / casa_tex / icaro).

    The reference file ``public/animations/vlibras/CASA_threejs.json``
    was produced by a three-step pipeline that we replicate here:

    1. **Axis convention fix** (``yz`` sign flip) on every rotation
       keyframe of every body bone::

           (x, y, z, w)  ->  (x, -y, -z, w)

       Empirically verified by comparing 14 animated body bones in
       the shipped CASA file against ``yz_flip(raw_unity_keyframe[0])``
       — arms, spine, neck, head, fingers all match exactly.

    2. **Static override for 7 helper bones** that lie outside the
       skin hierarchy in Unity and are baked into the GLB bind pose::

           BnBacia001, BnMaoOrientR, BnMaoOrientL,
           BnPolyVR, BnPolyVL, ik_FKR, ik_FKL

       For these bones the Unity animation curve does not match the
       yz-flip convention (typically because Unity stores them at
       identity while the GLB bakes in the ``Y-up -> Z-up`` 90° X
       rotation on the pelvis or pre-rotated IK targets).  We emit a
       2-keyframe constant track at the Icaro GLB bind-pose rotation
       for each of these, matching the reference file byte-for-byte
       within 1e-4 rounding.

    3. **Position tracks** are replaced with static 2-keyframe
       constants at the Icaro bind-pose local positions for every bone
       that has a rotation track.  VLibras position curves only carry
       bind-pose offsets anyway, and the reference file does the same.

    Scale tracks and blendshape morph tracks are omitted.
    """
    icaro_bind = _load_icaro_bind_pose()

    tracks: list[dict] = []
    emitted_rotation_leaves: list[str] = []
    yzflip_count = 0
    static_count = 0

    t_start = 1.0 / clip.sample_rate if clip.sample_rate else 0.0333333
    t_end = clip.duration if clip.duration > 0 else t_start

    # --- Rotation tracks ------------------------------------------------
    for curve in clip.rotation_curves:
        if curve.path in _BONE_BLACKLIST or not curve.times:
            continue
        leaf = _leaf_name(curve.path)
        icaro_entry = icaro_bind.get(leaf)

        if leaf in _LEGACY_STATIC_OVERRIDE and icaro_entry is not None:
            # Helper / pelvis bone: static override at GLB bind pose.
            q = icaro_entry["quaternion"]  # [x, y, z, w]
            tracks.append(
                {
                    "name": f"{leaf}.quaternion",
                    "type": "quaternion",
                    "times": [t_start, t_end],
                    "values": [q[0], q[1], q[2], q[3],
                               q[0], q[1], q[2], q[3]],
                }
            )
            static_count += 1
        else:
            # Body bone: yz sign flip per keyframe.
            flat: list[float] = []
            for qv in curve.values:  # qv = [x, y, z, w] raw Unity
                flat.extend((qv[0], -qv[1], -qv[2], qv[3]))
            tracks.append(
                {
                    "name": f"{leaf}.quaternion",
                    "type": "quaternion",
                    "times": list(curve.times),
                    "values": flat,
                }
            )
            yzflip_count += 1

        emitted_rotation_leaves.append(leaf)

    # --- Position tracks (static GLB bind pose) -------------------------
    for leaf in emitted_rotation_leaves:
        icaro_entry = icaro_bind.get(leaf)
        if icaro_entry is None:
            continue
        pos = icaro_entry["position"]  # [x, y, z]
        tracks.append(
            {
                "name": f"{leaf}.position",
                "type": "vector",
                "times": [t_start, t_end],
                "values": [pos[0], pos[1], pos[2],
                           pos[0], pos[1], pos[2]],
            }
        )

    logger.debug(
        "clip %s legacy retarget: yz_flip=%d, static_override=%d, "
        "total_rotation_tracks=%d",
        gloss_name, yzflip_count, static_count,
        len(emitted_rotation_leaves),
    )

    return {
        "name": gloss_name,
        "duration": clip.duration,
        "sample_rate": clip.sample_rate,
        "tracks": tracks,
    }


# ---------------------------------------------------------------------------
# Pipeline driver
# ---------------------------------------------------------------------------


def load_gloss_list(path: Path) -> list[str]:
    """Read a newline-delimited gloss list, ignoring comments.

    Lines starting with ``#`` and blank lines are skipped.  Whitespace
    is stripped; the remainder is returned in file order.
    """
    glosses: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            glosses.append(line)
    return glosses


def process_gloss(
    gloss: str,
    bundles_out: Path,
    tmp_dir: Path,
    *,
    match_legacy: bool = True,
) -> tuple[bool, str | None, dict | None]:
    """Run the full pipeline for a single gloss.

    Steps: download -> parse -> convert to Three.js dict -> write JSON
    under the ASCII-normalised filename.

    The conversion is **idempotent**: calling it multiple times for the
    same gloss overwrites the output atomically.

    Args:
        gloss: Gloss identifier as stored by VLibras (may contain
            Portuguese diacritics, e.g. ``"ÁGUA"``).  The raw form is
            used for the HTTP download because the VLibras CDN keys
            bundles by their original spelling.
        bundles_out: Directory where ``<ASCII-KEY>.threejs.json`` is
            written.
        tmp_dir: Temporary directory for downloaded bundle files.
        match_legacy: Forwarded to :func:`clip_to_threejs_dict`.

    Returns:
        Tuple ``(ok, error, stats)``.  On success ``stats`` contains:
        ``raw`` (original gloss), ``key`` (ASCII form), ``file``
        (basename written to disk), ``track_count``, ``duration``,
        ``sample_rate``, ``output_path`` (absolute path).
    """
    try:
        bundle_path_str = download_gloss(gloss, tmp_dir)
        bundle_path = Path(bundle_path_str)
        raw_clip = _read_unity_clip(bundle_path)
        data = clip_to_threejs_dict(
            raw_clip, gloss, match_legacy=match_legacy,
        )

        key = ascii_key(gloss)
        filename = f"{key}.threejs.json"
        out_path = bundles_out / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        tmp_path.replace(out_path)

        stats = {
            "raw": gloss,
            "key": key,
            "file": filename,
            "track_count": len(data["tracks"]),
            "duration": data["duration"],
            "sample_rate": data["sample_rate"],
            "output_path": str(out_path.resolve()),
        }
        return True, None, stats
    except Exception as exc:  # noqa: BLE001 (isolate per-gloss failure)
        return False, f"{type(exc).__name__}: {exc}", None


def write_index(
    bundles_out: Path,
    successes: list[dict],
    failures: list[tuple[str, str]],
) -> Path:
    """Write a manifest so the player can enumerate available glosses.

    Output shape (the client looks up a translated gloss by first
    applying :func:`ascii_key` to it and then matching against the
    ``key`` field of each entry)::

        {
            "count": 12,
            "glosses": [
                {"raw": "CASA", "key": "CASA",
                 "file": "CASA.threejs.json", "duration": 2.467},
                {"raw": "ÁGUA", "key": "AGUA",
                 "file": "AGUA.threejs.json", "duration": 3.800},
                ...
            ],
            "failures": [
                {"gloss": "MISSING", "reason": "..."},
                ...
            ]
        }

    ``duration`` is included so M4 queue logic can estimate total
    playback length without pre-loading every bundle.
    """
    gloss_entries = [
        {
            "raw": s["raw"],
            "key": s["key"],
            "file": s["file"],
            "duration": round(float(s["duration"]), 4),
        }
        for s in successes
    ]
    index = {
        "count": len(gloss_entries),
        "glosses": gloss_entries,
        "failures": [
            {"gloss": g, "reason": r} for g, r in failures
        ],
    }
    out = bundles_out / "index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Batch-convert VLibras AssetBundles to Three.js JSON files "
            "suitable for the vlibras-v3 player."
        )
    )
    parser.add_argument(
        "--gloss-list",
        type=Path,
        required=True,
        help="Text file with one gloss name per line.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("public/animations/vlibras/bundles"),
        help="Directory for emitted <gloss>.threejs.json files.",
    )
    parser.add_argument(
        "--keep-bundles",
        action="store_true",
        help="Keep downloaded bundle files (debugging).",
    )
    parser.add_argument(
        "--no-legacy",
        dest="match_legacy",
        action="store_false",
        help=(
            "Disable Icaro-bind-pose retargeting and emit raw Unity "
            "values.  Only useful for debugging upstream data; the "
            "result will NOT render correctly on the VLibras GLB "
            "avatars.  Default is retargeted output."
        ),
    )
    parser.set_defaults(match_legacy=True)
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase log verbosity (-v, -vv).",
    )
    args = parser.parse_args(argv)

    log_level = logging.WARNING - 10 * args.verbose
    logging.basicConfig(
        level=max(log_level, logging.DEBUG),
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    if not args.gloss_list.exists():
        logger.error("Gloss list not found: %s", args.gloss_list)
        return 2

    glosses = load_gloss_list(args.gloss_list)
    if not glosses:
        logger.error("Gloss list is empty: %s", args.gloss_list)
        return 2

    mode = "legacy-retarget (Icaro bind pose)" if args.match_legacy else "RAW (Unity pass-through)"
    print(f"Processing {len(glosses)} gloss(es)...")
    print(f"Mode:       {mode}")
    print(f"Output dir: {args.output_dir.resolve()}")
    print()

    successes: list[dict] = []
    failures: list[tuple[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="vlibras_bundle_") as tmp:
        tmp_dir = Path(tmp)
        if args.keep_bundles:
            print(f"Keeping bundles in: {tmp_dir}")

        for gloss in glosses:
            ok, err, stats = process_gloss(
                gloss, args.output_dir, tmp_dir,
                match_legacy=args.match_legacy,
            )
            if ok and stats is not None:
                successes.append(stats)
                print(
                    f"  OK  {gloss:<15} -> {stats['file']:<20} "
                    f"tracks={stats['track_count']:<4} "
                    f"dur={stats['duration']:.3f}s"
                )
            else:
                failures.append((gloss, err or "unknown error"))
                print(f"  FAIL {gloss:<15} {err}")

    index_path = write_index(args.output_dir, successes, failures)

    print()
    print(f"Success: {len(successes)}  Fail: {len(failures)}")
    print(f"Index:   {index_path.resolve()}")

    return 0 if successes else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
