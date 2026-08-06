#!/usr/bin/env python3
"""参数化宠物 Sprite Sheet 处理脚本（V2.3 Asset Reliability Patch）。

V2.3 升级点（仅修复图片后处理，不改变产品/确认/性格/接入逻辑）：
- Alpha-first：先检查源图是否已含有效透明通道，有则直接保留、跳过 RGB 抠背景；
- 明确背景模式：preserve-alpha / chroma / auto（auto 必须暂停报告，禁止默认采样四角抠除）；
- 正确羽化方向 0→255（基于到外部背景的距离），已有 alpha 时绝不覆盖原始 alpha；
- 自适应身体色填充（同时支持黑色角色与白色角色）；
- 真正统一角色尺寸：以 canonical/idle neutral frame 为参考，对整个状态统一缩放，保持基线与中心。

支持通过 JSON 配置传入：
- 输入源文件路径、输出目录
- 状态名称、帧数、fps、loop
- bg_mode（auto|preserve-alpha|chroma）、bg_color（chroma 显式背景色）
- bg_threshold、feather_band、bottom_offset
- canonical_state（尺寸参考状态，默认 idle）、scale（仅 QA 修复用的状态级校正因子）
"""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


@dataclass
class SpriteConfig:
    name: str
    source: str
    frame_count: int
    fps: float
    loop: bool
    bg_mode: str = "auto"            # auto | preserve-alpha | chroma
    bg_color: tuple[int, int, int] | None = None
    bg_threshold: int = 35
    feather_band: int = 20
    bottom_offset: int = 40
    canonical_state: str = "idle"    # 角色尺寸参考状态
    scale: float = 1.0               # 仅 QA 修复用的状态级校正因子


@dataclass
class FrameGeometry:
    width: int
    height: int
    bbox: tuple[int, int, int, int]
    center_x: float
    bottom_anchor: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process pet sprite sheets (V2.3)")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    parser.add_argument("--output-dir", required=True, help="Directory to write processed sprites and pet-sprites.json")
    return parser.parse_args()


def load_config(config_path: str) -> list[SpriteConfig]:
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("states", [])
    configs = []
    for item in raw:
        bg = item.get("bg_color")
        bg_color = tuple(bg) if isinstance(bg, (list, tuple)) and len(bg) == 3 else None
        configs.append(SpriteConfig(
            name=item["name"],
            source=item["source"],
            frame_count=item["frame_count"],
            fps=item.get("fps", 4.0),
            loop=item.get("loop", True),
            bg_mode=item.get("bg_mode", "auto"),
            bg_color=bg_color,
            bg_threshold=item.get("bg_threshold", 35),
            feather_band=item.get("feather_band", 20),
            bottom_offset=item.get("bottom_offset", 40),
            canonical_state=item.get("canonical_state", "idle"),
            scale=item.get("scale", 1.0),
        ))
    return configs


# ---------------- Alpha-first 与背景模式 ----------------

def has_valid_alpha(img: Image.Image, min_transparent_ratio: float = 0.01) -> bool:
    """源图是否包含有效的透明通道（存在显著比例的半透明/透明像素）。"""
    if img.mode != "RGBA":
        return False
    alpha = np.array(img.split()[-1])
    return (alpha < 250).sum() > alpha.size * min_transparent_ratio


def edges_mostly_transparent(img: Image.Image, ratio: float = 0.5) -> bool:
    """画布四条边是否主要由透明像素构成。"""
    alpha = np.array(img.convert("RGBA").split()[-1])
    h, w = alpha.shape
    edge = np.concatenate([alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1]])
    return (edge < 250).mean() > ratio


def detect_uniform_border_color(img: Image.Image, tol: int = 6) -> tuple[int, int, int] | None:
    """若四条边为统一纯色，返回该颜色；否则返回 None。"""
    rgb = np.array(img.convert("RGB"))
    border = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]]).astype(int)
    mean = border.mean(axis=0)
    if np.abs(border - mean).max() <= tol:
        return tuple(int(x) for x in mean)
    return None


def resolve_bg_mode(img: Image.Image, cfg: SpriteConfig) -> str:
    """严格优先级：有效 alpha → preserve-alpha；明确纯色背景 → chroma；无法确定 → auto（暂停）。"""
    if has_valid_alpha(img) and edges_mostly_transparent(img):
        return "preserve-alpha"
    if cfg.bg_mode == "chroma":
        if cfg.bg_color is not None:
            return "chroma"
        return "auto"
    if cfg.bg_mode == "preserve-alpha":
        return "preserve-alpha" if has_valid_alpha(img) else "auto"
    # auto：仅当存在统一纯色边框时才升级为 chroma，否则保持 auto（暂停）
    if cfg.bg_color is not None:
        return "chroma"
    border = detect_uniform_border_color(img)
    if border is not None:
        cfg.bg_color = border
        return "chroma"
    return "auto"


# ---------------- chroma 背景抠除（安全） ----------------

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


def edge_connected_bg(passable: np.ndarray) -> np.ndarray:
    """从画布四条边出发的 flood-fill，只标记与边缘连通的背景像素。"""
    h, w = passable.shape
    bg_mask = np.zeros((h, w), dtype=bool)
    stack = []
    for x in range(w):
        for y in (0, h - 1):
            if passable[y, x]:
                stack.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if passable[y, x] and not bg_mask[y, x]:
                stack.append((y, x))
    while stack:
        y, x = stack.pop()
        if bg_mask[y, x]:
            continue
        bg_mask[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not bg_mask[ny, nx] and passable[ny, nx]:
                stack.append((ny, nx))
    return bg_mask


def remove_background(img: Image.Image, bg: tuple[int, int, int], threshold: int, feather: int) -> Image.Image:
    """chroma 模式：仅删除与边缘连通的外部背景，羽化方向 0→255，内部用自适应身体色填充。

    自适应身体色取自“明显非背景色”的不透明像素中位数，因此同时支持黑色角色与白色角色。
    """
    img = img.convert("RGBA")
    arr = np.array(img).astype(np.float64)
    rgb = arr[:, :, :3]
    dist = np.sqrt(((rgb - np.array(bg, dtype=np.float64)) ** 2).sum(axis=2))

    t = min(threshold, otsu_threshold(dist))
    t = max(t, 8)
    passable = dist < t
    bg_mask = edge_connected_bg(passable)

    # 羽化：到外部背景的距离 → alpha 0(边缘)→255(主体内部)
    dist_to_bg = ndimage.distance_transform_edt(~bg_mask)
    alpha = np.clip(dist_to_bg / max(feather, 1), 0, 1) * 255.0

    # 恢复被轮廓包围的内部区域（被轮廓包围的背景色区域 + 透明空洞）
    opaque_mask = alpha > 0
    enclosed_bg = passable & ~bg_mask
    bridged = ndimage.binary_dilation(opaque_mask, iterations=6)
    filled = ndimage.binary_fill_holes(bridged)
    holes = filled & ~opaque_mask
    fill_mask = enclosed_bg | holes

    rgb_out = rgb.copy()
    if fill_mask.any():
        body = opaque_mask & ~enclosed_bg & (dist >= t)  # 明显非背景色（任意亮度）
        body_color = np.median(rgb[body], axis=0) if body.any() else np.array([246.0, 247.0, 250.0])
        rgb_out[fill_mask] = body_color
        alpha[fill_mask] = 255.0

    return Image.fromarray(np.dstack([rgb_out, alpha]).astype(np.uint8), "RGBA")


# ---------------- 帧提取与几何 ----------------

def find_content_columns(img: Image.Image) -> list[tuple[int, int]]:
    alpha = img.split()[-1]
    col_has_content = [any(alpha.getpixel((x, y)) > 10 for y in range(img.height)) for x in range(img.width)]
    segments = []
    start = None
    for i, has in enumerate(col_has_content):
        if has and start is None:
            start = i
        if not has and start is not None:
            segments.append((start, i))
            start = None
    if start is not None:
        segments.append((start, img.width))
    return segments


def crop_frame(img: Image.Image, left: int, right: int) -> Image.Image:
    frame = img.crop((left, 0, right, img.height))
    bbox = frame.getbbox()
    if bbox:
        return frame.crop(bbox)
    return frame


def extract_frames(img: Image.Image, cfg: SpriteConfig, mode: str) -> list[Image.Image]:
    print(f"[{cfg.name}] source size: {img.size}, bg_mode -> {mode}")
    if mode == "preserve-alpha":
        transparent = img.convert("RGBA")
    elif mode == "chroma":
        transparent = remove_background(img, cfg.bg_color, cfg.bg_threshold, cfg.feather_band)
    else:
        raise RuntimeError(f"[{cfg.name}] bg_mode=auto 无法确定背景，已暂停，请检查源素材或显式指定 bg_mode/bg_color")

    segments = find_content_columns(transparent)
    print(f"[{cfg.name}] detected {len(segments)} content segments, expected {cfg.frame_count}")
    if len(segments) != cfg.frame_count:
        print(f"[{cfg.name}] fallback to equal width slicing")
        frame_w = img.width // cfg.frame_count
        segments = [(i * frame_w, (i + 1) * frame_w) for i in range(cfg.frame_count)]
    return [crop_frame(transparent, l, r) for l, r in segments]


def compute_frame_geometry(frame: Image.Image) -> FrameGeometry:
    bbox = frame.getbbox()
    if not bbox:
        return FrameGeometry(width=0, height=0, bbox=(0, 0, 0, 0), center_x=0, bottom_anchor=0)
    l, t, r, b = bbox
    return FrameGeometry(width=r - l, height=b - t, bbox=bbox, center_x=(l + r) / 2, bottom_anchor=float(b))


# ---------------- canonical body scale ----------------

def body_height(frame: Image.Image) -> int:
    bbox = frame.getbbox()
    return (bbox[3] - bbox[1]) if bbox else 0


def build_canonical_frame_spec(
    all_frames: dict[str, list[Image.Image]],
    canonical_body_height: int,
    bottom_offset: int,
    padding_ratio: float = 0.05,
) -> dict:
    max_width = max((f.width for fs in all_frames.values() for f in fs if f.width > 0), default=0)
    max_height = max((f.height for fs in all_frames.values() for f in fs if f.height > 0), default=0)
    target_w = int(max(max_width, canonical_body_height * 0.5) * (1 + padding_ratio * 2))
    target_h = int(max_height * (1 + padding_ratio * 2)) + bottom_offset
    target_w += target_w % 2
    target_h += target_h % 2
    return {
        "frameWidth": target_w,
        "frameHeight": target_h,
        "anchor": "bottom-center",
        "anchorX": target_w // 2,
        "anchorY": target_h - bottom_offset,
        "bottomOffset": bottom_offset,
        "canonicalBodyHeight": canonical_body_height,
    }


def build_sprite_sheet(name: str, frames: list[Image.Image], frame_spec: dict, bottom_offset: int) -> Image.Image:
    target_w = frame_spec["frameWidth"]
    target_h = frame_spec["frameHeight"]
    sheet = Image.new("RGBA", (target_w * len(frames), target_h), (0, 0, 0, 0))
    anchor_y = target_h - bottom_offset
    for i, f in enumerate(frames):
        if f.width == 0 or f.height == 0:
            continue
        x = i * target_w + (target_w - f.width) // 2
        y = anchor_y - f.height
        sheet.paste(f, (x, y), f)
    return sheet


def main():
    args = parse_args()
    configs = load_config(args.config)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 解析背景模式 + 提取帧
    frames_by_state: dict[str, list[Image.Image]] = {}
    mode_by_state: dict[str, str] = {}
    for cfg in configs:
        src_path = Path(cfg.source)
        if not src_path.exists():
            print(f"Source not found, skipping: {src_path}")
            continue
        src = Image.open(src_path)
        mode = resolve_bg_mode(src, cfg)
        if mode == "auto":
            print(f"[{cfg.name}] ⚠ bg_mode=auto：无法确定背景，已暂停该状态，请检查源素材或显式指定 bg_mode/bg_color")
            continue
        frames_by_state[cfg.name] = extract_frames(src, cfg, mode)
        mode_by_state[cfg.name] = mode

    if not frames_by_state:
        print("No frames extracted, aborting.")
        return

    # 2. canonical body scale：以 canonical_state 的 neutral frame 为参考
    ref_state = next((c.canonical_state for c in configs if c.name in frames_by_state), None)
    if ref_state is None or ref_state not in frames_by_state:
        ref_state = next(iter(frames_by_state))
    canonical_body_height = body_height(frames_by_state[ref_state][0])
    print(f"[global] canonical reference state={ref_state}, body_height={canonical_body_height}")

    # 3. 对每个状态整体统一缩放（canonical_body_height / 该状态 neutral body height）
    scaled_frames: dict[str, list[Image.Image]] = {}
    state_scale: dict[str, float] = {}
    for cfg in configs:
        if cfg.name not in frames_by_state:
            continue
        frames = frames_by_state[cfg.name]
        neutral_h = body_height(frames[0]) if frames else 0
        if neutral_h > 0:
            s = canonical_body_height / neutral_h * cfg.scale
        else:
            s = cfg.scale
        state_scale[cfg.name] = s
        scaled = []
        for f in frames:
            if f.width > 0 and f.height > 0 and abs(s - 1.0) > 1e-3:
                f = f.resize((max(1, int(round(f.width * s))), max(1, int(round(f.height * s)))), Image.LANCZOS)
            scaled.append(f)
        scaled_frames[cfg.name] = scaled

    # 4. canonical frame spec
    bottom_offset = configs[0].bottom_offset
    canonical = build_canonical_frame_spec(scaled_frames, canonical_body_height, bottom_offset)
    print(f"[global] canonical frame size {canonical['frameWidth']}x{canonical['frameHeight']}")

    metadata: dict[str, dict] = {"canonical": canonical}
    for cfg in configs:
        if cfg.name not in scaled_frames:
            continue
        frames = scaled_frames[cfg.name]
        sheet = build_sprite_sheet(cfg.name, frames, canonical, cfg.bottom_offset)
        output = output_dir / f"{cfg.name}.png"
        sheet.save(output, "PNG")
        print(f"[{cfg.name}] output {output}, frames={len(frames)}, scale={state_scale[cfg.name]:.4f}, bg_mode={mode_by_state[cfg.name]}")
        metadata[cfg.name] = {
            "src": f"/images/pet/{cfg.name}.png",
            "frameCount": len(frames),
            "frameWidth": canonical["frameWidth"],
            "frameHeight": canonical["frameHeight"],
            "fps": cfg.fps,
            "loop": cfg.loop,
            "scale": state_scale[cfg.name],
            "bgMode": mode_by_state[cfg.name],
        }

    meta_path = output_dir / "pet-sprites.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"metadata saved to {meta_path}")


if __name__ == "__main__":
    main()