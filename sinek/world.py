"""Dunya: 2B surekli duzlem + izgara tabanli kaynak/tehlike alanlari.

Ajanlar surekli (float) konumda yasar; yemek, tehlike, sicaklik ve isik
izgara alani olarak tutulur. Boylece hem akiskan hareket hem de ucuz
kaynak muhasebesi elde edilir.

Yemek kapasitesi rastgele gaussian "yamalar"dan uretilir: dunya duz degil,
zengin ve fakir bolgeleri var. Kumelenme ve kitlik rekabeti gibi emergent
olgular icin gereken uzamsal heterojenlik buradan gelir.

ALGI (onemli tasarim karari)
---------------------------
Her sinek cevresini tek tek taramak yerine, dunya adim basina BIR KEZ
bulaniklastirilmis "koku alani" ve onun gradyanini hesaplar. Sinek sadece
kendi hucresindeki degeri okur (O(1)). Bu hem 20x daha hizli hem de
gercek kemotaksise daha yakin. Tehlike alanlari sabit oldugu icin bir kez,
kurulumda hesaplanir.
"""

from __future__ import annotations

import math

import numpy as np

from .fields import (
    blur2d,
    gaussian_kernel1d,
    gradient2d,
    normalize_vector_field,
    scatter_counts,
)


class World:
    def __init__(self, cfg, rng: np.random.Generator):
        self.cfg = cfg
        w = cfg.world
        self.width = int(w.width)
        self.height = int(w.height)
        self.toroidal = bool(w.toroidal)

        self._build_food(w.food, rng)
        self._build_hazards(w.hazard, rng)
        self._build_climate(w.climate)

        # algi cekirdekleri
        self._food_kernel = gaussian_kernel1d(float(cfg.agents.senses.food_radius) / 2.0)
        self._crowd_kernel = gaussian_kernel1d(float(cfg.agents.senses.neighbor_radius) / 2.0)
        self._crowd_ref = max(1e-6, float(self._crowd_kernel.max() ** 2))
        self._food_grad_ref = self._reference_gradient()

        self.food_consumed_total = 0.0
        self.update_food_perception()
        self.update_crowd_perception(np.zeros(0), np.zeros(0))

    # ---------------------------------------------------------------- kurulum
    def _build_food(self, fc, rng: np.random.Generator) -> None:
        h, w = self.height, self.width
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cap = np.full((h, w), float(fc.background), dtype=np.float32)

        self.patch_centers: list[tuple[float, float]] = []
        r = float(fc.patch_radius)
        for _ in range(int(fc.patches)):
            px = float(rng.uniform(0, w))
            py = float(rng.uniform(0, h))
            self.patch_centers.append((px, py))
            dx = np.abs(xx - px)
            dy = np.abs(yy - py)
            if self.toroidal:
                dx = np.minimum(dx, w - dx)
                dy = np.minimum(dy, h - dy)
            cap += float(fc.patch_peak) * np.exp(-(dx * dx + dy * dy) / (2.0 * r * r))

        self.food_capacity = np.clip(cap, 0.0, None).astype(np.float32)
        self.food = (self.food_capacity * float(fc.initial_fill)).astype(np.float32)
        self.food_scale = float(max(1e-6, self.food_capacity.max()))
        self.initial_food_total = float(self.food.sum())

    def _build_hazards(self, hz, rng: np.random.Generator) -> None:
        """Tehlikeler sabit; yon/yakinlik/hasar alanlari bir kez hesaplanir."""
        self.hazards: list[tuple[float, float, float, float]] = []
        radius = float(hz.radius)
        damage = float(hz.damage)
        avoid = bool(hz.get("avoid_food_patches", True))
        for _ in range(int(hz.count)):
            hx = hy = 0.0
            for _try in range(40):
                hx = float(rng.uniform(0, self.width))
                hy = float(rng.uniform(0, self.height))
                if not avoid:
                    break
                if all(
                    math.hypot(*self.delta(hx, hy, px, py)) >= radius * 1.2
                    for px, py in self.patch_centers
                ):
                    break
            self.hazards.append((hx, hy, radius, damage))

        h, w = self.height, self.width
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        vision = float(self.cfg.agents.senses.hazard_radius)

        best_edge = np.full((h, w), np.inf, dtype=np.float32)
        dir_x = np.zeros((h, w), dtype=np.float32)
        dir_y = np.zeros((h, w), dtype=np.float32)
        self.hazard_damage_field = np.zeros((h, w), dtype=np.float32)

        for hx, hy, hr, dmg in self.hazards:
            dx = xx - hx
            dy = yy - hy
            if self.toroidal:
                dx = np.where(dx > w * 0.5, dx - w, np.where(dx < -w * 0.5, dx + w, dx))
                dy = np.where(dy > h * 0.5, dy - h, np.where(dy < -h * 0.5, dy + h, dy))
            dist = np.sqrt(dx * dx + dy * dy)
            edge = dist - hr
            closer = edge < best_edge
            best_edge = np.where(closer, edge, best_edge)
            safe = np.maximum(dist, 1e-6)
            # ajandan tehlikeye dogru birim vektor (isaret ters: dx = hucre - tehlike)
            dir_x = np.where(closer, (-dx / safe), dir_x)
            dir_y = np.where(closer, (-dy / safe), dir_y)
            self.hazard_damage_field += np.where(dist <= hr, dmg, 0.0).astype(np.float32)

        near = 1.0 - np.clip(np.maximum(best_edge, 0.0) / max(1e-6, vision), 0.0, 1.0)
        near = np.where(np.isfinite(best_edge), near, 0.0)
        self.hazard_near_field = near.astype(np.float32)
        self.hazard_dir_x = (dir_x * (near > 0)).astype(np.float32)
        self.hazard_dir_y = (dir_y * (near > 0)).astype(np.float32)

    def _build_climate(self, cl) -> None:
        h, w = self.height, self.width
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.temperature = self._gradient(cl.temperature_gradient, xx, yy, w, h)
        self.light = self._gradient(cl.light_gradient, xx, yy, w, h)

    @staticmethod
    def _gradient(mode: str, xx, yy, w: int, h: int) -> np.ndarray:
        if mode == "vertical":
            return (yy / max(1, h - 1)).astype(np.float32)
        if mode == "horizontal":
            return (xx / max(1, w - 1)).astype(np.float32)
        return np.zeros_like(xx, dtype=np.float32)

    # ------------------------------------------------------------- geometri
    def delta(self, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
        """1'den 2'ye en kisa vektor (sarmali dunyada kestirme yolu dahil)."""
        dx = x2 - x1
        dy = y2 - y1
        if self.toroidal:
            if dx > self.width * 0.5:
                dx -= self.width
            elif dx < -self.width * 0.5:
                dx += self.width
            if dy > self.height * 0.5:
                dy -= self.height
            elif dy < -self.height * 0.5:
                dy += self.height
        return dx, dy

    def move(self, x: float, y: float, dx: float, dy: float) -> tuple[float, float]:
        nx, ny = x + dx, y + dy
        if self.toroidal:
            nx %= self.width
            ny %= self.height
        else:
            nx = min(max(nx, 0.0), self.width - 1e-6)
            ny = min(max(ny, 0.0), self.height - 1e-6)
        return nx, ny

    def cell(self, x: float, y: float) -> tuple[int, int]:
        cx = int(x) % self.width if self.toroidal else min(max(int(x), 0), self.width - 1)
        cy = int(y) % self.height if self.toroidal else min(max(int(y), 0), self.height - 1)
        return cx, cy

    def random_position(self, rng: np.random.Generator) -> tuple[float, float]:
        return float(rng.uniform(0, self.width)), float(rng.uniform(0, self.height))

    # ---------------------------------------------------------------- kaynak
    def food_at(self, x: float, y: float) -> float:
        cx, cy = self.cell(x, y)
        return float(self.food[cy, cx])

    def take_food(self, x: float, y: float, amount: float) -> float:
        cx, cy = self.cell(x, y)
        available = float(self.food[cy, cx])
        taken = min(available, max(0.0, amount))
        if taken > 0.0:
            self.food[cy, cx] = available - taken
            self.food_consumed_total += taken
        return taken

    # ------------------------------------------------------------------ algi
    def _reference_gradient(self) -> float:
        """Sensor olcegi: TAM dolu bir dunyada erisilebilecek en dik gradyan.

        Sabit ve ajanlardan bagimsiz oldugu icin `food_strength` sensoru
        yorumlanabilir kalir: 1.0 = bu dunyanin verebilecegi en guclu koku izi.
        """
        blur = blur2d(self.food_capacity, self._food_kernel, self.toroidal)
        gx, gy = gradient2d(blur, self.toroidal)
        _ux, _uy, mag = normalize_vector_field(gx, gy)
        return max(1e-6, float(np.percentile(mag, 99.0)))

    def update_food_perception(self) -> None:
        """Yemek koku alani + gradyani (adim basina bir kez)."""
        blur = blur2d(self.food, self._food_kernel, self.toroidal)
        gx, gy = gradient2d(blur, self.toroidal)
        ux, uy, mag = normalize_vector_field(gx, gy)
        self.food_blur = blur
        self.food_dir_x = ux
        self.food_dir_y = uy
        self.food_grad_strength = np.clip(mag / self._food_grad_ref, 0.0, 1.0).astype(np.float32)

    def update_crowd_perception(self, xs: np.ndarray, ys: np.ndarray) -> None:
        """Ajan yogunlugu alani + gradyani (surulesme sensoru icin)."""
        counts = scatter_counts(xs, ys, self.width, self.height)
        blur = blur2d(counts, self._crowd_kernel, self.toroidal)
        gx, gy = gradient2d(blur, self.toroidal)
        ux, uy, _mag = normalize_vector_field(gx, gy)
        self.crowd_density = np.clip(blur / self._crowd_ref / 8.0, 0.0, 1.0).astype(np.float32)
        self.crowd_dir_x = ux
        self.crowd_dir_y = uy

    def sample(self, x: float, y: float, *fields: np.ndarray) -> tuple[float, ...]:
        cx, cy = self.cell(x, y)
        return tuple(float(f[cy, cx]) for f in fields)

    def hazard_damage_at(self, x: float, y: float) -> float:
        cx, cy = self.cell(x, y)
        return float(self.hazard_damage_field[cy, cx])

    # ------------------------------------------------------------------ adim
    def step(self) -> None:
        """Yemek yenilenmesi (vektorel, adim basina bir kez)."""
        fc = self.cfg.world.food
        rate = float(fc.regrowth_rate)
        cap = self.food_capacity
        if fc.regrowth_mode == "constant":
            self.food += rate * cap
        else:  # logistic + kucuk tohumlama (olu bolgelerin geri gelebilmesi icin)
            self.food += rate * self.food * (1.0 - self.food / np.maximum(cap, 1e-6))
            self.food += float(fc.seed_rate) * cap
        np.clip(self.food, 0.0, cap, out=self.food)

    # ---------------------------------------------------------------- ozetler
    @property
    def food_total(self) -> float:
        return float(self.food.sum())

    @property
    def food_capacity_total(self) -> float:
        return float(self.food_capacity.sum())
