#!/usr/bin/env python3
"""生成每个状态的动画预览。

将每个状态的若干帧拼成一个网格，便于快速检查动画语义和跨帧一致性。

示例：
    python3 generate_preview.py \
        --config /path/to/sprites-config.json \
        --output-dir /path/to/public/images/pet
"""

import argparse
import json
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate motion preview")
    parser.add_argument("--config", required=True, help="Path to sprites-config.json")
    parser.add_argument("--output-dir", required=True, help="Directory containing processed sprites")
    return parser.parse_args()


def load_sprite_config(config_path: str) -> list[dict]:
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        return raw.get("states", [])
    return raw


def main():
    args = parse_args()
    configs = load_sprite_config(args.config)
    output_dir = Path(args.output_dir)

    if not (output_dir / "pet-sprites.json").exists():
        print("pet-sprites.json not found, run process_sprites.py first")
        return

    with open(output_dir / "pet-sprites.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    canonical = metadata.get("canonical", {})
    frame_width = canonical.get("frameWidth", 0)
    frame_height = canonical.get("frameHeight", 0)

    if frame_width == 0 or frame_height == 0:
        print("canonical frame spec missing, aborting")
        return

    max_cols = 6
    margin = 8
    label_height = 24

    state_rows = []
    for cfg in configs:
        state = cfg["name"]
        sprite_path = output_dir / f"{state}.png"
        if not sprite_path.exists():
            continue

        meta = metadata.get(state, {})
        frame_count = meta.get("frameCount", cfg.get("frame_count", 0))
        img = Image.open(sprite_path)

        frames = []
        for i in range(frame_count):
            frame = img.crop((i * frame_width, 0, (i + 1) * frame_width, frame_height))
            frames.append(frame)

        cols = min(max_cols, frame_count)
        rows = (frame_count + cols - 1) // cols
        sheet_width = cols * frame_width + (cols + 1) * margin
        sheet_height = rows * frame_height + (rows + 1) * margin + label_height
        sheet = Image.new("RGBA", (sheet_width, sheet_height), (255, 255, 255, 255))

        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        draw.text((margin, margin), f"{state} ({frame_count} frames)", fill=(0, 0, 0, 255), font=font)

        for i, frame in enumerate(frames):
            col = i % cols
            row = i // cols
            x = margin + col * (frame_width + margin)
            y = margin + label_height + row * (frame_height + margin)
            sheet.paste(frame, (x, y), frame)

        state_rows.append((state, sheet))

    if not state_rows:
        print("No frames found")
        return

    total_width = max(sheet.width for _, sheet in state_rows) + margin * 2
    total_height = sum(sheet.height for _, sheet in state_rows) + margin * (len(state_rows) + 1)
    preview = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 255))

    y = margin
    for state, sheet in state_rows:
        x = (total_width - sheet.width) // 2
        preview.paste(sheet, (x, y), sheet)
        y += sheet.height + margin

    output_path = output_dir / "motion-preview.png"
    preview.save(output_path, "PNG")
    print(f"motion preview saved to {output_path}")


if __name__ == "__main__":
    main()
