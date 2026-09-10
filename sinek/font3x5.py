"""Kucucuk 3x5 bitmap font — kare uzerine HUD yazisi basmak icin.

Pillow bagimliligindan kacinmak icin elle yazildi. Sadece buyuk harf,
rakam ve birkac sembol.
"""

from __future__ import annotations

import numpy as np

_GLYPHS = {
    "A": "010 101 111 101 101", "B": "110 101 110 101 110",
    "C": "011 100 100 100 011", "D": "110 101 101 101 110",
    "E": "111 100 110 100 111", "F": "111 100 110 100 100",
    "G": "011 100 101 101 011", "H": "101 101 111 101 101",
    "I": "111 010 010 010 111", "J": "001 001 001 101 010",
    "K": "101 101 110 101 101", "L": "100 100 100 100 111",
    "M": "101 111 111 101 101", "N": "101 111 111 111 101",
    "O": "010 101 101 101 010", "P": "110 101 110 100 100",
    "Q": "010 101 101 111 011", "R": "110 101 110 101 101",
    "S": "011 100 010 001 110", "T": "111 010 010 010 010",
    "U": "101 101 101 101 011", "V": "101 101 101 101 010",
    "W": "101 101 111 111 101", "X": "101 101 010 101 101",
    "Y": "101 101 010 010 010", "Z": "111 001 010 100 111",
    "0": "111 101 101 101 111", "1": "010 110 010 010 111",
    "2": "110 001 010 100 111", "3": "111 001 011 001 111",
    "4": "101 101 111 001 001", "5": "111 100 110 001 110",
    "6": "011 100 111 101 111", "7": "111 001 010 010 010",
    "8": "111 101 111 101 111", "9": "111 101 111 001 110",
    " ": "000 000 000 000 000", ":": "000 010 000 010 000",
    ".": "000 000 000 000 010", "/": "001 001 010 100 100",
    "-": "000 000 111 000 000", "%": "101 001 010 100 101",
    "+": "000 010 111 010 000", "=": "000 111 000 111 000",
    "*": "000 101 010 101 000", "?": "110 001 010 000 010",
}

FONT: dict[str, np.ndarray] = {
    ch: np.array([[c == "1" for c in row] for row in pat.split(" ")], dtype=bool)
    for ch, pat in _GLYPHS.items()
}
GLYPH_W, GLYPH_H = 3, 5


def draw_text(img: np.ndarray, text: str, x: int, y: int, color, scale: int = 1) -> int:
    """img uzerine metin basar, bir sonraki x konumunu dondurur."""
    color = np.asarray(color, dtype=np.uint8)
    h, w = img.shape[:2]
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            cx += (GLYPH_W + 1) * scale
            continue
        for gy in range(GLYPH_H):
            for gx in range(GLYPH_W):
                if not glyph[gy, gx]:
                    continue
                px, py = cx + gx * scale, y + gy * scale
                if 0 <= px < w and 0 <= py < h:
                    img[py : py + scale, px : px + scale] = color
        cx += (GLYPH_W + 1) * scale
    return cx
