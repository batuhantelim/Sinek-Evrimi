"""Komsu sorgulari icin basit uzamsal hash izgarasi.

Faz 1'de sadece 'crowd' sensoru icin gerekiyor; Faz 3'te paylasma/saldirma
etkilesimleri de bunun uzerinden calisacak. O(n) kurulum, O(1) sorgu.
"""

from __future__ import annotations

import math
from collections import defaultdict


class SpatialHash:
    def __init__(self, width: float, height: float, cell: float, toroidal: bool):
        self.cell = max(1e-6, float(cell))
        self.nx = max(1, int(math.ceil(width / self.cell)))
        self.ny = max(1, int(math.ceil(height / self.cell)))
        self.toroidal = toroidal
        self.buckets: dict[tuple[int, int], list] = defaultdict(list)

    def build(self, agents) -> None:
        self.buckets.clear()
        for a in agents:
            self.buckets[self._key(a.x, a.y)].append(a)

    def _key(self, x: float, y: float) -> tuple[int, int]:
        return int(x / self.cell) % self.nx, int(y / self.cell) % self.ny

    def query(self, x: float, y: float, radius: float, world, exclude_id: int = -1) -> list:
        """radius icindeki ajanlar (kendisi haric), deterministik sirada."""
        span = int(math.ceil(radius / self.cell))
        cx, cy = self._key(x, y)
        out = []
        r2 = radius * radius
        for gy in range(cy - span, cy + span + 1):
            for gx in range(cx - span, cx + span + 1):
                if self.toroidal:
                    key = (gx % self.nx, gy % self.ny)
                else:
                    if not (0 <= gx < self.nx and 0 <= gy < self.ny):
                        continue
                    key = (gx, gy)
                bucket = self.buckets.get(key)
                if not bucket:
                    continue
                for a in bucket:
                    if a.id == exclude_id:
                        continue
                    dx, dy = world.delta(x, y, a.x, a.y)
                    if dx * dx + dy * dy <= r2:
                        out.append(a)
        out.sort(key=lambda a: a.id)  # determinizm garantisi
        return out
