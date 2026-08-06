#!/usr/bin/env python3
"""宠物 Sprite 几何 + 素材完整性 QA 脚本（V2.3）。

在原有几何一致性检测（size popping / baseline / center / 裁切 / 越界）基础上，
新增「素材完整性 QA」：比较处理前(源)与处理后(输出)的面积、主体高度、主体宽度、
主要连通区域，以及头部/耳朵/身体内部 alpha 覆盖率，并检测透明洞、黑色线稿、
白色贴纸外壳、异常边缘膨胀。主体面积或高度灾难性减少(≥50%)直接判 blocker。

示例：
    python3 geometry_qa.py \
        --config /path/to/sprites-config.json \
        --output-dir /path/to/public/images/pet \
        --report /path/to/geometry-report.json
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


@dataclass
class FrameGeometry:
    state: str
    frame_index: int
    bbox: tuple[int, int, int, int]
    width: int
    height: int
    center_x: float
    bottom_anchor: float
    area: int
    anchor_x: float
    anchor_y: float


@dataclass
class Blocker:
    type: str
    severity: str
    message: str
    state: str | None
    frame_index: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pet sprite geometry + asset integrity QA")
    parser.add_argument("--config", required=True, help="Path to sprites-config.json")
    parser.add_argument("--output-dir", required=True, help="Directory containing processed sprites")
    parser.add_argument("--report", required=True, help="Path to write geometry report JSON")
    parser.add_argument("--size-threshold", type=float, default=0.10)
    parser.add_argument("--baseline-threshold", type=float, default=0.05)
    parser.add_argument("--center-threshold", type=float, default=0.05)
    return parser.parse_args()


def load_sprite_config(config_path: str) -> list[dict]:
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        return raw.get("states", [])
    return raw


def load_frame(img: Image.Image, frame_index: int, frame_width: int, frame_height: int) -> Image.Image:
    left = frame_index * frame_width
    return img.crop((left, 0, left + frame_width, frame_height))


def compute_frame_geometry(state, frame_index, frame, frame_width, frame_height, bottom_offset) -> FrameGeometry:
    bbox = frame.getbbox()
    if not bbox:
        return FrameGeometry(state, frame_index, (0, 0, 0, 0), 0, 0, 0, 0, 0, frame_width / 2, frame_height - bottom_offset)
    l, t, r, b = bbox
    return FrameGeometry(state, frame_index, bbox, r - l, b - t, (l + r) / 2, float(b), (r - l) * (b - t), frame_width / 2, frame_height - bottom_offset)


def check_intra_state(frames: list[FrameGeometry], frame_height: int) -> list[Blocker]:
    blockers = []
    for i, g in enumerate(frames):
        if g.width == 0 or g.height == 0:
            blockers.append(Blocker("empty_frame", "blocker", f"第 {i} 帧为空帧", g.state, i))
            continue
        if g.bbox[3] > frame_height:
            blockers.append(Blocker("edge_overflow", "blocker", f"第 {i} 帧主体超出 frame 下边界", g.state, i))
        if i > 0:
            prev = frames[i - 1]
            if prev.height > 0 and abs(g.height - prev.height) / prev.height > 0.10:
                blockers.append(Blocker("size_popping", "warning", f"第 {i-1} -> {i} 帧高度变化 {abs(g.height - prev.height) / prev.height:.1%}", g.state, i))
            if abs(g.bottom_anchor - prev.bottom_anchor) / frame_height > 0.05:
                blockers.append(Blocker("baseline_jump", "warning", f"第 {i-1} -> {i} 帧 baseline 变化 {abs(g.bottom_anchor - prev.bottom_anchor) / frame_height:.1%}", g.state, i))
            if g.width > 0 and prev.width > 0 and abs(g.center_x - prev.center_x) / max(g.width, prev.width) > 0.05:
                blockers.append(Blocker("center_shift", "warning", f"第 {i-1} -> {i} 帧 centerX 偏移 {abs(g.center_x - prev.center_x) / max(g.width, prev.width):.1%}", g.state, i))
    return blockers


def check_cross_state(state_frames: dict[str, list[FrameGeometry]], frame_width: int, frame_height: int) -> list[Blocker]:
    blockers = []
    states = list(state_frames.keys())
    if len(states) < 2:
        return blockers
    base_frames = {s: frames[0] for s, frames in state_frames.items() if frames}
    first_state = states[0]
    first = base_frames.get(first_state)
    if not first or first.height == 0:
        return blockers
    for s, frame in base_frames.items():
        if s == first_state or frame.height == 0:
            continue
        if abs(frame.height - first.height) / first.height > 0.10:
            blockers.append(Blocker("cross_state_size_popping", "blocker", f"{first_state} -> {s} 主体高度变化 {abs(frame.height - first.height) / first.height:.1%}", s, 0))
        if abs(frame.bottom_anchor - first.bottom_anchor) / frame_height > 0.05:
            blockers.append(Blocker("cross_state_baseline_jump", "blocker", f"{first_state} -> {s} baseline 变化 {abs(frame.bottom_anchor - first.bottom_anchor) / frame_height:.1%}", s, 0))
        if abs(frame.center_x - first.center_x) / frame_width > 0.05:
            blockers.append(Blocker("cross_state_center_shift", "blocker", f"{first_state} -> {s} centerX 偏移 {abs(frame.center_x - first.center_x) / frame_width:.1%}", s, 0))
        ratio = frame.width / frame.height if frame.height > 0 else 0
        first_ratio = first.width / first.height if first.height > 0 else 0
        if first_ratio > 0 and abs(ratio - first_ratio) / first_ratio > 0.10:
            blockers.append(Blocker("cross_state_silhouette_mismatch", "blocker", f"{first_state} -> {s} 轮廓宽高比变化 {abs(ratio - first_ratio) / first_ratio:.1%}", s, 0))
    return blockers


# ---------------- 素材完整性 QA ----------------

def region_opaque_ratio(opaque: np.ndarray, x0, y0, x1, y1) -> float:
    h, w = opaque.shape
    x0, x1 = max(0, int(x0)), min(w, int(x1))
    y0, y1 = max(0, int(y0)), min(h, int(y1))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    region = opaque[y0:y1, x0:x1]
    return float(region.mean()) if region.size else 0.0


def otsu_threshold(values: np.ndarray) -> int:
    flat = values.ravel()
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))
    total = flat.size
    sum_total = np.sum(np.arange(256) * hist)
    sum_b = 0.0
    w_b = 0.0
    max_var = -1.0
    threshold = 0
    for i in range(256):
        w_b += hist[i]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += i * hist[i]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > max_var:
            max_var = var
            threshold = i
    return threshold


def source_foreground(src_neutral: Image.Image | None, bg_color, threshold: int):
    """计算源帧主体前景掩码：有真实 alpha 用 alpha，否则用与背景色的距离（与 remove_background 一致）。"""
    if src_neutral is None:
        return None
    rgba = src_neutral.convert("RGBA")
    alpha = np.array(rgba.split()[-1])
    if (alpha < 250).mean() > 0.01:
        return alpha > 10
    if bg_color is None:
        return None
    rgb = np.array(rgba)[:, :, :3].astype(np.float64)
    dist = np.sqrt(((rgb - np.array(bg_color, dtype=np.float64)) ** 2).sum(axis=2))
    t = max(min(threshold, otsu_threshold(dist)), 8)
    return dist >= t


def check_interior_alpha(state: str, frame: Image.Image, geo: FrameGeometry, min_ratio: float = 0.5) -> list[Blocker]:
    """采样主体内部关键区域的不透明覆盖率，防止白色身体/耳朵被误抠透明。"""
    blockers = []
    if geo.width == 0 or geo.height == 0:
        return blockers
    l, t, r, b = geo.bbox
    alpha = np.array(frame.convert("RGBA").split()[-1])
    opaque = alpha > 200
    cx = (l + r) / 2
    regions = {
        "head": (cx - 0.225 * geo.width, t, cx + 0.225 * geo.width, t + 0.30 * geo.height, 0.3),
        "body": (cx - 0.275 * geo.width, t + 0.40 * geo.height, cx + 0.275 * geo.width, t + 0.80 * geo.height, 0.4),
        "left_ear": (l, t, l + 0.35 * geo.width, t + 0.45 * geo.height, 0.1),
        "right_ear": (r - 0.35 * geo.width, t, r, t + 0.45 * geo.height, 0.1),
    }
    for name, (x0, y0, x1, y1, thresh) in regions.items():
        f = region_opaque_ratio(opaque, x0, y0, x1, y1)
        if f < thresh:
            blockers.append(Blocker("interior_transparency", "blocker",
                f"{name} 区域不透明覆盖率={f:.2f}（<{thresh}），主体内部疑似被误抠透明", state, geo.frame_index))
    return blockers


def load_source_neutral(cfg: dict) -> Image.Image | None:
    """加载源 spritesheet 的 neutral frame（frame 0）。"""
    src_path = cfg.get("source")
    if not src_path or not Path(src_path).exists():
        return None
    src = Image.open(src_path)
    frame_count = max(int(cfg.get("frame_count", 1)), 1)
    fw = src.width // frame_count
    return src.crop((0, 0, fw, src.height))


def check_asset_integrity(state: str, src_neutral: Image.Image | None, out_frames: list[Image.Image],
                          geos: list[FrameGeometry], scale: float, bg_color, threshold: int) -> list[Blocker]:
    """比较源与输出的面积/高度/宽度，并检测透明洞、黑色线稿、白色外壳、边缘膨胀。"""
    blockers = []
    src_opaque = source_foreground(src_neutral, bg_color, threshold)
    src_area = src_body_h = src_body_w = 0
    if src_opaque is not None:
        src_area = int(src_opaque.sum())
        rows = src_opaque.any(axis=1)
        cols = src_opaque.any(axis=0)
        src_body_h = int(rows.sum())
        src_body_w = int(cols.sum())

    for i, (frame, geo) in enumerate(zip(out_frames, geos)):
        arr = np.array(frame.convert("RGBA"))
        out_alpha = arr[:, :, 3]
        out_opaque = out_alpha > 10
        out_rgb = arr[:, :, :3].astype(int)
        out_area = int(out_opaque.sum())
        rows = out_opaque.any(axis=1)
        cols = out_opaque.any(axis=0)
        out_body_h = int(rows.sum())
        out_body_w = int(cols.sum())

        if src_area > 0:
            expected = src_area * (scale ** 2)
            if out_area < 0.5 * expected:
                blockers.append(Blocker("area_loss", "blocker",
                    f"主体面积处理后仅剩 {out_area / expected * 100:.0f}%（灾难性减少），疑似角色被误抠", state, i))
            if out_area > 1.5 * expected:
                blockers.append(Blocker("edge_dilation", "blocker",
                    f"主体面积膨胀至 {out_area / expected * 100:.0f}%，疑似异常边缘膨胀/白色外壳", state, i))
        if src_body_h > 0:
            expected_h = src_body_h * scale
            if out_body_h < 0.5 * expected_h:
                blockers.append(Blocker("height_loss", "blocker",
                    f"主体高度处理后仅剩 {out_body_h / expected_h * 100:.0f}%（灾难性减少）", state, i))
        if src_body_w > 0:
            expected_w = src_body_w * scale
            if out_body_w < 0.5 * expected_w:
                blockers.append(Blocker("width_loss", "blocker",
                    f"主体宽度处理后仅剩 {out_body_w / expected_w * 100:.0f}%（灾难性减少）", state, i))

        # 主体内部 alpha 覆盖率（头部/耳朵/身体）
        blockers.extend(check_interior_alpha(state, frame, geo))

        # 角色内部透明洞（棋盘格穿透）：仅真正全透明(alpha=0)的内部区域，排除羽化半透明边缘
        enclosed = ndimage.binary_fill_holes(out_opaque) & ~out_opaque
        holes = enclosed & (out_alpha == 0)
        if int(holes.sum()) > 200:
            blockers.append(Blocker("interior_holes", "blocker",
                f"角色内部出现 {int(holes.sum())} 个透明洞（棋盘格穿透）", state, i))

        # 黑色线稿（排除正常实心黑色角色：仅当黑色像素主要构成细轮廓环时才判定）
        black = out_opaque & (out_rgb.max(axis=2) < 120)
        if int(black.sum()) > 500:
            black_border = black & ndimage.binary_dilation(~out_opaque, iterations=1)
            if int(black_border.sum()) > 0.5 * int(black.sum()):
                blockers.append(Blocker("black_lineart", "blocker",
                    f"出现 {int(black.sum())} 个不透明深色像素且主要构成轮廓环，疑似黑色线稿", state, i))

        # 白色贴纸外壳：边缘不透明白色环，且内部非白（排除正常白色角色）
        border_opaque = out_opaque & ndimage.binary_dilation(~out_opaque, iterations=1)
        interior_opaque = out_opaque & ~border_opaque
        border_white = border_opaque & (out_rgb.min(axis=2) > 220)
        interior_white = interior_opaque & (out_rgb.min(axis=2) > 220)
        if int(border_white.sum()) > 800 and int(interior_white.sum()) < int(border_white.sum()) * 0.3:
            blockers.append(Blocker("white_shell", "blocker",
                f"轮廓边缘出现 {int(border_white.sum())} 个不透明白色像素且内部非白，疑似白色贴纸外壳", state, i))
    return blockers


def main():
    args = parse_args()
    configs = load_sprite_config(args.config)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

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

    state_frames: dict[str, list[FrameGeometry]] = {}
    state_out_images: dict[str, list[Image.Image]] = {}
    all_blockers: list[Blocker] = []

    for cfg in configs:
        state = cfg["name"]
        sprite_path = output_dir / f"{state}.png"
        if not sprite_path.exists():
            continue
        img = Image.open(sprite_path)
        frame_count = cfg.get("frame_count", metadata.get(state, {}).get("frameCount", 0))
        bottom_offset = cfg.get("bottom_offset", 40)
        scale = float(metadata.get(state, {}).get("scale", 1.0))

        frames_geo = []
        out_images = []
        for i in range(frame_count):
            frame = load_frame(img, i, frame_width, frame_height)
            out_images.append(frame)
            frames_geo.append(compute_frame_geometry(state, i, frame, frame_width, frame_height, bottom_offset))

        state_frames[state] = frames_geo
        state_out_images[state] = out_images
        all_blockers.extend(check_intra_state(frames_geo, frame_height))

        # 素材完整性 QA：源 neutral vs 输出
        src_neutral = load_source_neutral(cfg)
        bg_color = cfg.get("bg_color")
        bg_color = tuple(bg_color) if isinstance(bg_color, (list, tuple)) and len(bg_color) == 3 else None
        all_blockers.extend(check_asset_integrity(state, src_neutral, out_images, frames_geo, scale, bg_color, cfg.get("bg_threshold", 35)))

    all_blockers.extend(check_cross_state(state_frames, frame_width, frame_height))

    report = {
        "canonical": canonical,
        "states": {
            state: [{"frameIndex": g.frame_index, "bbox": g.bbox, "width": g.width, "height": g.height,
                     "centerX": g.center_x, "bottomAnchor": g.bottom_anchor, "area": g.area}
                    for g in frames]
            for state, frames in state_frames.items()
        },
        "blockers": [{"type": b.type, "severity": b.severity, "message": b.message,
                      "state": b.state, "frameIndex": b.frame_index} for b in all_blockers],
        "blockerCount": len([b for b in all_blockers if b.severity == "blocker"]),
        "warningCount": len([b for b in all_blockers if b.severity == "warning"]),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"geometry report saved to {report_path}")
    print(f"blockers: {report['blockerCount']}, warnings: {report['warningCount']}")
    if report["blockerCount"] > 0:
        print("BLOCKERS DETECTED, do not proceed without fixing failed states")


if __name__ == "__main__":
    main()