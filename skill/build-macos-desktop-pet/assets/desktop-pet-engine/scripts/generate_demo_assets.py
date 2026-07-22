#!/usr/bin/env python3
"""Generate a tiny original blob-pet asset pack for the public template."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as error:  # pragma: no cover - dependency message
    raise SystemExit("Pillow is required: python3 -m pip install pillow") from error


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "Sources" / "DesktopPetEngine" / "Assets"
SIZE = 360
FRAME_COUNT = 16
ACTIONS = (
    "walk",
    "dance",
    "playBall",
    "eat",
    "drink",
    "yawn",
    "frustrated",
    "crying",
    "shy",
    "happy",
    "rowing",
    "meditation",
)
DIRECTIONS = (
    "center",
    "upLeft",
    "up",
    "upRight",
    "right",
    "downRight",
    "down",
    "downLeft",
    "left",
)


def circle(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float, fill, outline=None, width=1):
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=width)


def line(draw: ImageDraw.ImageDraw, points, fill, width=8):
    draw.line(points, fill=fill, width=width, joint="curve")


def draw_pet(action: str, frame: int, direction: str = "center") -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    phase = frame / max(1, FRAME_COUNT - 1) * math.tau
    bounce = math.sin(phase) * 6
    sway = math.sin(phase) * 12
    cx, cy = 180.0, 190.0

    if action == "walk":
        cy += abs(math.sin(phase)) * -10
    elif action == "dance":
        cx += sway
        cy += bounce
    elif action == "frustrated":
        cx += 4 if frame % 2 else -4
    elif action == "happy":
        cy -= abs(math.sin(phase)) * 18
    elif action == "meditation":
        cy += 22

    outline = (24, 52, 72, 255)
    body = (70, 205, 206, 255)
    highlight = (120, 238, 228, 255)
    shadow = (35, 151, 171, 255)
    blush = (255, 132, 153, 210)
    eye = (18, 34, 48, 255)

    # Feet and arms sit behind the body.
    left_foot = -10 if action == "walk" and frame % 4 < 2 else 7
    right_foot = 10 if action == "walk" and frame % 4 < 2 else -7
    draw.rounded_rectangle((cx - 83 + left_foot, cy + 78, cx - 18 + left_foot, cy + 105), 13, fill=shadow, outline=outline, width=5)
    draw.rounded_rectangle((cx + 18 + right_foot, cy + 78, cx + 83 + right_foot, cy + 105), 13, fill=shadow, outline=outline, width=5)

    arm_y = cy + 15
    left_hand = (cx - 104, arm_y + math.sin(phase) * 9)
    right_hand = (cx + 104, arm_y - math.sin(phase) * 9)
    if action in {"dance", "happy"}:
        left_hand = (cx - 92, cy - 78 + bounce)
        right_hand = (cx + 92, cy - 78 - bounce)
    elif action == "frustrated":
        left_hand = (cx - 60, cy - 85)
        right_hand = (cx + 60, cy - 85)
    elif action == "rowing":
        reach = math.sin(phase) * 36
        left_hand = (cx - 65 + reach, cy + 20)
        right_hand = (cx + 65 + reach, cy + 20)
    elif action == "meditation":
        left_hand = (cx - 78, cy + 48)
        right_hand = (cx + 78, cy + 48)

    line(draw, ((cx - 58, cy + 8), left_hand), shadow, 22)
    line(draw, ((cx + 58, cy + 8), right_hand), shadow, 22)
    circle(draw, *left_hand, 15, highlight, outline, 4)
    circle(draw, *right_hand, 15, highlight, outline, 4)

    # Blob body.
    draw.ellipse((cx - 91, cy - 94, cx + 91, cy + 92), fill=body, outline=outline, width=6)
    draw.ellipse((cx - 58, cy - 72, cx + 16, cy - 5), fill=highlight)
    draw.arc((cx - 90, cy - 94, cx + 91, cy + 92), 310, 100, fill=shadow, width=8)

    look = {
        "center": (0, 0), "upLeft": (-5, -7), "up": (0, -8), "upRight": (5, -7),
        "right": (7, 0), "downRight": (5, 7), "down": (0, 8),
        "downLeft": (-5, 7), "left": (-7, 0),
    }[direction]
    eye_y = cy - 25
    for eye_x in (cx - 34, cx + 34):
        circle(draw, eye_x, eye_y, 20, (255, 255, 255, 255), outline, 4)
        circle(draw, eye_x + look[0], eye_y + look[1], 8, eye)

    # Mouth and action props.
    if action == "yawn":
        draw.ellipse((cx - 25, cy + 10, cx + 25, cy + 58), fill=(64, 42, 68, 255), outline=outline, width=4)
    elif action == "frustrated":
        line(draw, ((cx - 52, cy - 54), (cx - 18, cy - 42)), eye, 7)
        line(draw, ((cx + 18, cy - 42), (cx + 52, cy - 54)), eye, 7)
        draw.arc((cx - 28, cy + 18, cx + 28, cy + 65), 200, 340, fill=eye, width=6)
    elif action == "crying":
        draw.arc((cx - 30, cy + 14, cx + 30, cy + 58), 200, 340, fill=eye, width=5)
        line(draw, ((cx - 35, cy - 2), (cx - 39, cy + 42)), (71, 164, 255, 220), 8)
        line(draw, ((cx + 35, cy - 2), (cx + 39, cy + 42)), (71, 164, 255, 220), 8)
    else:
        draw.arc((cx - 31, cy + 1, cx + 31, cy + 48), 12, 168, fill=eye, width=6)

    if action == "shy":
        circle(draw, cx - 61, cy + 9, 15, blush)
        circle(draw, cx + 61, cy + 9, 15, blush)
    elif action == "playBall":
        ball_x = cx + math.cos(phase) * 105
        ball_y = cy + 45 + math.sin(phase) * 38
        circle(draw, ball_x, ball_y, 28, (255, 194, 64, 255), outline, 4)
        line(draw, ((ball_x - 15, ball_y), (ball_x + 15, ball_y)), outline, 3)
        line(draw, ((ball_x, ball_y - 15), (ball_x, ball_y + 15)), outline, 3)
    elif action == "eat":
        circle(draw, cx + 74, cy + 35, 24, (218, 151, 83, 255), outline, 4)
        for angle in (0, 2.1, 4.2):
            circle(draw, cx + 74 + math.cos(angle) * 10, cy + 35 + math.sin(angle) * 10, 3, eye)
    elif action == "drink":
        draw.rounded_rectangle((cx + 55, cy - 3, cx + 94, cy + 71), 10, fill=(100, 150, 255, 255), outline=outline, width=4)
        draw.rectangle((cx + 66, cy - 16, cx + 83, cy + 2), fill=(230, 245, 255, 255), outline=outline, width=3)
    elif action == "meditation":
        line(draw, ((cx - 76, cy + 78), (cx - 5, cy + 96), (cx + 76, cy + 78)), outline, 14)

    return image


def main() -> int:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    animations: dict[str, dict] = {}
    idle_dir = OUTPUT / "idle"
    idle_dir.mkdir()
    for index, direction in enumerate(DIRECTIONS, start=1):
        draw_pet("idle", index - 1, direction).save(idle_dir / f"frame_{index:05d}.png", optimize=True)
    animations["idle"] = {
        "fps": 1.0,
        "frameCount": len(DIRECTIONS),
        "directionFrames": {direction: index for index, direction in enumerate(DIRECTIONS)},
        "sourceFile": "programmatic-demo-blob",
    }

    for action in ACTIONS:
        folder = OUTPUT / action
        folder.mkdir()
        for frame in range(FRAME_COUNT):
            draw_pet(action, frame).save(folder / f"frame_{frame + 1:05d}.png", optimize=True)
        animations[action] = {
            "fps": 12.0,
            "frameCount": FRAME_COUNT,
            "sourceFile": "programmatic-demo-blob",
        }

    manifest = {
        "version": 1,
        "canvasWidth": SIZE,
        "canvasHeight": SIZE,
        "animations": animations,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {sum(item['frameCount'] for item in animations.values())} frames in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
