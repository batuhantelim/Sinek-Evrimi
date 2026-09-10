#!/usr/bin/env python3
"""metrics.csv -> cok panelli PNG grafik (matplotlib gerektirmez).

Kullanim:
    python tools/plot_metrics.py runs/faz1
    python tools/plot_metrics.py runs/faz1 --cols population,mean_energy,food_fill
    python tools/plot_metrics.py runs/a runs/b --cols population   # kosum karsilastirma
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.font3x5 import GLYPH_H, draw_text  # noqa: E402
from sinek.pngwrite import write_png  # noqa: E402

BG = (14, 16, 22)
PANEL = (22, 25, 33)
GRID = (44, 49, 62)
TEXT = (205, 214, 230)
DIM = (120, 130, 150)
SERIES = [(250, 200, 90), (90, 210, 140), (120, 170, 255), (245, 120, 120), (200, 140, 245)]

DEFAULT_COLS = "population,mean_energy,food_fill,clustering,behavior_diversity"
GENERATION_COLS = "mean_fitness,max_fitness,mean_food_eaten,survivors,weight_diversity"


def read_csv(path: str) -> dict[str, np.ndarray]:
    if not os.path.exists(path):
        raise SystemExit(f"CSV bulunamadi: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"bos CSV: {path}")
    out = {}
    for key in rows[0]:
        out[key] = np.array([float(r[key]) for r in rows], dtype=np.float64)
    return out


def _bin(y: np.ndarray, width: int) -> np.ndarray:
    if y.size <= width:
        return y
    idx = np.linspace(0, y.size, width + 1).astype(int)
    return np.array([y[a:b].mean() if b > a else y[min(a, y.size - 1)] for a, b in zip(idx[:-1], idx[1:])])


def _line(img, x0, y0, x1, y1, color):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    h, w = img.shape[:2]
    for i in range(n + 1):
        x = int(round(x0 + (x1 - x0) * i / n))
        y = int(round(y0 + (y1 - y0) * i / n))
        if 0 <= x < w and 0 <= y < h:
            img[y, x] = color


def plot(
    runs: list[str],
    cols: list[str],
    out: str,
    width: int = 900,
    panel_h: int = 150,
    csv_name: str = "metrics.csv",
    x_col: str = "step",
) -> str:
    data = []
    for run in runs:
        path = run if run.endswith(".csv") else os.path.join(run, csv_name)
        data.append((os.path.basename(os.path.dirname(path) or path), read_csv(path)))

    pad_l, pad_r, pad_t = 46, 12, 16
    header = 22
    height = header + len(cols) * (panel_h + pad_t) + 20
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = BG

    title = "SINEK EVRIMI  /  " + "  VS  ".join(name.upper() for name, _ in data)
    draw_text(img, title[:110], 8, 7, TEXT)

    plot_w = width - pad_l - pad_r
    for pi, col in enumerate(cols):
        top = header + pi * (panel_h + pad_t) + pad_t
        img[top : top + panel_h, pad_l : pad_l + plot_w] = PANEL

        series = [(name, _bin(d[col], plot_w)) for name, d in data if col in d]
        if not series:
            draw_text(img, f"{col}: SUTUN YOK", pad_l + 6, top + 6, DIM)
            continue
        lo = min(float(s.min()) for _, s in series)
        hi = max(float(s.max()) for _, s in series)
        if hi - lo < 1e-9:
            hi = lo + 1.0
        pad = (hi - lo) * 0.08
        lo, hi = lo - pad, hi + pad

        for frac in (0.0, 0.5, 1.0):  # yatay klavuzlar
            gy = int(top + panel_h - 1 - frac * (panel_h - 1))
            img[gy, pad_l : pad_l + plot_w] = GRID

        for si, (name, s) in enumerate(series):
            color = SERIES[si % len(SERIES)]
            ys = (top + panel_h - 1 - (s - lo) / (hi - lo) * (panel_h - 1)).astype(int)
            xs = (pad_l + np.linspace(0, plot_w - 1, s.size)).astype(int)
            for i in range(1, s.size):
                _line(img, xs[i - 1], ys[i - 1], xs[i], ys[i], color)
            if len(series) > 1:
                draw_text(img, name[:14], pad_l + 6 + si * 70, top + 5, color)

        draw_text(img, col.upper()[:26], pad_l + 6, top + panel_h - GLYPH_H - 5, TEXT)
        draw_text(img, f"{hi:.4g}"[:9], 4, top - 1, DIM)
        draw_text(img, f"{lo:.4g}"[:9], 4, top + panel_h - GLYPH_H - 1, DIM)

    axis = data[0][1].get(x_col)
    label = f"{x_col} 0 - {int(axis[-1])}" if axis is not None and axis.size else x_col
    draw_text(img, label.upper(), pad_l, height - 14, DIM)
    write_png(out, img)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="metrics.csv -> PNG grafik")
    ap.add_argument("runs", nargs="+", help="runs/<name> dizini ya da dogrudan .csv yolu")
    ap.add_argument("--cols", default=DEFAULT_COLS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument(
        "--generations",
        action="store_true",
        help="metrics.csv yerine generations.csv ciz (nesil bazli evrim egrileri)",
    )
    ap.add_argument("--x", default=None, help="x ekseni etiketi icin sutun (varsayilan: step)")
    args = ap.parse_args(argv)

    csv_name = "generations.csv" if args.generations else "metrics.csv"
    x_col = args.x or ("generation" if args.generations else "step")
    if args.generations and args.cols == DEFAULT_COLS:
        args.cols = GENERATION_COLS

    default_name = "generations.png" if args.generations else "metrics.png"
    out = args.out or os.path.join(
        args.runs[0] if os.path.isdir(args.runs[0]) else ".", default_name
    )
    cols = [c.strip() for c in args.cols.split(",") if c.strip()]
    print("yazildi:", plot(args.runs, cols, out, width=args.width, csv_name=csv_name, x_col=x_col))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
