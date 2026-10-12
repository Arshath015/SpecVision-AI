"""Generates the synthetic reference-ring images used by the evaluation
dataset and the frontend's bundled sample gallery.

These are programmatically drawn illustrations (simple shapes/gradients),
not photographs and not sourced from any third party -- there is no
licensing concern, but they are also not photo-realistic. Ground-truth
visible-stone counts recorded in evaluation/data/cases.json were set by
construction (we drew exactly N visible circles), so they are an exact
label for "what a human could count in this image", not a claim about
real jewelry photography.

Run with: python evaluation/generate_images.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import cv2
import numpy as np

OUT_DIR = Path(__file__).resolve().parent / "images"
FRONTEND_SAMPLES_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "sample-images"


def _band(canvas: np.ndarray, center, band_radius, band_thickness, color_bgr):
    cv2.circle(canvas, center, band_radius, color_bgr, band_thickness, lineType=cv2.LINE_AA)
    # subtle highlight arc to look metallic
    highlight = tuple(min(255, c + 60) for c in color_bgr)
    cv2.ellipse(canvas, center, (band_radius, band_radius), 0, 200, 340, highlight, max(1, band_thickness // 3))


def _center_stone(canvas: np.ndarray, center, size, color_bgr):
    pts = np.array([
        [center[0], center[1] - size],
        [center[0] + int(size * 0.75), center[1]],
        [center[0], center[1] + size],
        [center[0] - int(size * 0.75), center[1]],
    ])
    cv2.fillConvexPoly(canvas, pts, color_bgr, lineType=cv2.LINE_AA)
    cv2.circle(canvas, (center[0] - size // 4, center[1] - size // 4), max(2, size // 5), (255, 255, 255), -1, lineType=cv2.LINE_AA)


def _side_stone(canvas: np.ndarray, pos, radius, color_bgr):
    cv2.circle(canvas, pos, radius, color_bgr, -1, lineType=cv2.LINE_AA)
    cv2.circle(canvas, (pos[0] - radius // 3, pos[1] - radius // 3), max(1, radius // 3), (255, 255, 255), -1, lineType=cv2.LINE_AA)
    cv2.circle(canvas, pos, radius, (30, 30, 30), 1, lineType=cv2.LINE_AA)


def _background(size, bg_color, texture=False, seed=0):
    h, w = size
    canvas = np.full((h, w, 3), bg_color, dtype=np.uint8)
    if texture:
        rng = np.random.default_rng(seed)
        noise = rng.normal(0, 3, (h, w, 1)).astype(np.int16)
        canvas = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return canvas


def make_ring_image(
    side_count: int,
    metal_color_bgr=(40, 170, 220),
    stone_color_bgr=(230, 230, 250),
    bg_color=(195, 195, 195),
    size=(500, 700),
    band_radius=150,
    stone_radius=12,
    cluster=False,
    seed=1,
):
    h, w = size
    canvas = _background(size, bg_color, texture=True, seed=seed)
    center = (w // 2, h // 2 + 40)

    _band(canvas, center, band_radius, 26, metal_color_bgr)
    _center_stone(canvas, (center[0], center[1] - band_radius - 10), 34, stone_color_bgr)

    if side_count > 0:
        if cluster:
            # Cram stones close together on one arc segment to simulate
            # occlusion/overlap -- a harder, honestly-labeled case.
            start_angle = -40
            end_angle = 40
            for i in range(side_count):
                angle = math.radians(start_angle + (end_angle - start_angle) * i / max(side_count - 1, 1))
                r = band_radius
                x = int(center[0] + r * math.sin(angle))
                y = int(center[1] - band_radius - r * (0.08) - r * math.cos(angle) * 0 + (band_radius - r))
                pos = (int(center[0] + r * math.sin(angle)), int(center[1] - band_radius + 4))
                _side_stone(canvas, pos, stone_radius, stone_color_bgr)
        else:
            half = side_count // 2
            for side_sign, n_side in ((-1, half), (1, side_count - half)):
                for i in range(n_side):
                    angle = math.radians(25 + i * 22)
                    x = int(center[0] + side_sign * band_radius * math.sin(angle))
                    y = int(center[1] - band_radius * math.cos(angle))
                    _side_stone(canvas, (x, y), stone_radius, stone_color_bgr)
    return canvas


def save(name: str, img: np.ndarray, quality=92):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, quality] if name.endswith(".jpg") else [])
    return path


def main():
    random.seed(7)

    clear_6 = make_ring_image(6, metal_color_bgr=(40, 170, 220), seed=1)
    save("ring_clear_6stones.jpg", clear_6)

    clear_12 = make_ring_image(12, metal_color_bgr=(200, 200, 200), stone_radius=10, seed=2)
    save("ring_clear_12stones.jpg", clear_12)

    dark_8 = make_ring_image(8, metal_color_bgr=(40, 170, 220), seed=3)
    dark_8 = cv2.convertScaleAbs(dark_8, alpha=0.35, beta=-10)
    save("ring_dark_8stones.jpg", dark_8)

    bright_8 = make_ring_image(8, metal_color_bgr=(40, 170, 220), seed=4)
    bright_8 = cv2.convertScaleAbs(bright_8, alpha=1.8, beta=90)
    save("ring_overexposed_8stones.jpg", bright_8)

    blurry_10 = make_ring_image(10, metal_color_bgr=(90, 90, 230), stone_radius=9, seed=5)
    blurry_10 = cv2.GaussianBlur(blurry_10, (15, 15), 0)
    save("ring_blurry_10stones.jpg", blurry_10)

    angled_6 = make_ring_image(6, metal_color_bgr=(40, 170, 220), seed=6)
    h, w = angled_6.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), 12, 1.0)
    angled_6 = cv2.warpAffine(angled_6, matrix, (w, h), borderValue=(235, 235, 235))
    save("ring_angled_6stones.jpg", angled_6)

    occluded = make_ring_image(10, metal_color_bgr=(40, 170, 220), stone_radius=13, cluster=True, seed=7)
    save("ring_occluded_cluster.jpg", occluded)

    no_side = make_ring_image(0, metal_color_bgr=(40, 170, 220), seed=8)
    save("ring_no_sidestones.jpg", no_side)

    busy_bg = make_ring_image(8, metal_color_bgr=(90, 90, 230), bg_color=(180, 200, 170), seed=9)
    save("ring_busy_background.jpg", busy_bg)

    tiny = make_ring_image(6, metal_color_bgr=(40, 170, 220), size=(80, 100), band_radius=25, stone_radius=3, seed=10)
    save("ring_tiny_resolution.jpg", tiny)

    rose_14 = make_ring_image(14, metal_color_bgr=(120, 150, 230), stone_radius=9, seed=11)
    save("ring_rose_eternity_14stones.jpg", rose_14)

    print(f"Generated images in {OUT_DIR}")

    # Copy a representative subset into the frontend's sample gallery.
    FRONTEND_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for name in [
        "ring_clear_6stones.jpg",
        "ring_clear_12stones.jpg",
        "ring_rose_eternity_14stones.jpg",
        "ring_no_sidestones.jpg",
    ]:
        img = cv2.imread(str(OUT_DIR / name))
        cv2.imwrite(str(FRONTEND_SAMPLES_DIR / name), img)
    print(f"Copied sample subset into {FRONTEND_SAMPLES_DIR}")


if __name__ == "__main__":
    main()
