"""Kare uretimi: simulasyon durumu -> RGB numpy dizisi.

Tek bir cizici var; ciktisi ister PNG'ye yazilir (headless), ister pygame
penceresine basilir. Boylece iki mod da BIREBIR ayni goruntuyu uretir.
"""

from __future__ import annotations

import math

import numpy as np

from .font3x5 import GLYPH_H, draw_text

BG = np.array([12, 14, 20], dtype=np.uint8)
HUD_BG = np.array([20, 22, 30], dtype=np.uint8)
TEXT = np.array([200, 210, 225], dtype=np.uint8)
DIM = np.array([110, 120, 140], dtype=np.uint8)


def _hud_height(cfg) -> int:
    return (GLYPH_H + 5) * 2 if bool(cfg.get("viz.hud", True)) else 0


def frame_size(cfg) -> tuple[int, int]:
    scale = int(cfg.get("viz.scale", 4))
    return int(cfg.world.width) * scale, int(cfg.world.height) * scale + _hud_height(cfg)


def render(sim) -> np.ndarray:
    """(H, W, 3) uint8 kare uretir."""
    cfg = sim.cfg
    world = sim.world
    scale = int(cfg.get("viz.scale", 4))
    hud_h = _hud_height(cfg)
    w_px = world.width * scale
    h_px = world.height * scale

    # --- zemin: yemek yogunlugu + kapasite hayaleti ---
    food = np.clip(world.food / world.food_scale, 0.0, 1.0)
    cap = np.clip(world.food_capacity / world.food_scale, 0.0, 1.0)

    cell = np.empty((world.height, world.width, 3), dtype=np.float32)
    cell[..., 0] = BG[0] + 18.0 * cap                      # kapasite: hafif mor sis
    cell[..., 1] = BG[1] + 30.0 * cap + 165.0 * food       # yemek: yesil
    cell[..., 2] = BG[2] + 26.0 * cap + 55.0 * food

    # --- tehlike diskleri: kirmizi tul ---
    if bool(cfg.get("viz.show_hazards", True)):
        haz = np.clip(world.hazard_damage_field, 0.0, None)
        if haz.max() > 0:
            m = (haz > 0).astype(np.float32)
            cell[..., 0] = cell[..., 0] * (1 - 0.55 * m) + 175.0 * 0.55 * m
            cell[..., 1] = cell[..., 1] * (1 - 0.35 * m) + 40.0 * 0.35 * m
            cell[..., 2] = cell[..., 2] * (1 - 0.35 * m) + 55.0 * 0.35 * m

    img_world = np.repeat(np.repeat(np.clip(cell, 0, 255).astype(np.uint8), scale, axis=0), scale, axis=1)

    img = np.empty((h_px + hud_h, w_px, 3), dtype=np.uint8)
    img[hud_h:] = img_world
    if hud_h:
        img[:hud_h] = HUD_BG

    # --- ajanlar ---
    e_max = float(cfg.agents.energy.max)
    dot = max(1, scale // 2)
    for a in sim.agents:
        px = int(a.x * scale)
        py = int(a.y * scale) + hud_h
        t = min(1.0, max(0.0, a.energy / e_max))
        # dusuk enerji: soguk mavi -> yuksek enerji: sicak sari
        color = (int(70 + 185 * t), int(90 + 130 * t), int(235 - 190 * t))
        _blit(img, px, py, dot, color)
        if scale >= 5:  # bakis yonu tirnagi
            hx = int(px + math.cos(a.heading) * scale * 0.9)
            hy = int(py + math.sin(a.heading) * scale * 0.9)
            _blit(img, hx, hy, max(1, dot // 2), (color[0] // 2 + 40, color[1] // 2 + 40, color[2] // 2 + 40))

    if hud_h:
        _draw_hud(img, sim, w_px, hud_h)
    return img


def _blit(img: np.ndarray, x: int, y: int, size: int, color) -> None:
    h, w = img.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(w, x + size), min(h, y + size)
    if x1 > x0 and y1 > y0:
        img[y0:y1, x0:x1] = color


def _draw_hud(img: np.ndarray, sim, w_px: int, hud_h: int) -> None:
    row = sim.last_metrics or {}
    energy = row.get("mean_energy", 0.0)
    fill = row.get("food_fill", 0.0)
    clus = row.get("clustering", 0.0)
    div = row.get("behavior_diversity", 0.0)

    line1 = f"STEP {sim.step_index}   N {sim.population}   ENERJI {energy:.0f}"
    line2 = f"YEMEK {fill * 100:.0f}%   KUME {clus:+.2f}   CESIT {div:.3f}   SEED {sim.seed}"
    draw_text(img, line1, 4, 3, TEXT, scale=1)
    draw_text(img, line2, 4, 3 + GLYPH_H + 3, DIM, scale=1)

    # sag ust: populasyon cubugu
    cap = max(1, int(sim.cfg.agents.max_count))
    bar_w = min(160, w_px // 4)
    x0 = w_px - bar_w - 6
    frac = min(1.0, sim.population / cap)
    img[4 : 4 + 4, x0 : x0 + bar_w] = (45, 50, 62)
    img[4 : 4 + 4, x0 : x0 + max(1, int(bar_w * frac))] = (250, 200, 90)
    img[hud_h - 6 : hud_h - 2, x0 : x0 + bar_w] = (45, 50, 62)
    img[hud_h - 6 : hud_h - 2, x0 : x0 + max(1, int(bar_w * min(1.0, fill)))] = (90, 210, 120)
