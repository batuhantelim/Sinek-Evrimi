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

    def candidates(self, agent, radius: float, world, k: int):
        """radius icindeki EN YAKIN k ajan, mesafeye gore sirali.

        Faz 6 partner secimi icin: ajan yalnizca en yakinla degil, bir ADAY
        HAVUZU icinden secer. `nearest` bunun k=1 hali gibi gorunur ama sicak
        yol oldugu icin ayri tutulur — k=1'de liste kurmak bosuna maliyet.

        Beraberlikte kucuk id once gelir (determinizm).
        """
        x, y = agent.x, agent.y
        span = int(math.ceil(radius / self.cell))
        cx, cy = self._key(x, y)
        r2 = radius * radius
        found = []
        for gy in range(cy - span, cy + span + 1):
            for gx in range(cx - span, cx + span + 1):
                if self.toroidal:
                    key = (gx % self.nx, gy % self.ny)
                else:
                    if not (0 <= gx < self.nx and 0 <= gy < self.ny):
                        continue
                    key = (gx, gy)
                for other in self.buckets.get(key, ()):
                    if other.id == agent.id:
                        continue
                    dx, dy = world.delta(x, y, other.x, other.y)
                    d2 = dx * dx + dy * dy
                    if d2 <= r2:
                        found.append((d2, other.id, other))
        if not found:
            return []
        found.sort(key=lambda t: (t[0], t[1]))
        return [(t[2], t[0]) for t in found[:k]]

    def nearest(self, agent, radius: float, world):
        """radius icindeki EN YAKIN ajan (kendisi haric) ya da None.

        Liste kurup siralamaktan kacinir: Faz 3'te her ajan icin her adimda
        cagrildigi icin sicak yol burasi. Beraberlikte kucuk id kazanir
        (determinizm).
        """
        x, y = agent.x, agent.y
        span = int(math.ceil(radius / self.cell))
        cx, cy = self._key(x, y)
        best = None
        best_d2 = radius * radius
        for gy in range(cy - span, cy + span + 1):
            for gx in range(cx - span, cx + span + 1):
                if self.toroidal:
                    key = (gx % self.nx, gy % self.ny)
                else:
                    if not (0 <= gx < self.nx and 0 <= gy < self.ny):
                        continue
                    key = (gx, gy)
                for other in self.buckets.get(key, ()):
                    if other.id == agent.id:
                        continue
                    dx, dy = world.delta(x, y, other.x, other.y)
                    d2 = dx * dx + dy * dy
                    if d2 < best_d2 or (d2 == best_d2 and best is not None and other.id < best.id):
                        best, best_d2 = other, d2
        return best

    def count_label(self, agent, radius: float, world, label) -> int:
        """radius icinde AYNI etikete sahip kac komsu var (kendisi haric).

        `query` liste kurup siralar; bu sicak yolda adim x ajan basina
        cagrildigi icin yalnizca SAYAR — tahsis ve siralama yok.
        Determinizm: sayim sirasi sonucu etkilemez.
        """
        x, y = agent.x, agent.y
        span = int(math.ceil(radius / self.cell))
        cx, cy = self._key(x, y)
        r2 = radius * radius
        aid = agent.id
        n = 0
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
                for o in bucket:
                    if o.id == aid or o.crowd_label != label:
                        continue
                    dx, dy = world.delta(x, y, o.x, o.y)
                    if dx * dx + dy * dy <= r2:
                        n += 1
        return n

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
