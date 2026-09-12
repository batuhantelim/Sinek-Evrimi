"""Dogal avci: hareketli, ortak, gruptan bagimsiz tehdit.

TASARIM KARARI — SURU DAVRANISI KODLANMAZ
----------------------------------------
Avci adim basina YALNIZCA BIR hedefe vurur ve sonra bekler (cooldown).
Bundan dogal olarak SEYRELTME (dilution) cikar: N kisilik bir kumede
vurulan olma olasiligin 1/N'dir. Yani "avci gelince gruplas" diye bir
kural YOK; gruplasma karli hale gelir, secilim onu bulursa bulur.

Avci GRUPTAN BAGIMSIZDIR: hedefi yalnizca mesafeye gore secer, soyisme
bakmaz. Belirli bir soyu hedefleseydi grup dusmanligini elle kurmus
olurduk — olculmek istenen sey tam da bu yuzden kodlanamaz.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Predator:
    x: float
    y: float
    heading: float
    cooldown: int = 0
    kills: int = 0
    strikes: int = 0


class PredatorPack:
    """Avci surusu. Ajan sirasi gibi burada da sira sabittir (determinizm)."""

    def __init__(self, cfg, world, rng):
        pr = cfg.rules.predator
        self.enabled = bool(pr.enabled)
        self.speed = float(pr.speed)
        self.vision = float(pr.vision)
        self.strike_radius = float(pr.strike_radius)
        self.damage = float(pr.damage)
        self.cooldown_steps = int(pr.cooldown)
        self.turn_rate = float(pr.turn_rate)
        self.sense_radius = float(cfg.get("agents.senses.predator_radius", 20.0))
        self.world = world
        self.predators: list[Predator] = []
        if not self.enabled:
            return
        for _ in range(int(pr.count)):
            x, y = world.random_position(rng)
            self.predators.append(Predator(x, y, float(rng.uniform(0, 2 * math.pi))))

    # ------------------------------------------------------------------
    def step(self, agents) -> tuple[int, int]:
        """Avcilari hareket ettirir ve vurusları uygular.

        (vurus sayisi, oldurme sayisi) dondurur. Olum muhasebesi simulasyonun
        olum adiminda yapilir; burada yalnizca enerji dusulur.
        """
        if not self.enabled or not agents:
            return 0, 0
        world = self.world
        strikes = kills = 0
        for p in self.predators:
            if p.cooldown > 0:
                p.cooldown -= 1

            target = self._nearest(p, agents)
            if target is not None:
                dx, dy = world.delta(p.x, p.y, target.x, target.y)
                want = math.atan2(dy, dx)
                # Yumusak donus: avci da ani yon degistiremesin
                diff = (want - p.heading + math.pi) % (2 * math.pi) - math.pi
                p.heading += max(-self.turn_rate, min(self.turn_rate, diff))

            p.x, p.y = world.move(
                p.x, p.y, math.cos(p.heading) * self.speed, math.sin(p.heading) * self.speed
            )

            if p.cooldown > 0 or target is None:
                continue
            dx, dy = world.delta(p.x, p.y, target.x, target.y)
            if dx * dx + dy * dy <= self.strike_radius * self.strike_radius:
                target.energy -= self.damage
                target.predator_hits += 1
                p.strikes += 1
                p.cooldown = self.cooldown_steps
                strikes += 1
                if target.energy <= 0.0:
                    target.death_cause = "predator"
                    p.kills += 1
                    kills += 1
        return strikes, kills

    def _nearest(self, p: Predator, agents):
        """Menzildeki en yakin ajan. SOYISME BAKMAZ — yalnizca mesafe.

        Beraberlikte kucuk id kazanir (determinizm).
        """
        best = None
        best_d2 = self.vision * self.vision
        for a in agents:
            dx, dy = self.world.delta(p.x, p.y, a.x, a.y)
            d2 = dx * dx + dy * dy
            if d2 < best_d2 or (d2 == best_d2 and best is not None and a.id < best.id):
                best, best_d2 = a, d2
        return best

    # ------------------------------------------------------------------
    def signal(self, x: float, y: float) -> tuple[float, float, float]:
        """Ajan icin: (en yakin avciya birim yon x, y, 0..1 yakinlik)."""
        if not self.enabled:
            return 0.0, 0.0, 0.0
        best_d = float("inf")
        bx = by = 0.0
        for p in self.predators:
            dx, dy = self.world.delta(x, y, p.x, p.y)
            d = math.hypot(dx, dy)
            if d < best_d:
                best_d = d
                bx, by = (dx / d, dy / d) if d > 1e-9 else (0.0, 0.0)
        if best_d > self.sense_radius:
            return 0.0, 0.0, 0.0
        return bx, by, 1.0 - best_d / max(1e-6, self.sense_radius)

    @property
    def total_strikes(self) -> int:
        return sum(p.strikes for p in self.predators)

    @property
    def total_kills(self) -> int:
        return sum(p.kills for p in self.predators)
