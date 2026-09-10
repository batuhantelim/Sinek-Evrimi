"""Skaler alan yardimcilari: bulaniklastirma (blur) ve gradyan.

Sensorleri ajan basina dongu yerine alan tabanli hesaplamak icin var.
Yemek alanini bir kez bulaniklastirip gradyanini almak, her sinegin
cevresini tek tek taramasindan ~20x daha hizli ve daha duzgun bir
"koku izi" (chemotaxis) modeli veriyor.
"""

from __future__ import annotations

import numpy as np


def gaussian_kernel1d(sigma: float, radius: int | None = None) -> np.ndarray:
    sigma = max(1e-3, float(sigma))
    r = int(radius if radius is not None else max(1, round(3.0 * sigma)))
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-(x * x) / (2.0 * sigma * sigma))
    return (k / k.sum()).astype(np.float32)


def blur2d(a: np.ndarray, k: np.ndarray, wrap: bool) -> np.ndarray:
    """Ayrilabilir (separable) gaussian blur. wrap=True ise sarmali kenar."""
    r = (k.size - 1) // 2
    mode = "wrap" if wrap else "edge"

    p = np.pad(a, ((0, 0), (r, r)), mode=mode)
    out = np.zeros_like(a, dtype=np.float32)
    w = a.shape[1]
    for i, kv in enumerate(k):
        out += kv * p[:, i : i + w]

    p = np.pad(out, ((r, r), (0, 0)), mode=mode)
    res = np.zeros_like(a, dtype=np.float32)
    h = a.shape[0]
    for i, kv in enumerate(k):
        res += kv * p[i : i + h, :]
    return res


def gradient2d(a: np.ndarray, wrap: bool) -> tuple[np.ndarray, np.ndarray]:
    """Merkezi fark gradyani: (d/dx, d/dy). Yon = artan degere dogru."""
    if wrap:
        gx = (np.roll(a, -1, axis=1) - np.roll(a, 1, axis=1)) * 0.5
        gy = (np.roll(a, -1, axis=0) - np.roll(a, 1, axis=0)) * 0.5
    else:
        gx = np.gradient(a, axis=1)
        gy = np.gradient(a, axis=0)
    return gx.astype(np.float32), gy.astype(np.float32)


def normalize_vector_field(gx: np.ndarray, gy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(birim x, birim y, buyukluk)"""
    mag = np.sqrt(gx * gx + gy * gy)
    safe = np.maximum(mag, 1e-9)
    return (gx / safe).astype(np.float32), (gy / safe).astype(np.float32), mag.astype(np.float32)


def scatter_counts(xs: np.ndarray, ys: np.ndarray, width: int, height: int) -> np.ndarray:
    """Ajan konumlarini hucre sayimlarina rasterize eder."""
    grid = np.zeros((height, width), dtype=np.float32)
    if xs.size:
        ix = np.clip(xs.astype(np.int32), 0, width - 1)
        iy = np.clip(ys.astype(np.int32), 0, height - 1)
        np.add.at(grid, (iy, ix), 1.0)
    return grid
