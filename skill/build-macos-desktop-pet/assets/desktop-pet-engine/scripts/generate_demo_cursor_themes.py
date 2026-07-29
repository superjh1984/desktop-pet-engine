#!/usr/bin/env python3
"""Generate two original Mousecape-compatible Blob cursor themes."""

from __future__ import annotations

import argparse
import binascii
import json
import plistlib
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 96
HEIGHT = 96


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(kind)
    checksum = binascii.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def encode_png(pixels: bytearray) -> bytes:
    rows = []
    stride = WIDTH * 4
    for y in range(HEIGHT):
        rows.append(b"\x00" + bytes(pixels[y * stride : (y + 1) * stride]))
    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), level=9))
        + png_chunk(b"IEND", b"")
    )


def draw_ellipse(
    pixels: bytearray,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    color: tuple[int, int, int, int],
) -> None:
    min_x = max(0, int(center_x - radius_x - 1))
    max_x = min(WIDTH - 1, int(center_x + radius_x + 1))
    min_y = max(0, int(center_y - radius_y - 1))
    max_y = min(HEIGHT - 1, int(center_y + radius_y + 1))
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            distance = ((x + 0.5 - center_x) / radius_x) ** 2 + (
                (y + 0.5 - center_y) / radius_y
            ) ** 2
            if distance <= 1:
                offset = (y * WIDTH + x) * 4
                pixels[offset : offset + 4] = bytes(color)


def make_blob_png(body: tuple[int, int, int, int]) -> bytes:
    pixels = bytearray(WIDTH * HEIGHT * 4)
    shadow = (25, 35, 55, 90)
    dark = (25, 35, 55, 255)
    white = (255, 255, 255, 255)

    draw_ellipse(pixels, 49, 77, 29, 7, shadow)
    draw_ellipse(pixels, 48, 54, 31, 27, body)
    draw_ellipse(pixels, 31, 33, 12, 15, body)
    draw_ellipse(pixels, 64, 31, 13, 16, body)
    draw_ellipse(pixels, 34, 50, 8, 10, white)
    draw_ellipse(pixels, 61, 50, 8, 10, white)
    draw_ellipse(pixels, 36, 52, 3, 5, dark)
    draw_ellipse(pixels, 59, 52, 3, 5, dark)
    draw_ellipse(pixels, 48, 66, 10, 4, dark)
    draw_ellipse(pixels, 48, 64, 8, 3, body)
    draw_ellipse(pixels, 36, 27, 5, 4, (255, 255, 255, 80))
    return encode_png(pixels)


def write_cape(
    path: Path,
    *,
    name: str,
    identifier: str,
    color: tuple[int, int, int, int],
) -> None:
    cape = {
        "Author": "Desktop Pet Engine contributors",
        "CapeName": name,
        "CapeVersion": 1,
        "Cloud": False,
        "Cursors": {
            "com.apple.coregraphics.Arrow": {
                "FrameCount": 1,
                "FrameDuration": 1.0,
                "HotSpotX": 24.0,
                "HotSpotY": 24.0,
                "PointsHigh": 48.0,
                "PointsWide": 48.0,
                "Representations": [make_blob_png(color)],
            }
        },
        "HiDPI": True,
        "Identifier": identifier,
        "MinimumVersion": 2,
        "Version": 2,
    }
    with path.open("wb") as handle:
        plistlib.dump(cape, handle, fmt=plistlib.FMT_XML, sort_keys=False)


def ensure_writable(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"{path} already exists; pass --force to replace it")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate original Blob .cape files and a local cursor theme manifest."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "CursorThemes",
        help="Directory for generated .cape files (default: CursorThemes)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "cursor_themes.json",
        help="Local manifest path (default: cursor_themes.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace previously generated demo files",
    )
    args = parser.parse_args()

    example_config = ROOT / "cursor_themes.example.json"
    manifest = json.loads(example_config.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ensure_writable(args.config, args.force)

    colors = {
        "blob-blue": (46, 155, 255, 255),
        "blob-gold": (245, 178, 47, 255),
    }
    for theme in manifest["themes"]:
        cape_path = args.output_dir / theme["cape_file"]
        ensure_writable(cape_path, args.force)
        write_cape(
            cape_path,
            name=theme["title"]["en"],
            identifier=theme["cape_identifier"],
            color=colors[theme["id"]],
        )

    args.config.parent.mkdir(parents=True, exist_ok=True)
    args.config.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(manifest['themes'])} cursor themes in {args.output_dir}")
    print(f"Wrote local manifest to {args.config}")


if __name__ == "__main__":
    main()
