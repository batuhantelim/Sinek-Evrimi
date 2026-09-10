"""Saf Python PNG yazici (sadece stdlib: zlib + struct).

Headless kare kaydetmenin ek bagimlilik gerektirmemesi icin var —
Pillow ya da pygame kurulu olmasa da `viz.mode: frames` calisir.
"""

from __future__ import annotations

import struct
import zlib

import numpy as np


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path: str, rgb: np.ndarray, compress_level: int = 6) -> None:
    """rgb: (H, W, 3) uint8 dizisi."""
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    h, w, _ = rgb.shape
    # her satirin basina filtre baytini (0 = None) ekle
    raw = np.zeros((h, w * 3 + 1), dtype=np.uint8)
    raw[:, 1:] = rgb.reshape(h, w * 3)
    payload = zlib.compress(raw.tobytes(), compress_level)

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        fh.write(_chunk(b"IDAT", payload))
        fh.write(_chunk(b"IEND", b""))
