#!/usr/bin/env python3
"""把桌宠动作视频转换为统一画布的透明 PNG 序列帧。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "assets_config.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "Sources" / "DesktopPetEngine" / "Assets"
VALID_ACTIONS = {
    "idle", "walk", "dance", "playBall", "eat", "drink", "yawn", "frustrated", "crying",
    "shy", "happy", "rowing", "meditation"
}


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def ensure_tools() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise RuntimeError("缺少工具：" + ", ".join(missing) + "。可先运行 brew install ffmpeg")


def probe_video(source: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,pix_fmt,r_frame_rate,duration:format=duration",
            "-of",
            "json",
            str(source),
        ],
        capture=True,
    )
    payload = json.loads(result.stdout.decode("utf-8"))
    stream = payload["streams"][0]
    if not stream.get("duration"):
        stream["duration"] = payload.get("format", {}).get("duration", 0)
    return stream


def pixel_format_has_alpha(pixel_format: str) -> bool:
    value = pixel_format.lower()
    return (
        value.startswith("yuva")
        or value.startswith("gbrap")
        or value in {"rgba", "bgra", "argb", "abgr", "ya8", "ya16le", "ya16be"}
    )


def sample_background_color(source: Path) -> tuple[int, int, int]:
    result = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            "format=rgb24,crop=1:1:0:0",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
        capture=True,
    )
    if len(result.stdout) < 3:
        raise RuntimeError(f"无法读取背景颜色：{source.name}")
    return tuple(result.stdout[:3])  # type: ignore[return-value]


def choose_key_settings(
    source: Path,
    requested_mode: str,
    has_alpha: bool,
    action_config: dict[str, Any],
) -> tuple[str, str | None, float, float]:
    if has_alpha:
        return "alpha", None, 0.0, 0.0

    color = sample_background_color(source)
    mode = requested_mode
    if mode == "auto":
        red, green, blue = color
        if max(color) <= 45:
            mode = "black"
        elif green >= 80 and green > red * 1.25 and green > blue * 1.20:
            mode = "green"
        else:
            raise RuntimeError(
                f"{source.name} 没有透明通道，背景也不是可识别的黑/绿纯色（左上角 RGB={color}）。"
                "请提供透明 MOV，或在配置里明确指定 background/keyColor。"
            )

    if mode == "black":
        similarity = float(action_config.get("keySimilarity", 0.005))
        blend = float(action_config.get("keyBlend", 0.020))
        return mode, "0x000000", similarity, blend
    if mode == "green":
        default_color = f"0x{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        key_color = str(action_config.get("keyColor", default_color))
        similarity = float(action_config.get("keySimilarity", 0.080))
        blend = float(action_config.get("keyBlend", 0.060))
        return mode, key_color, similarity, blend
    if mode == "key":
        key_color = str(action_config.get("keyColor", "0x00ff00"))
        similarity = float(action_config.get("keySimilarity", 0.080))
        blend = float(action_config.get("keyBlend", 0.060))
        return mode, key_color, similarity, blend
    raise RuntimeError(f"不支持的 background 模式：{requested_mode}")


def key_filter(key_color: str | None, similarity: float, blend: float) -> str | None:
    if key_color is None:
        return None
    return f"colorkey={key_color}:{similarity:.5f}:{blend:.5f}"


def detect_union_crop(
    source: Path,
    width: int,
    height: int,
    key_color: str | None,
    similarity: float,
    blend: float,
    padding: int,
) -> tuple[int, int, int, int]:
    filters = ["fps=6", "format=rgba"]
    key = key_filter(key_color, similarity, blend)
    if key:
        filters.append(key)
    filters.extend(["alphaextract", "cropdetect=limit=1:round=2:reset=0"])

    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(source),
            "-vf",
            ",".join(filters),
            "-an",
            "-f",
            "null",
            "-",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    matches = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", result.stderr)
    if not matches:
        return 0, 0, width - (width % 2), height - (height % 2)

    crop_width, crop_height, crop_x, crop_y = map(int, matches[-1])
    left = max(0, crop_x - padding)
    top = max(0, crop_y - padding)
    right = min(width, crop_x + crop_width + padding)
    bottom = min(height, crop_y + crop_height + padding)

    left -= left % 2
    top -= top % 2
    crop_width = max(2, right - left)
    crop_height = max(2, bottom - top)
    crop_width -= crop_width % 2
    crop_height -= crop_height % 2
    return left, top, crop_width, crop_height


def convert_action(
    action: str,
    action_config: dict[str, Any],
    global_config: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    source = Path(str(action_config["source"])).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"找不到“{action}”素材：{source}")

    probe = probe_video(source)
    source_has_alpha = pixel_format_has_alpha(str(probe.get("pix_fmt", "")))
    mode, key_color, similarity, blend = choose_key_settings(
        source,
        str(action_config.get("background", "auto")),
        source_has_alpha,
        action_config,
    )

    source_width = int(probe["width"])
    source_height = int(probe["height"])
    padding = int(global_config.get("cropPadding", 24))
    crop_x, crop_y, crop_width, crop_height = detect_union_crop(
        source,
        source_width,
        source_height,
        key_color,
        similarity,
        blend,
        padding,
    )

    fps = float(global_config.get("fps", 20))
    canvas = global_config.get("canvas", {"width": 360, "height": 360})
    content_box = global_config.get("contentBox", {"width": 300, "height": 300})
    canvas_width = int(canvas["width"])
    canvas_height = int(canvas["height"])
    scale_adjustment = float(action_config.get("scale", 1.0))
    target_width = max(2, int(float(content_box["width"]) * scale_adjustment))
    target_height = max(2, int(float(content_box["height"]) * scale_adjustment))
    offset = action_config.get("offset", [0, 0])
    offset_x, offset_y = int(offset[0]), int(offset[1])

    action_output = output_root / action
    if action_output.exists():
        shutil.rmtree(action_output)
    action_output.mkdir(parents=True, exist_ok=True)

    filters = [f"fps={fps:g}", "format=rgba"]
    key = key_filter(key_color, similarity, blend)
    if key:
        filters.append(key)
    filters.extend(
        [
            f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}",
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:flags=lanczos",
            (
                f"pad={canvas_width}:{canvas_height}:"
                f"(ow-iw)/2+{offset_x}:(oh-ih)/2+{offset_y}:color=0x00000000"
            ),
            "format=rgba",
        ]
    )

    print(
        f"[{action}] {source.name} | {probe.get('codec_name')}/{probe.get('pix_fmt')} | "
        f"alpha={'是' if source_has_alpha else '否'} | 处理={mode} | "
        f"crop={crop_width}x{crop_height}+{crop_x}+{crop_y}"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-i",
            str(source),
            "-an",
            "-vf",
            ",".join(filters),
            "-compression_level",
            "6",
            str(action_output / "frame_%05d.png"),
        ]
    )

    frame_count = len(list(action_output.glob("frame_*.png")))
    if frame_count == 0:
        raise RuntimeError(f"“{action}”没有成功生成 PNG 帧")

    repaired_frames: list[int] = []
    for frame_number_value in action_config.get("repairFrames", []):
        frame_number = int(frame_number_value)
        if frame_number <= 1 or frame_number >= frame_count:
            raise RuntimeError(
                f"“{action}”修复帧 {frame_number} 超出可插值范围 2...{frame_count - 1}"
            )
        previous_frame = action_output / f"frame_{frame_number - 1:05d}.png"
        target_frame = action_output / f"frame_{frame_number:05d}.png"
        next_frame = action_output / f"frame_{frame_number + 1:05d}.png"
        repaired_frame = action_output / f".repair_{frame_number:05d}.png"
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(previous_frame),
                "-i",
                str(next_frame),
                "-filter_complex",
                "[0:v][1:v]blend=all_mode=average,format=rgba",
                "-frames:v",
                "1",
                str(repaired_frame),
            ]
        )
        repaired_frame.replace(target_frame)
        repaired_frames.append(frame_number)
        print(f"[{action}] 已用前后帧插值修复第 {frame_number} 帧")

    metadata: dict[str, Any] = {
        "fps": fps,
        "frameCount": frame_count,
        "sourceFile": source.name,
        "sourceCodec": probe.get("codec_name"),
        "sourcePixelFormat": probe.get("pix_fmt"),
        "sourceHasAlpha": source_has_alpha,
        "backgroundMode": mode,
        "crop": [crop_x, crop_y, crop_width, crop_height],
        "scale": scale_adjustment,
        "offset": [offset_x, offset_y],
    }
    if repaired_frames:
        metadata["repairedFrames"] = repaired_frames
    direction_times = action_config.get("directionTimes")
    if isinstance(direction_times, dict):
        metadata["directionFrames"] = {
            key: min(frame_count - 1, max(0, round(float(seconds) * fps)))
            for key, seconds in direction_times.items()
        }
    return metadata


def parse_source_overrides(values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"--source 格式应为 动作=文件路径，收到：{value}")
        action, path = value.split("=", 1)
        if action not in VALID_ACTIONS:
            raise ValueError(f"未知动作：{action}")
        overrides[action] = path
    return overrides


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="素材配置 JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="PNG 输出目录")
    parser.add_argument("--only", action="append", choices=sorted(VALID_ACTIONS), help="只处理指定动作，可重复")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="动作=文件路径",
        help="临时覆盖某个动作的源文件，可重复",
    )
    args = parser.parse_args()

    try:
        ensure_tools()
        config = json.loads(args.config.read_text(encoding="utf-8"))
        overrides = parse_source_overrides(args.source)
        actions = config.setdefault("actions", {})
        for action, source in overrides.items():
            actions.setdefault(action, {"background": "auto", "scale": 1.0, "offset": [0, 0]})
            actions[action]["source"] = source

        selected = set(args.only) if args.only else VALID_ACTIONS
        args.output.mkdir(parents=True, exist_ok=True)
        manifest_path = args.output / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            manifest = {"version": 1, "animations": {}}

        canvas = config.get("canvas", {"width": 360, "height": 360})
        manifest["version"] = 1
        manifest["canvasWidth"] = int(canvas["width"])
        manifest["canvasHeight"] = int(canvas["height"])
        manifest.setdefault("animations", {})

        processed = 0
        for action in sorted(selected):
            action_config = actions.get(action, {})
            if not action_config.get("source"):
                continue
            manifest["animations"][action] = convert_action(
                action,
                action_config,
                config,
                args.output,
            )
            processed += 1

        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"完成：处理 {processed} 个动作，manifest 写入 {manifest_path}")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
