#!/usr/bin/env python3
"""生成 cross-state contact sheet。

将每个状态的第一帧并排展示，便于人工检查角色身份、画风、比例、基线一致性。

示例：
    python3 generate_contact_sheet.py \
        --config /path/to/sprites-config.json \
        --output-dir /path/to/public/images/pet
"""

import argparse
import json
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cross-state contact sheet")
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

    frames: list[tuple[str, Image.Image]] = []

    # V2.1：若存在 canonical base pet，作为统一参考放在最前，便于跨状态比较
    canonical_base_path = output_dir / "canonical-base-pet.png"
    if canonical_base_path.exists():
        base_img = Image.open(canonical_base_path).convert("RGBA")
        base_img = base_img.resize((frame_width, frame_height))
        frames.append(("canonical", base_img))

    for cfg in configs:
        state = cfg["name"]
        sprite_path = output_dir / f"{state}.png"
        if not sprite_path.exists():
            continue
        img = Image.open(sprite_path)
        first_frame = img.crop((0, 0, frame_width, frame_height))
        frames.append((state, first_frame))

    if not frames:
        print("No frames found")
        return

    margin = 16
    label_height = 32
    total_width = len(frames) * (frame_width + margin) + margin
    total_height = frame_height + label_height + margin * 2
    contact = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 255))

    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(contact)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    # V2.1：统一参考辅助线（baseline 与 center line）
    bottom_offset = canonical.get("bottomOffset", 0)
    baseline_y = frame_height - bottom_offset
    center_x = frame_width // 2
    baseline_color = (220, 80, 80, 160)   # 红色 baseline
    centerline_color = (80, 120, 220, 160)  # 蓝色 center line

    for i, (state, frame) in enumerate(frames):
        x = margin + i * (frame_width + margin)
        y = margin
        contact.paste(frame, (x, y), frame)
        # baseline 参考线
        draw.line([(x, y + baseline_y), (x + frame_width, y + baseline_y)], fill=baseline_color, width=1)
        # center line 参考线
        draw.line([(x + center_x, y), (x + center_x, y + frame_height)], fill=centerline_color, width=1)
        text_bbox = draw.textbbox((0, 0), state, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_x = x + (frame_width - text_w) // 2
        text_y = y + frame_height + 8
        draw.text((text_x, text_y), state, fill=(0, 0, 0, 255), font=font)

    output_path = output_dir / "contact-sheet.png"
    contact.save(output_path, "PNG")
    print(f"contact sheet saved to {output_path}")


if __name__ == "__main__":
    main()
