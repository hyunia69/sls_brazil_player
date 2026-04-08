"""
SLMB Converter CLI - Main entry point.
BVH -> SLMB encoding/compression and SLMB -> BVH/glTF decoding.

Usage:
  python -m slmb_converter encode <input.bvh> [output.slmb.xz] [--face-frames N]
  python -m slmb_converter decode-bvh <input.slmb.xz> [output.bvh]
  python -m slmb_converter decode-gltf <input.slmb.xz> [output.gltf]
  python -m slmb_converter roundtrip <input.bvh> [--face-frames N]
  python -m slmb_converter info <input.slmb.xz>
"""

import sys
import os
import argparse


def cmd_encode(args):
    """Encode BVH + generated face data -> .slmb.xz"""
    from .bvh_parser import parse_bvh
    from .face_data import generate_sample_face_data
    from .slmb_encoder import bvh_to_slmb

    print(f"[Encode] Parsing BVH: {args.input}")
    bvh = parse_bvh(args.input)
    print(f"  Joints: {len(bvh.joint_list)}, Frames: {bvh.num_frames}, "
          f"Frame Time: {bvh.frame_time:.6f}s")

    # Generate face data matching BVH frame count
    face_frames = args.face_frames or bvh.num_frames
    print(f"[Encode] Generating face data: {face_frames} frames")
    face_data = generate_sample_face_data(face_frames, bvh.frame_time)

    output = args.output or args.input.replace('.bvh', '.slmb.xz')
    print(f"[Encode] Encoding SLMB -> {output}")
    result_path = bvh_to_slmb(bvh, face_data, output)

    file_size = os.path.getsize(result_path)
    print(f"[Encode] Done! Output: {result_path} ({file_size} bytes)")
    return result_path


def cmd_decode_bvh(args):
    """Decode .slmb.xz -> BVH"""
    from .slmb_decoder import decode_slmb_file
    from .bvh_writer import slmb_to_bvh

    print(f"[Decode-BVH] Loading SLMB: {args.input}")
    slmb_data = decode_slmb_file(args.input)
    print(f"  Body: {slmb_data.body.num_frames} frames, "
          f"frame_time={slmb_data.body.frame_time:.6f}s")
    print(f"  Face: {slmb_data.face.num_frames} frames, "
          f"{len(slmb_data.face.blendshapes)} active blendshapes")

    output = args.output or args.input.replace('.slmb.xz', '_decoded.bvh')
    print(f"[Decode-BVH] Writing BVH -> {output}")
    slmb_to_bvh(slmb_data, output)
    print(f"[Decode-BVH] Done!")


def cmd_decode_gltf(args):
    """Decode .slmb.xz -> glTF"""
    from .slmb_decoder import decode_slmb_file
    from .gltf_writer import slmb_to_gltf

    print(f"[Decode-glTF] Loading SLMB: {args.input}")
    slmb_data = decode_slmb_file(args.input)
    print(f"  Body: {slmb_data.body.num_frames} frames, "
          f"frame_time={slmb_data.body.frame_time:.6f}s")
    print(f"  Face: {slmb_data.face.num_frames} frames, "
          f"{len(slmb_data.face.blendshapes)} active blendshapes")

    output = args.output or args.input.replace('.slmb.xz', '_decoded.gltf')
    print(f"[Decode-glTF] Writing glTF -> {output}")
    slmb_to_gltf(slmb_data, output)
    print(f"[Decode-glTF] Done!")


def cmd_roundtrip(args):
    """Full roundtrip test: BVH -> SLMB -> BVH + glTF"""
    from .bvh_parser import parse_bvh
    from .face_data import generate_sample_face_data
    from .slmb_encoder import bvh_to_slmb
    from .slmb_decoder import decode_slmb_file
    from .bvh_writer import slmb_to_bvh
    from .gltf_writer import slmb_to_gltf
    from .json_writer import slmb_to_json

    base = os.path.splitext(args.input)[0]
    slmb_path = base + '.slmb.xz'
    bvh_out = base + '_roundtrip.bvh'
    gltf_out = base + '_roundtrip.gltf'
    json_out = base + '_roundtrip_slmb.json'

    # Step 1: Parse BVH
    print(f"\n{'='*60}")
    print(f"[Step 1] Parsing BVH: {args.input}")
    bvh = parse_bvh(args.input)
    print(f"  Joints: {len(bvh.joint_list)}, Frames: {bvh.num_frames}, "
          f"Frame Time: {bvh.frame_time:.6f}s")

    # Step 2: Generate face data
    face_frames = args.face_frames or bvh.num_frames
    print(f"\n[Step 2] Generating face data: {face_frames} frames")
    face_data = generate_sample_face_data(face_frames, bvh.frame_time)
    print(f"  Generated {face_frames} frames with face expressions")

    # Step 3: Encode to SLMB
    print(f"\n[Step 3] Encoding -> {slmb_path}")
    bvh_to_slmb(bvh, face_data, slmb_path)
    slmb_size = os.path.getsize(slmb_path)
    print(f"  SLMB file size: {slmb_size} bytes (xz compressed)")

    # Step 4: Decode SLMB
    print(f"\n[Step 4] Decoding SLMB...")
    slmb_data = decode_slmb_file(slmb_path)
    print(f"  Body: {slmb_data.body.num_frames} frames")
    print(f"  Face: {slmb_data.face.num_frames} frames, "
          f"{len(slmb_data.face.blendshapes)} blendshapes")

    # Step 5: Write BVH
    print(f"\n[Step 5] Writing BVH -> {bvh_out}")
    slmb_to_bvh(slmb_data, bvh_out)

    # Step 6: Write glTF
    print(f"\n[Step 6] Writing glTF -> {gltf_out}")
    slmb_to_gltf(slmb_data, gltf_out)

    # Step 7: Write JSON
    print(f"\n[Step 7] Writing JSON -> {json_out}")
    slmb_to_json(slmb_data, json_out)
    json_size = os.path.getsize(json_out)

    # Summary
    print(f"\n{'='*60}")
    print(f"Roundtrip complete!")
    print(f"  Input BVH:     {args.input}")
    print(f"  SLMB (xz):     {slmb_path} ({slmb_size} bytes)")
    print(f"  Output BVH:    {bvh_out}")
    print(f"  Output glTF:   {gltf_out}")
    print(f"  Output JSON:   {json_out} ({json_size:,} bytes)")
    print(f"{'='*60}\n")


def cmd_decode_json(args):
    """Decode .slmb.xz -> JSON (SLMBData)"""
    from .slmb_decoder import decode_slmb_file
    from .json_writer import slmb_to_json

    print(f"[Decode-JSON] Loading SLMB: {args.input}")
    slmb_data = decode_slmb_file(args.input)
    print(f"  Body: {slmb_data.body.num_frames} frames")
    print(f"  Face: {slmb_data.face.num_frames} frames, "
          f"{len(slmb_data.face.blendshapes)} blendshapes")

    output = args.output or args.input.replace('.slmb.xz', '_slmb.json')
    print(f"[Decode-JSON] Writing JSON -> {output}")
    slmb_to_json(slmb_data, output, pretty=args.pretty)
    import os
    size = os.path.getsize(output)
    print(f"[Decode-JSON] Done! ({size:,} bytes)")


def cmd_info(args):
    """Show information about an SLMB file."""
    from .slmb_decoder import decode_slmb_file, decompress_slmb
    from .constants import JOINT_ORDER, BLENDSHAPE_ID_TO_NAME, NUM_JOINTS
    import lzma

    print(f"[Info] SLMB File: {args.input}")

    # File size
    compressed_size = os.path.getsize(args.input)
    raw = decompress_slmb(args.input)
    raw_size = len(raw)
    ratio = compressed_size / raw_size * 100 if raw_size > 0 else 0

    print(f"  Compressed size:   {compressed_size} bytes")
    print(f"  Uncompressed size: {raw_size} bytes")
    print(f"  Compression ratio: {ratio:.1f}%")

    # Decode
    slmb_data = decode_slmb_file(args.input)
    bmb = slmb_data.body
    fmb = slmb_data.face

    print(f"\n  --- Body Motion ---")
    print(f"  Frames:     {bmb.num_frames}")
    print(f"  Frame Time: {bmb.frame_time:.6f}s ({1.0/bmb.frame_time:.1f} fps)" if bmb.frame_time > 0 else "  Frame Time: N/A")
    duration = bmb.num_frames * bmb.frame_time if bmb.frame_time > 0 else 0
    print(f"  Duration:   {duration:.3f}s")
    print(f"  Joints:     {NUM_JOINTS}")

    # Body data size
    body_bits_per_frame = 144 + 15*48 + 8*32 + 20*8 + 2*16  # Type0 + Type1 + Type2 + Type3 + Type4
    body_bytes = 8 + (body_bits_per_frame // 8) * bmb.num_frames
    print(f"  Body data:  ~{body_bytes} bytes")

    print(f"\n  --- Face Motion ---")
    print(f"  Frames:      {fmb.num_frames}")
    if fmb.frame_times:
        print(f"  Time range:  {fmb.frame_times[0]:.3f}s - {fmb.frame_times[-1]:.3f}s")
    print(f"  Active blendshapes: {len(fmb.blendshapes)}")
    for bs in fmb.blendshapes:
        name_info = BLENDSHAPE_ID_TO_NAME.get(bs.blend_shape_id, ("?", "?"))
        non_zero = len(bs.weights)
        print(f"    ID {bs.blend_shape_id:5d}: {name_info[0]}/{name_info[1]} "
              f"({non_zero} non-zero frames)")


def main():
    parser = argparse.ArgumentParser(
        description="SLMB Converter - BVH <-> SLMB <-> glTF (ABNT NBR 25606)")
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # encode
    p_encode = subparsers.add_parser('encode', help='BVH -> SLMB')
    p_encode.add_argument('input', help='Input BVH file')
    p_encode.add_argument('output', nargs='?', help='Output .slmb.xz file')
    p_encode.add_argument('--face-frames', type=int, help='Number of face frames')

    # decode-bvh
    p_dbvh = subparsers.add_parser('decode-bvh', help='SLMB -> BVH')
    p_dbvh.add_argument('input', help='Input .slmb.xz file')
    p_dbvh.add_argument('output', nargs='?', help='Output BVH file')

    # decode-gltf
    p_dgltf = subparsers.add_parser('decode-gltf', help='SLMB -> glTF')
    p_dgltf.add_argument('input', help='Input .slmb.xz file')
    p_dgltf.add_argument('output', nargs='?', help='Output glTF file')

    # roundtrip
    p_rt = subparsers.add_parser('roundtrip', help='BVH -> SLMB -> BVH + glTF')
    p_rt.add_argument('input', help='Input BVH file')
    p_rt.add_argument('--face-frames', type=int, help='Number of face frames')

    # decode-json
    p_djson = subparsers.add_parser('decode-json', help='SLMB -> JSON')
    p_djson.add_argument('input', help='Input .slmb.xz file')
    p_djson.add_argument('output', nargs='?', help='Output JSON file')
    p_djson.add_argument('--pretty', action='store_true', help='Pretty-print JSON')

    # info
    p_info = subparsers.add_parser('info', help='Show SLMB file info')
    p_info.add_argument('input', help='Input .slmb.xz file')

    args = parser.parse_args()

    if args.command == 'encode':
        cmd_encode(args)
    elif args.command == 'decode-bvh':
        cmd_decode_bvh(args)
    elif args.command == 'decode-gltf':
        cmd_decode_gltf(args)
    elif args.command == 'roundtrip':
        cmd_roundtrip(args)
    elif args.command == 'decode-json':
        cmd_decode_json(args)
    elif args.command == 'info':
        cmd_info(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
