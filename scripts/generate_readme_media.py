#!/usr/bin/env python3
"""Generate README screenshots and motion previews from the public demo frames."""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS = ROOT / "Sources" / "DesktopPetEngine" / "Assets"
ASSETS = DEFAULT_ASSETS
OUTPUT = ROOT / "docs" / "media"
PROFILE = "blob"

WIDTH = 1600
HEIGHT = 900

FONT_REGULAR = Path("/System/Library/Fonts/SFNS.ttf")
FONT_ROUNDED = Path("/System/Library/Fonts/SFNSRounded.ttf")
FONT_FALLBACK = Path("/System/Library/Fonts/Supplemental/Arial.ttf")

NAVY = (8, 18, 39)
INK = (10, 25, 51)
MUTED = (111, 128, 157)
CYAN = (69, 207, 207)
CYAN_LIGHT = (131, 247, 231)
BLUE = (48, 132, 255)
ORANGE = (255, 177, 48)
WHITE = (247, 251, 255)


def is_character_showcase() -> bool:
    return PROFILE == "character"


def app_font(size: int, rounded: bool = False) -> ImageFont.FreeTypeFont:
    preferred = FONT_ROUNDED if rounded else FONT_REGULAR
    path = preferred if preferred.exists() else FONT_FALLBACK
    return ImageFont.truetype(str(path), size=size)


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    strip = Image.new("RGB", (1, height))
    pixels = strip.load()
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(round(top[channel] * (1 - t) + bottom[channel] * t) for channel in range(3))
        pixels[0, y] = color
    return strip.resize((width, height), Image.Resampling.BILINEAR).convert("RGBA")


def frame_path(action: str, index: int) -> Path:
    frames = sorted((ASSETS / action).glob("frame_*.png"))
    if not frames:
        raise FileNotFoundError(f"No public demo frames found for action: {action}")
    return frames[index % len(frames)]


def pet_frame(action: str, index: int, size: int) -> Image.Image:
    with Image.open(frame_path(action, index)) as source:
        rgba = source.convert("RGBA")
    return rgba.resize((size, size), Image.Resampling.LANCZOS)


def paste_with_shadow(canvas: Image.Image, subject: Image.Image, position: tuple[int, int], blur: int = 28) -> None:
    x, y = position
    alpha = subject.getchannel("A")
    shadow = Image.new("RGBA", subject.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(blur)))
    dark = Image.new("RGBA", subject.size, (0, 12, 30, 150))
    dark.putalpha(shadow.getchannel("A"))
    canvas.alpha_composite(dark, (x + 12, y + 24))
    canvas.alpha_composite(subject, (x, y))


def rounded_panel(canvas: Image.Image, box: tuple[int, int, int, int], fill: tuple[int, int, int, int], radius: int, outline=None, width: int = 1) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    canvas.alpha_composite(overlay)


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, accent: tuple[int, int, int] = CYAN) -> int:
    x, y = xy
    label_font = app_font(25, rounded=True)
    bbox = draw.textbbox((0, 0), text, font=label_font)
    width = bbox[2] - bbox[0] + 42
    draw.rounded_rectangle((x, y, x + width, y + 48), radius=24, fill=(*accent, 34), outline=(*accent, 120), width=2)
    draw.text((x + 21, y + 10), text, font=label_font, fill=WHITE)
    return width


def add_glow(canvas: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 2))
    canvas.alpha_composite(glow)


def create_hero() -> Path:
    canvas = vertical_gradient((WIDTH, HEIGHT), (8, 20, 49), (14, 62, 94))
    add_glow(canvas, (1310, 220), 290, CYAN, 80)
    add_glow(canvas, (240, 790), 260, BLUE, 55)

    panel = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    rounded_panel(panel, (58, 48, 1542, 852), (8, 19, 42, 222), 44, (255, 255, 255, 35), 2)
    canvas.alpha_composite(panel)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((90, 76, 1510, 124), radius=20, fill=(255, 255, 255, 15))
    for i, color in enumerate(((255, 95, 87), (255, 189, 46), (39, 201, 63))):
        draw.ellipse((116 + i * 30, 91, 132 + i * 30, 107), fill=color)
    top_label = "UNOFFICIAL CHARACTER DEMO" if is_character_showcase() else "PUBLIC DEMO"
    draw.text((1190, 88), top_label, font=app_font(20, rounded=True), fill=(165, 184, 212))

    draw.text((132, 205), "Desktop Pet", font=app_font(83, rounded=True), fill=WHITE)
    draw.text((132, 292), "Engine", font=app_font(83, rounded=True), fill=CYAN_LIGHT)
    draw.text((136, 403), "A tiny native macOS companion,", font=app_font(35), fill=(211, 225, 241))
    draw.text((136, 450), "ready for your own character.", font=app_font(35), fill=(211, 225, 241))

    x = 136
    for label, color in (("AppKit", CYAN), ("Universal 2", BLUE), ("Apache-2.0", ORANGE)):
        x += pill(draw, (x, 520), label, color) + 16

    rounded_panel(canvas, (132, 624, 760, 755), (0, 8, 28, 185), 24, (112, 222, 228, 65), 2)
    draw = ImageDraw.Draw(canvas)
    draw.text((166, 652), "$  ./scripts/run_demo.sh", font=app_font(29), fill=(161, 244, 223))
    draw.text((166, 704), "✓  Native desktop pet is ready", font=app_font(25), fill=(178, 195, 217))

    rounded_panel(canvas, (855, 154, 1456, 782), (255, 255, 255, 17), 44, (255, 255, 255, 28), 2)
    add_glow(canvas, (1165, 470), 230, CYAN, 52)
    main_action, main_index = ("happy", 39) if is_character_showcase() else ("dance", 7)
    main_pet = pet_frame(main_action, main_index, 460)
    paste_with_shadow(canvas, main_pet, (934, 260), blur=32)

    rounded_panel(canvas, (830, 178, 1012, 360), (13, 31, 57, 235), 34, (255, 255, 255, 38), 2)
    side_action, side_index = ("shy", 39) if is_character_showcase() else ("playBall", 9)
    small_pet = pet_frame(side_action, side_index, 168)
    paste_with_shadow(canvas, small_pet, (837, 185), blur=14)

    rounded_panel(canvas, (1272, 590, 1446, 764), (13, 31, 57, 235), 34, (255, 255, 255, 38), 2)
    small_pet = pet_frame("rowing", 5, 160)
    paste_with_shadow(canvas, small_pet, (1279, 597), blur=14)

    draw = ImageDraw.Draw(canvas)
    footer_label = "SHOWCASE MEDIA ONLY" if is_character_showcase() else "ORIGINAL BLOB DEMO"
    draw.text((1000, 724), footer_label, font=app_font(18, rounded=True), fill=(165, 184, 212))

    output = OUTPUT / "hero.png"
    canvas.convert("RGB").save(output, quality=94)
    return output


def create_desktop_preview() -> Path:
    canvas = vertical_gradient((1600, 1000), (35, 79, 120), (8, 26, 54))
    add_glow(canvas, (1160, 390), 330, CYAN, 58)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 1600, 48), fill=(245, 248, 252, 226))
    draw.text((34, 13), "●  Desktop Pet Engine", font=app_font(20), fill=INK)
    draw.text((1290, 13), "Wi-Fi     10:24", font=app_font(20), fill=INK)

    rounded_panel(canvas, (90, 112, 720, 710), (8, 17, 37, 218), 34, (255, 255, 255, 34), 2)
    draw = ImageDraw.Draw(canvas)
    for i, color in enumerate(((255, 95, 87), (255, 189, 46), (39, 201, 63))):
        draw.ellipse((122 + i * 30, 140, 140 + i * 30, 158), fill=color)
    draw.text((124, 205), "A real native macOS pet", font=app_font(42, rounded=True), fill=WHITE)
    draw.text((124, 278), "• transparent borderless window", font=app_font(27), fill=(193, 211, 232))
    draw.text((124, 326), "• pixel-perfect hit testing", font=app_font(27), fill=(193, 211, 232))
    draw.text((124, 374), "• drag, click and hover reactions", font=app_font(27), fill=(193, 211, 232))
    draw.text((124, 422), "• menu actions + autonomous mode", font=app_font(27), fill=(193, 211, 232))
    rounded_panel(canvas, (124, 508, 626, 632), (2, 9, 26, 220), 22, (94, 226, 218, 55), 2)
    draw = ImageDraw.Draw(canvas)
    draw.text((156, 540), "$ ./scripts/check_demo.sh", font=app_font(25), fill=CYAN_LIGHT)
    draw.text((156, 582), "✓ x86_64  ✓ arm64", font=app_font(23), fill=(167, 188, 214))

    desktop_action, desktop_index = ("happy", 39) if is_character_showcase() else ("idle", 4)
    pet = pet_frame(desktop_action, desktop_index, 430)
    pet_x = 800 if is_character_showcase() else 930
    paste_with_shadow(canvas, pet, (pet_x, 300), blur=34)

    rounded_panel(canvas, (1160, 160, 1484, 662), (250, 252, 255, 246), 22, (255, 255, 255, 100), 1)
    draw = ImageDraw.Draw(canvas)
    menu_items = [
        ("Walk", False),
        ("Dance", False),
        ("Play ball", False),
        ("Drink", False),
        ("Random action", True),
        ("Adjust size", False),
        ("Hide", True),
    ]
    y = 190
    for label, divider in menu_items:
        if divider:
            draw.line((1180, y - 10, 1464, y - 10), fill=(198, 206, 218), width=1)
        draw.text((1200, y), label, font=app_font(25), fill=INK)
        y += 62

    rounded_panel(canvas, (460, 850, 1140, 946), (240, 245, 252, 225), 28)
    draw = ImageDraw.Draw(canvas)
    icons = ["Finder", "Code", "Pet", "Terminal", "Settings"]
    x = 500
    for index, label in enumerate(icons):
        color = (56 + index * 24, 147 + index * 10, 230 - index * 20)
        draw.rounded_rectangle((x, 870, x + 56, 926), radius=14, fill=color)
        draw.text((x + 12, 886), label[0], font=app_font(24, rounded=True), fill=WHITE)
        x += 126

    preview_note = (
        "Unofficial character showcase · source frames and app are not included"
        if is_character_showcase()
        else "Public demo preview · generated from the repository's actual frames"
    )
    draw.text((92, 758), preview_note, font=app_font(21), fill=(184, 205, 229))

    output = OUTPUT / "desktop-preview.png"
    canvas.convert("RGB").save(output, quality=94)
    return output


def create_action_grid() -> Path:
    canvas = vertical_gradient((1600, 900), (247, 251, 255), (220, 237, 246))
    draw = ImageDraw.Draw(canvas)
    draw.text((90, 62), "One engine. Many moods.", font=app_font(62, rounded=True), fill=INK)
    draw.text((94, 138), "Swap the frame packs and make the pet completely yours.", font=app_font(28), fill=MUTED)

    if is_character_showcase():
        cards = [
            ("walk", 49, "WALK", CYAN),
            ("eat", 49, "EAT", ORANGE),
            ("drink", 49, "DRINK", (255, 116, 135)),
            ("happy", 39, "HAPPY", BLUE),
            ("rowing", 39, "ROW", (110, 126, 255)),
            ("meditation", 59, "MEDITATE", (100, 191, 129)),
        ]
    else:
        cards = [
            ("dance", 7, "DANCE", CYAN),
            ("playBall", 9, "PLAY BALL", ORANGE),
            ("eat", 4, "EAT", (255, 116, 135)),
            ("drink", 8, "DRINK", BLUE),
            ("rowing", 5, "ROW", (110, 126, 255)),
            ("meditation", 2, "MEDITATE", (100, 191, 129)),
        ]
    positions = [(90, 230), (590, 230), (1090, 230), (90, 550), (590, 550), (1090, 550)]

    for (action, index, label, accent), (x, y) in zip(cards, positions):
        shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle((x + 8, y + 14, x + 420, y + 278), radius=32, fill=(8, 31, 54, 40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
        canvas.alpha_composite(shadow)
        rounded_panel(canvas, (x, y, x + 420, y + 270), (255, 255, 255, 244), 32, (255, 255, 255, 255), 2)
        draw = ImageDraw.Draw(canvas)
        pale_accent = tuple(round(channel * 0.18 + 255 * 0.82) for channel in accent)
        draw.rounded_rectangle((x + 24, y + 22, x + 162, y + 60), radius=19, fill=pale_accent)
        draw.text((x + 42, y + 31), label, font=app_font(18, rounded=True), fill=accent)
        pet = pet_frame(action, index, 220)
        paste_with_shadow(canvas, pet, (x + 104, y + 42), blur=16)

    output = OUTPUT / "action-grid.png"
    canvas.convert("RGB").save(output, quality=94)
    return output


def motion_background(scene: int) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    palettes = [
        ((8, 20, 48), (11, 66, 91)),
        ((21, 25, 68), (15, 91, 104)),
        ((33, 25, 63), (111, 60, 86)),
        ((7, 44, 61), (18, 102, 103)),
        ((21, 37, 76), (48, 88, 135)),
        ((8, 20, 48), (11, 66, 91)),
    ]
    return palettes[scene % len(palettes)]


def render_motion_frame(action: str, action_label: str, source_index: int, phase_index: int, scene: int, total_scenes: int) -> Image.Image:
    top, bottom = motion_background(scene)
    canvas = vertical_gradient((1280, 720), top, bottom)
    add_glow(canvas, (935, 310), 260, CYAN, 52)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((42, 34, 1238, 686), radius=34, fill=(6, 16, 39, 160), outline=(255, 255, 255, 30), width=2)
    draw.rounded_rectangle((72, 62, 334, 108), radius=23, fill=(69, 207, 207, 30), outline=(69, 207, 207, 95), width=2)
    demo_label = "UNOFFICIAL CHARACTER DEMO" if is_character_showcase() else "NATIVE macOS DEMO"
    draw.text((98, 73), demo_label, font=app_font(20, rounded=True), fill=CYAN_LIGHT)

    draw.text((88, 190), "Desktop Pet", font=app_font(58, rounded=True), fill=WHITE)
    draw.text((88, 253), "Engine", font=app_font(58, rounded=True), fill=CYAN_LIGHT)
    draw.text((92, 352), "NOW PLAYING", font=app_font(18, rounded=True), fill=(145, 167, 196))
    draw.text((88, 382), action_label, font=app_font(45, rounded=True), fill=WHITE)

    chips = ["transparent", "draggable", "custom actions"]
    x = 88
    for label in chips:
        x += pill(draw, (x, 474), label, CYAN) + 12

    source_note = (
        "Showcase media only · source character pack is not included"
        if is_character_showcase()
        else "Generated from the public repository frames"
    )
    draw.text((90, 602), source_note, font=app_font(21), fill=(161, 183, 211))

    y_offset = round(math.sin(phase_index / 16 * math.pi * 2) * 8)
    pet = pet_frame(action, source_index, 430)
    paste_with_shadow(canvas, pet, (748, 144 + y_offset), blur=30)

    for position in range(total_scenes):
        color = CYAN_LIGHT if position == scene else (94, 116, 147)
        x = 882 + position * 38
        draw.rounded_rectangle((x, 622, x + (24 if position == scene else 10), 632), radius=5, fill=color)

    return canvas.convert("RGB")


def create_motion_preview() -> tuple[Path, Path]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to generate README motion previews")

    if is_character_showcase():
        scenes = [
            ("happy", "CHARACTER READY"),
            ("walk", "WALK"),
            ("eat", "EAT"),
            ("rowing", "ROWING"),
            ("meditation", "MEDITATE"),
            ("happy", "BUILD YOUR OWN"),
        ]
    else:
        scenes = [
            ("idle", "IDLE"),
            ("dance", "DANCE"),
            ("playBall", "PLAY BALL"),
            ("happy", "HAPPY"),
            ("rowing", "ROWING"),
            ("idle", "READY FOR YOUR PET"),
        ]

    with tempfile.TemporaryDirectory(prefix="desktop-pet-readme-") as temp_dir:
        frame_dir = Path(temp_dir)
        output_index = 0
        for scene_index, (action, label) in enumerate(scenes):
            available = sorted((ASSETS / action).glob("frame_*.png"))
            for frame_index in range(16):
                source_index = (
                    round(frame_index / 15 * (len(available) - 1))
                    if is_character_showcase()
                    else frame_index % len(available)
                )
                frame = render_motion_frame(
                    action,
                    label,
                    source_index,
                    frame_index,
                    scene_index,
                    len(scenes),
                )
                frame.save(frame_dir / f"frame_{output_index:04d}.png", optimize=True)
                output_index += 1

        input_pattern = str(frame_dir / "frame_%04d.png")
        gif_path = OUTPUT / "demo.gif"
        mp4_path = OUTPUT / "demo.mp4"

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                "12",
                "-i",
                input_pattern,
                "-filter_complex",
                "[0:v]fps=12,scale=960:-2:flags=lanczos,split[s0][s1];"
                "[s0]palettegen=max_colors=128[p];"
                "[s1][p]paletteuse=dither=bayer:bayer_scale=3",
                "-loop",
                "0",
                str(gif_path),
            ],
            check=True,
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                "12",
                "-i",
                input_pattern,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "20",
                "-movflags",
                "+faststart",
                str(mp4_path),
            ],
            check=True,
        )

    return gif_path, mp4_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asset-root",
        type=Path,
        default=DEFAULT_ASSETS,
        help="Frame-pack root. Defaults to the repository's public Blob assets.",
    )
    parser.add_argument(
        "--profile",
        choices=("blob", "character"),
        default="blob",
        help="Select public Blob labels/actions or a separately held character showcase.",
    )
    args = parser.parse_args()

    global ASSETS, PROFILE
    ASSETS = args.asset_root.expanduser().resolve()
    PROFILE = args.profile
    if not (ASSETS / "manifest.json").is_file():
        raise FileNotFoundError(f"Asset manifest not found: {ASSETS / 'manifest.json'}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    outputs = [create_hero(), create_desktop_preview(), create_action_grid()]
    outputs.extend(create_motion_preview())
    for output in outputs:
        size_kib = output.stat().st_size / 1024
        print(f"generated {output.relative_to(ROOT)} ({size_kib:.1f} KiB)")


if __name__ == "__main__":
    main()
