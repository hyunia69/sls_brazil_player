"""Command-line interface for the VLibras -> SLMB converter.

Provides subcommands:
    convert    -- Convert a single file (AssetBundle or JSON) to SLMB
    validate   -- Validate a .slmb.xz file (with optional roundtrip check)
    decode-gltf -- Decode .slmb.xz to glTF with animation
    batch      -- Batch convert multiple glosses
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    """Entry point for the vlibras2slmb CLI."""
    parser = argparse.ArgumentParser(
        description="VLibras -> SLMB Converter",
        prog="vlibras2slmb",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -- convert ---------------------------------------------------------------
    conv = subparsers.add_parser("convert", help="Convert a single file")
    conv.add_argument("input", help="Input file (AssetBundle or JSON)")
    conv.add_argument("-o", "--output", help="Output .slmb.xz path")
    conv.add_argument(
        "--json",
        action="store_true",
        help="Treat input as JSON (not AssetBundle)",
    )

    # -- validate --------------------------------------------------------------
    val = subparsers.add_parser("validate", help="Validate a .slmb.xz file")
    val.add_argument("slmb_file", help=".slmb.xz file to validate")
    val.add_argument(
        "--reference",
        help="Reference JSON for roundtrip comparison",
    )

    # -- decode-gltf -----------------------------------------------------------
    dec = subparsers.add_parser(
        "decode-gltf",
        help="Decode .slmb.xz to glTF with animation",
    )
    dec.add_argument("slmb_file", help=".slmb.xz file to decode")
    dec.add_argument("-o", "--output", help="Output .gltf path")
    dec.add_argument(
        "--name",
        default="sign_animation",
        help="Animation clip name (default: sign_animation)",
    )

    # -- batch -----------------------------------------------------------------
    batch = subparsers.add_parser("batch", help="Batch convert glosses")
    batch.add_argument("--gloss-list", help="Path to gloss list file (JSON array)")
    batch.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for .slmb.xz files",
    )
    batch.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )

    args = parser.parse_args()

    if args.command == "convert":
        _do_convert(args)
    elif args.command == "validate":
        _do_validate(args)
    elif args.command == "decode-gltf":
        _do_decode_gltf(args)
    elif args.command == "batch":
        _do_batch(args)
    else:
        parser.print_help()
        sys.exit(1)


def _do_convert(args: argparse.Namespace) -> None:
    """Execute the 'convert' subcommand."""
    from .parsing.animation_clip import AnimationClipData
    from .retarget.body_retarget import retarget_body
    from .retarget.face_retarget import retarget_face
    from .encoding.body_encoder import encode_body_motion
    from .encoding.face_encoder import encode_face_motion
    from .encoding.motion_bundle import build_motion_bundle
    from .encoding.slmb_writer import write_slmb

    # Load input
    if args.json or args.input.endswith(".json"):
        clip = AnimationClipData.from_json(args.input)
    else:
        from .parsing.asset_bundle import load_asset_bundle

        clip = load_asset_bundle(args.input)

    print(f"Loaded: {clip.name}, {clip.sample_rate}fps, {clip.duration:.3f}s")

    # Retarget
    body_data = retarget_body(clip)
    face_data = retarget_face(clip)
    print(f"Retargeted: {body_data.num_frames} frames")

    # Encode
    body_block = encode_body_motion(body_data)
    face_block = encode_face_motion(face_data)
    print(f"Encoded: body={len(body_block)}B, face={len(face_block)}B")

    # Assemble and compress
    bundle = build_motion_bundle(body_block, face_block)

    output = args.output or os.path.splitext(args.input)[0] + ".slmb.xz"
    write_slmb(bundle, output)

    compressed_size = os.path.getsize(output)
    print(
        f"Output: {output} "
        f"({compressed_size}B compressed, {len(bundle)}B uncompressed)"
    )


def _do_validate(args: argparse.Namespace) -> None:
    """Execute the 'validate' subcommand."""
    from .encoding.slmb_writer import read_slmb
    from .validation.roundtrip import (
        parse_motion_bundle,
        decode_body_motion_block,
        decode_face_motion_block,
    )

    raw = read_slmb(args.slmb_file)
    print(f"Decompressed: {len(raw)} bytes")

    bundle = parse_motion_bundle(raw)
    print(f"MotionBundle elements: {list(bundle.keys())}")

    if "body" in bundle:
        body = decode_body_motion_block(bundle["body"])
        print(
            f"Body: {body['num_frames']} frames, "
            f"frame_time={body['frame_time']:.6f}s"
        )

    if "face" in bundle:
        face = decode_face_motion_block(bundle["face"])
        print(
            f"Face: {face['num_frames']} frames, "
            f"{face['num_blendshapes']} active blendshapes"
        )

    if args.reference:
        from .parsing.animation_clip import AnimationClipData
        from .validation.roundtrip import validate_roundtrip

        clip = AnimationClipData.from_json(args.reference)
        results = validate_roundtrip(clip, args.slmb_file)

        print("\nRoundtrip validation:")
        print(f"  Max quaternion error: {results['max_quat_error']:.6f}")
        print(f"  Mean quaternion error: {results['mean_quat_error']:.6f}")

        if results["passed"]:
            print("  PASS: Error within tolerance")
        else:
            print("  WARN: Error exceeds threshold")

            # Report top-5 worst joints
            per_joint = results.get("per_joint_max_error", {})
            if per_joint:
                sorted_joints = sorted(
                    per_joint.items(), key=lambda x: x[1], reverse=True
                )
                print("\n  Worst joints:")
                for joint_name, err in sorted_joints[:5]:
                    print(f"    {joint_name}: {err:.6f}")


def _do_decode_gltf(args: argparse.Namespace) -> None:
    """Execute the 'decode-gltf' subcommand."""
    from .encoding.slmb_writer import read_slmb
    from .validation.roundtrip import (
        parse_motion_bundle,
        decode_body_motion_block,
        decode_face_motion_block,
    )
    from .encoding.gltf_writer import write_gltf

    raw = read_slmb(args.slmb_file)
    print(f"Decompressed: {len(raw)} bytes")

    bundle = parse_motion_bundle(raw)
    print(f"MotionBundle elements: {list(bundle.keys())}")

    body_data = None
    face_data = None

    if "body" in bundle:
        body_data = decode_body_motion_block(bundle["body"])
        print(
            f"Body: {body_data['num_frames']} frames, "
            f"frame_time={body_data['frame_time']:.6f}s"
        )
    else:
        print("ERROR: No body block in MotionBundle")
        sys.exit(1)

    if "face" in bundle:
        face_data = decode_face_motion_block(bundle["face"])
        print(
            f"Face: {face_data['num_frames']} frames, "
            f"{face_data['num_blendshapes']} active blendshapes"
        )

    output = args.output or os.path.splitext(
        os.path.splitext(args.slmb_file)[0]
    )[0] + ".gltf"

    write_gltf(body_data, face_data, output, animation_name=args.name)
    print(f"Output: {output}")


def _do_batch(args: argparse.Namespace) -> None:
    """Execute the 'batch' subcommand."""
    print("Batch conversion not yet fully implemented (requires UnityPy)")
    print("Use 'convert --json' for individual JSON files")

    if args.gloss_list:
        from .batch.downloader import load_gloss_list_file

        glosses = load_gloss_list_file(args.gloss_list)
        print(f"Loaded {len(glosses)} glosses from {args.gloss_list}")
    else:
        print("No --gloss-list provided. Nothing to do.")
