"""Genom: kalitsal davranis parametreleri (+ ileride sinir agi agirliklari).

Faz 1'de tum ajanlar ayni genomun kopyasini tasir ve `evolution.enabled: false`
oldugu icin mutasyon uygulanmaz -> klonlar. Faz 2'de tek yapilacak sey
config'te `evolution.enabled: true` demek; altyapi hazir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Genome:
    """Kalitsal materyal.

    params : isimli davranis parametreleri (reflex beyin bunlari okur)
    weights: serbest agirlik vektoru — reflex beyin kullanmaz, ileride
             kucuk bir recurrent aga baglanacak (bkz. sinek/brains/base.py)
    """

    params: dict[str, float]
    weights: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float32))
    lineage: int = 0  # kacinci nesil torun

    # --- kopya / mutasyon ---------------------------------------------
    def copy(self) -> "Genome":
        return Genome(dict(self.params), self.weights.copy(), self.lineage)

    def child(self, cfg, rng: np.random.Generator) -> "Genome":
        """Ureme sirasinda cagrilir. Mutasyon kapaliysa saf klon dondurur."""
        g = self.copy()
        g.lineage = self.lineage + 1
        if cfg.get("evolution.enabled", False):
            g.mutate(cfg, rng)
        return g

    def mutate(self, cfg, rng: np.random.Generator) -> None:
        rate = float(cfg.get("evolution.mutation_rate", 0.0))
        sigma = float(cfg.get("evolution.mutation_sigma", 0.0))
        bounds = cfg.get("evolution.param_bounds", {})
        bounds = bounds.to_dict() if hasattr(bounds, "to_dict") else dict(bounds or {})

        for name in list(self.params):
            if rng.random() < rate:
                self.params[name] += float(rng.normal(0.0, sigma))
                lo_hi = bounds.get(name)
                if lo_hi:
                    self.params[name] = float(np.clip(self.params[name], lo_hi[0], lo_hi[1]))

        if self.weights.size:
            mask = rng.random(self.weights.shape) < rate
            self.weights = self.weights + mask * rng.normal(0.0, sigma, self.weights.shape)
            self.weights = self.weights.astype(np.float32)

    # --- olcum ---------------------------------------------------------
    def vector(self, order: list[str] | None = None) -> np.ndarray:
        """Cesitlilik metrikleri icin sabit sirali sayisal temsil."""
        names = order if order is not None else sorted(self.params)
        return np.array([self.params[n] for n in names], dtype=np.float64)


def founder_genome(cfg) -> Genome:
    """config.genome.params'tan kurucu genomu uretir."""
    params = cfg.get("genome.params", {})
    params = params.to_dict() if hasattr(params, "to_dict") else dict(params)
    return Genome({k: float(v) for k, v in params.items()})
