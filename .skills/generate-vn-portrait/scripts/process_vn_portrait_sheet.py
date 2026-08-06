#!/usr/bin/env python3
"""Remove a flat chroma-key background and split VN portrait sheets."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
DEFAULT_KEY_COLOR = (255, 0, 255)
ALPHA_NOISE_FLOOR = 2
KEY_DOMINANCE_THRESHOLD = 24.0


def parse_hex_color(value: str) -> tuple[int, int, int]:
    match = HEX_RE.match(value.strip())
    if not match:
        raise argparse.ArgumentTypeError(f"Expected hex color like #FF00FF, got {value!r}")
    raw = match.group(1)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def color_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def smoothstep(values: np.ndarray) -> np.ndarray:
    values = np.clip(values, 0.0, 1.0)
    return values * values * (3.0 - 2.0 * values)


def infer_border_key(rgb: np.ndarray, sample_px: int) -> tuple[int, int, int]:
    h, w, _ = rgb.shape
    sample_px = max(1, min(sample_px, h // 2 or 1, w // 2 or 1))
    border = np.concatenate(
        [
            rgb[:sample_px, :, :].reshape(-1, 3),
            rgb[h - sample_px :, :, :].reshape(-1, 3),
            rgb[:, :sample_px, :].reshape(-1, 3),
            rgb[:, w - sample_px :, :].reshape(-1, 3),
        ],
        axis=0,
    )
    median = np.median(border, axis=0)
    return tuple(int(round(v)) for v in median)


def spill_channels(key: tuple[int, int, int]) -> list[int]:
    key_max = max(key)
    if key_max < 128:
        return []
    return [idx for idx, value in enumerate(key) if value >= key_max - 16 and value >= 128]


def key_dominance(rgb: np.ndarray, key: tuple[int, int, int]) -> np.ndarray:
    channels = spill_channels(key)
    if not channels:
        return np.zeros(rgb.shape[:2], dtype=np.float32)

    spill = rgb[:, :, channels]
    key_strength = spill.min(axis=2) if len(channels) > 1 else spill[:, :, 0]
    non_spill_channels = [idx for idx in range(3) if idx not in channels]
    if non_spill_channels:
        non_key_strength = rgb[:, :, non_spill_channels].max(axis=2)
    else:
        non_key_strength = np.zeros(rgb.shape[:2], dtype=np.float32)
    return key_strength - non_key_strength


def dominance_alpha(rgb: np.ndarray, key: tuple[int, int, int]) -> np.ndarray:
    dominance = key_dominance(rgb, key)
    if not spill_channels(key):
        return np.full(rgb.shape[:2], 255.0, dtype=np.float32)
    non_spill_channels = [idx for idx in range(3) if idx not in spill_channels(key)]
    if non_spill_channels:
        non_key_strength = rgb[:, :, non_spill_channels].max(axis=2)
    else:
        non_key_strength = np.zeros(rgb.shape[:2], dtype=np.float32)
    denominator = np.maximum(1.0, float(max(key)) - non_key_strength)
    alpha = 1.0 - np.clip(dominance / denominator, 0.0, 1.0)
    return np.where(dominance > 0, alpha * 255.0, 255.0)


def contract_alpha(image: Image.Image, pixels: int) -> Image.Image:
    if pixels <= 0:
        return image
    alpha = image.getchannel("A")
    for _ in range(pixels):
        alpha = alpha.filter(ImageFilter.MinFilter(3))
    image.putalpha(alpha)
    return image


def feather_alpha(image: Image.Image, radius: float) -> Image.Image:
    if radius <= 0:
        return image
    alpha = image.getchannel("A").filter(ImageFilter.GaussianBlur(radius=radius))
    image.putalpha(alpha)
    return image


def apply_chroma_key(
    image: Image.Image,
    key: tuple[int, int, int],
    transparent_threshold: float,
    opaque_threshold: float,
    despill: bool,
    edge_contract: int,
    edge_feather: float,
) -> Image.Image:
    rgba = np.array(image.convert("RGBA")).astype(np.float32)
    rgb = rgba[:, :, :3]
    input_alpha = rgba[:, :, 3]
    key_arr = np.array(key, dtype=np.float32)
    dist = np.linalg.norm(rgb - key_arr, axis=2)

    ratio = (dist - transparent_threshold) / max(1.0, opaque_threshold - transparent_threshold)
    soft_alpha = smoothstep(ratio) * 255.0
    dominance = key_dominance(rgb, key)
    key_like = (dist <= 32.0) | (dominance >= KEY_DOMINANCE_THRESHOLD)
    output_alpha = np.where(key_like, np.minimum(soft_alpha, dominance_alpha(rgb, key)), 255.0)
    output_alpha = output_alpha * (input_alpha / 255.0)
    output_alpha = np.where((output_alpha > 0) & (output_alpha <= ALPHA_NOISE_FLOOR), 0.0, output_alpha)

    if despill:
        channels = spill_channels(key)
        non_spill_channels = [idx for idx in range(3) if idx not in channels]
        if channels and non_spill_channels:
            anchor = rgb[:, :, non_spill_channels].max(axis=2)
            cap = np.maximum(0.0, anchor - 1.0)
            cleanup_mask = key_like & (output_alpha < 252.0)
            for idx in channels:
                rgb[:, :, idx] = np.where(
                    cleanup_mask & (rgb[:, :, idx] > cap),
                    cap,
                    rgb[:, :, idx],
                )

    rgb = np.where(output_alpha[:, :, None] == 0, 0, rgb)

    rgba[:, :, :3] = np.clip(rgb, 0, 255)
    rgba[:, :, 3] = np.clip(output_alpha, 0, 255)
    result = Image.fromarray(rgba.astype(np.uint8), "RGBA")
    result = contract_alpha(result, edge_contract)
    result = feather_alpha(result, edge_feather)
    return result


def split_bounds(width: int, height: int, rows: int, cols: int) -> list[tuple[int, int, int, int]]:
    bounds: list[tuple[int, int, int, int]] = []
    for row in range(rows):
        y0 = round(height * row / rows)
        y1 = round(height * (row + 1) / rows)
        for col in range(cols):
            x0 = round(width * col / cols)
            x1 = round(width * (col + 1) / cols)
            bounds.append((x0, y0, x1, y1))
    return bounds


def alpha_bbox(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    alpha = np.array(image.convert("RGBA"))[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def expand_bbox(
    bbox: tuple[int, int, int, int],
    padding: int,
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return max(0, x0 - padding), max(0, y0 - padding), min(width, x1 + padding), min(height, y1 + padding)


def edge_touch_flags(image: Image.Image, threshold: int) -> list[str]:
    alpha = np.array(image.convert("RGBA"))[:, :, 3]
    flags: list[str] = []
    if np.any(alpha[0, :] > threshold):
        flags.append("top")
    if np.any(alpha[-1, :] > threshold):
        flags.append("bottom")
    if np.any(alpha[:, 0] > threshold):
        flags.append("left")
    if np.any(alpha[:, -1] > threshold):
        flags.append("right")
    return flags


def alpha_coverage(image: Image.Image, threshold: int) -> float:
    alpha = np.array(image.convert("RGBA"))[:, :, 3]
    return float(np.count_nonzero(alpha > threshold) / alpha.size)


def corner_alpha_values(image: Image.Image) -> list[int]:
    rgba = image.convert("RGBA")
    w, h = rgba.size
    return [
        rgba.getpixel((0, 0))[3],
        rgba.getpixel((w - 1, 0))[3],
        rgba.getpixel((0, h - 1))[3],
        rgba.getpixel((w - 1, h - 1))[3],
    ]


def parse_labels(raw: str | None, count: int) -> list[str]:
    if not raw:
        return [f"portrait-{i + 1:02d}" for i in range(count)]
    labels = [item.strip() for item in raw.split(",") if item.strip()]
    if len(labels) != count:
        raise ValueError(f"--labels must contain exactly {count} comma-separated labels; got {len(labels)}")
    safe_labels = []
    for label in labels:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._-")
        safe_labels.append(safe or "portrait")
    return safe_labels


def write_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process(args: argparse.Namespace) -> dict:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = Image.open(input_path).convert("RGBA")
    rgb = np.array(source)[:, :, :3]
    key = infer_border_key(rgb, args.border_sample) if args.auto_key else args.key_color
    alpha_sheet = apply_chroma_key(
        source,
        key=key,
        transparent_threshold=args.transparent_threshold,
        opaque_threshold=args.opaque_threshold,
        despill=not args.no_despill,
        edge_contract=args.edge_contract,
        edge_feather=args.edge_feather,
    )

    sheet_alpha_path = output_dir / args.sheet_name
    alpha_sheet.save(sheet_alpha_path)

    cell_bounds = split_bounds(alpha_sheet.width, alpha_sheet.height, args.rows, args.cols)
    labels = parse_labels(args.labels, len(cell_bounds))
    portraits = []
    warnings: list[str] = []
    sheet_corner_alpha = corner_alpha_values(alpha_sheet)
    if any(value > args.alpha_threshold for value in sheet_corner_alpha):
        warnings.append(
            "sheet: corners are not transparent after cleanup; raw background is probably not flat #FF00FF"
        )

    for index, (label, bounds) in enumerate(zip(labels, cell_bounds), start=1):
        cell = alpha_sheet.crop(bounds)
        bbox = alpha_bbox(cell, args.alpha_threshold)
        empty = bbox is None
        if empty:
            crop = cell
            final_bbox = None
            warnings.append(f"{label}: no opaque subject detected")
        elif args.trim:
            padded_bbox = expand_bbox(bbox, args.padding, cell.width, cell.height)
            crop = cell.crop(padded_bbox)
            final_bbox = padded_bbox
        else:
            crop = cell
            final_bbox = bbox

        edge_flags = edge_touch_flags(cell, args.alpha_threshold)
        if edge_flags:
            warnings.append(f"{label}: subject touches cell edge: {', '.join(edge_flags)}")

        output_path = output_dir / f"{label}.png"
        crop.save(output_path)

        portraits.append(
            {
                "id": label,
                "index": index,
                "row": math.ceil(index / args.cols),
                "col": ((index - 1) % args.cols) + 1,
                "image": output_path.name,
                "source_cell": list(bounds),
                "output_size": [crop.width, crop.height],
                "alpha_bbox": list(final_bbox) if final_bbox else None,
                "alpha_coverage": round(alpha_coverage(cell, args.alpha_threshold), 6),
                "edge_touch": edge_flags,
                "empty": empty,
            }
        )

    manifest = {
        "source": str(input_path),
        "sheet_alpha": sheet_alpha_path.name,
        "rows": args.rows,
        "cols": args.cols,
        "key_color": color_to_hex(key),
        "transparent_threshold": args.transparent_threshold,
        "opaque_threshold": args.opaque_threshold,
        "alpha_threshold": args.alpha_threshold,
        "edge_contract": args.edge_contract,
        "edge_feather": args.edge_feather,
        "despill": not args.no_despill,
        "mode": "trim" if args.trim else "keep-cell-canvas",
        "sheet_corner_alpha": sheet_corner_alpha,
        "portraits": portraits,
        "warnings": warnings,
    }
    write_manifest(output_dir / args.manifest_name, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Raw generated portrait sheet image.")
    parser.add_argument("--output-dir", required=True, help="Directory for transparent outputs and manifest.")
    parser.add_argument("--rows", type=int, required=True, help="Number of equal sheet rows.")
    parser.add_argument("--cols", type=int, required=True, help="Number of equal sheet columns.")
    parser.add_argument("--labels", help="Comma-separated output ids, one per cell in row-major order.")
    parser.add_argument("--key-color", type=parse_hex_color, default=DEFAULT_KEY_COLOR, help="Explicit chroma key color. Defaults to #FF00FF for VN portraits.")
    parser.add_argument("--auto-key", choices=["border"], help="Infer key color from image border for exceptional salvage/debug runs.")
    parser.add_argument("--border-sample", type=int, default=8, help="Border thickness in pixels for auto key sampling.")
    parser.add_argument("--transparent-threshold", type=float, default=14.0, help="RGB distance treated as transparent.")
    parser.add_argument("--opaque-threshold", type=float, default=190.0, help="RGB distance treated as fully opaque.")
    parser.add_argument("--alpha-threshold", type=int, default=8, help="Alpha threshold for bbox and edge-touch QC.")
    parser.add_argument("--edge-contract", type=int, default=1, help="Shrink the visible alpha matte by this many pixels to remove color fringe.")
    parser.add_argument("--edge-feather", type=float, default=0.25, help="Blur the alpha matte slightly after contraction to soften cutout edges.")
    parser.add_argument("--padding", type=int, default=24, help="Transparent padding added around trimmed portraits.")
    parser.add_argument("--trim", action="store_true", help="Trim each portrait to alpha bbox plus padding.")
    parser.add_argument("--keep-cell-canvas", action="store_true", help="Keep split cells at full cell size. This is the default.")
    parser.add_argument("--no-despill", action="store_true", help="Disable conservative edge despill.")
    parser.add_argument("--sheet-name", default="sheet-alpha.png", help="Filename for the cleaned alpha sheet.")
    parser.add_argument("--manifest-name", default="manifest.json", help="Filename for manifest JSON.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.rows <= 0 or args.cols <= 0:
        parser.error("--rows and --cols must be positive")
    if args.padding < 0:
        parser.error("--padding must be non-negative")
    if args.edge_contract < 0 or args.edge_contract > 16:
        parser.error("--edge-contract must be between 0 and 16")
    if args.edge_feather < 0 or args.edge_feather > 64:
        parser.error("--edge-feather must be between 0 and 64")
    if args.trim and args.keep_cell_canvas:
        parser.error("--trim and --keep-cell-canvas are mutually exclusive")
    manifest = process(args)
    print(json.dumps({"manifest": args.manifest_name, "portraits": len(manifest["portraits"]), "warnings": manifest["warnings"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
