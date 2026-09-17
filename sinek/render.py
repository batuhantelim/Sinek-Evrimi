"""Kare uretimi: simulasyon durumu -> RGB numpy dizisi.

Tek bir cizici var; ciktisi ister PNG'ye yazilir (headless), ister pygame
penceresine basilir. Boylece iki mod da BIREBIR ayni goruntuyu uretir.
"""

from __future__ import annotations

import math

import numpy as np

from .lineage import label_key

from .font3x5 import GLYPH_H, draw_text

BG = np.array([12, 14, 20], dtype=np.uint8)
HUD_BG = np.array([20, 22, 30], dtype=np.uint8)
TEXT = np.array([200, 210, 225], dtype=np.uint8)
DIM = np.array([110, 120, 140], dtype=np.uint8)


# En kalabalik soylara elle secilmis, birbirinden acikca ayrilan renkler.
# Yuzlerce soya otomatik ton atamak (altin oran vb.) ekranda ayirt edilemeyen
# bir konfeti uretiyordu; asil soru "akrabalar kumeleniyor mu" oldugu icin
# baskin birkac soyun okunabilir olmasi, hepsinin benzersiz olmasindan onemli.
LINEAGE_PALETTE = [
    (255, 90, 80),    # kirmizi
    (90, 210, 255),   # camgobegi
    (250, 215, 80),   # sari
    (200, 120, 255),  # mor
    (110, 235, 130),  # yesil
    (255, 155, 70),   # turuncu
    (120, 140, 255),  # mavi
    (255, 130, 195),  # pembe
]
OTHER_LINEAGE = (135, 140, 150)  # geri kalan tum soylar: notr gri


def lineage_colors(agents, top_n: int = len(LINEAGE_PALETTE)) -> dict[int, tuple]:
    """En kalabalik `top_n` soya palet rengi, digerlerine gri atar."""
    counts: dict[int, int] = {}
    for a in agents:
        key = label_key(a.genome.surname, getattr(a.genome, "surname2", -1))
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    return {name: LINEAGE_PALETTE[i] for i, (name, _n) in enumerate(ranked)}


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

    # --- sosyal olaylar (ajanlarin ALTINA cizilir ki noktalar ustte kalsin) ---
    if bool(cfg.get("viz.show_share", True)):
        events = [(e, True) for e in getattr(sim, "share_events", ())]
        events += [(e, False) for e in getattr(sim, "attack_events", ())]
        for (x1, y1, x2, y2, kin), is_share in events:
            dx, dy = world.delta(x1, y1, x2, y2)
            if math.hypot(dx, dy) > world.width * 0.25:
                continue  # sarmali dunyada ekrani boydan boya kesen cizgi cizme
            if is_share:  # paylasim: akrabaya parlak yesil, yabanciya soluk
                col = (170, 255, 190) if kin else (80, 150, 175)
            else:         # saldiri: akrabaya parlak kirmizi, yabanciya soluk
                col = (255, 140, 120) if kin else (190, 80, 70)
            _line(
                img,
                int(x1 * scale), int(y1 * scale) + hud_h,
                int((x1 + dx) * scale), int((y1 + dy) * scale) + hud_h,
                col,
            )

    # --- ajanlar ---
    e_max = float(cfg.agents.energy.max)
    by_lineage = str(cfg.get("viz.color_by", "energy")) == "lineage"
    dot = max(2, scale // 2 + 1) if by_lineage else max(1, scale // 2)
    palette = lineage_colors(sim.agents) if by_lineage else {}
    for a in sim.agents:
        px = int(a.x * scale)
        py = int(a.y * scale) + hud_h
        t = min(1.0, max(0.0, a.energy / e_max))
        if by_lineage:
            # ton = soyisim (kimlik), parlaklik = enerji (durum).
            # Alt sinir yuksek tutuldu: ac bir sinek sonuk olsun ama rengi
            # hala okunabilsin.
            r, g, b = palette.get(
                label_key(a.genome.surname, getattr(a.genome, "surname2", -1)),
                OTHER_LINEAGE)
            k = 0.60 + 0.40 * t
            color = (int(r * k), int(g * k), int(b * k))
        else:
            # dusuk enerji: soguk mavi -> yuksek enerji: sicak sari
            color = (int(70 + 185 * t), int(90 + 130 * t), int(235 - 190 * t))
        _blit(img, px, py, dot, color)
        if scale >= 5:  # bakis yonu tirnagi
            hx = int(px + math.cos(a.heading) * scale * 0.9)
            hy = int(py + math.sin(a.heading) * scale * 0.9)
            _blit(img, hx, hy, max(1, dot // 2), (color[0] // 2 + 40, color[1] // 2 + 40, color[2] // 2 + 40))

    # --- avcilar: ajanlardan belirgin sekilde buyuk ve kirmizi ---
    pack = getattr(sim, "predators", None)
    if pack is not None and getattr(pack, "enabled", False):
        size = max(3, scale + 2)
        for p in pack.predators:
            px = int(p.x * scale) - size // 2
            py = int(p.y * scale) + hud_h - size // 2
            # bekleme suresindeki avci soluk: tehdit anlik degil
            col = (255, 60, 60) if p.cooldown == 0 else (150, 60, 70)
            _blit(img, px, py, size, col)
            hx = int(px + math.cos(p.heading) * size)
            hy = int(py + math.sin(p.heading) * size)
            _blit(img, hx, hy, max(2, size // 2), col)

    if hud_h:
        _draw_hud(img, sim, w_px, hud_h)
    return img


def _line(img: np.ndarray, x0: int, y0: int, x1: int, y1: int, color) -> None:
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    h, w = img.shape[:2]
    for i in range(n + 1):
        x = int(round(x0 + (x1 - x0) * i / n))
        y = int(round(y0 + (y1 - y0) * i / n))
        if 0 <= x < w and 0 <= y < h:
            img[y, x] = color


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

    line1 = (
        f"STEP {sim.step_index}   N {sim.population}   ENERJI {energy:.0f}   "
        f"YEMEK {fill * 100:.0f}%   KUME {clus:+.2f}   SOY {row.get('lineage_count', 0)}"
        f"/{row.get('lineage_effective', 0.0):.1f}"
    )
    pack = getattr(sim, "predators", None)
    if pack is not None and getattr(pack, "enabled", False):
        line1 += f"   AVCI {len(pack.predators)} OLDURME {pack.total_kills}"
    if getattr(sim, "_share_on", False):
        line2 = (
            f"PAYLAS IC {row.get('coop_in_group', 0.0) * 100:5.2f}% "
            f"DIS {row.get('coop_out_group', 0.0) * 100:5.2f}%   "
            f"SALDIR IC {row.get('attack_in_group', 0.0) * 100:5.2f}% "
            f"DIS {row.get('attack_out_group', 0.0) * 100:5.2f}%   SEED {sim.seed}"
        )
    else:
        line2 = (
            f"CESIT {row.get('behavior_diversity', 0.0):.3f}   "
            f"AGIRLIK {row.get('weight_diversity', 0.0):.3f}   SEED {sim.seed}"
        )
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
