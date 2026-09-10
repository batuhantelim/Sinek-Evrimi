"""Genom: kalitsal davranis parametreleri + sinir agi agirliklari.

Iki bolum var, cunku iki beyin backend'i var:

* `params` — isimli davranis katsayilari. `reflex` beyni bunlari okur.
  `rnn` beyni sadece `wander`'i (kesif gurultusu olcegi) kullanir.
* `weights` — serbest agirlik vektoru. `rnn` beyni bunlardan kurulur;
  uzunlugu backend'in `genome_size()` bildirimine gore belirlenir.

Faz 1'de mutasyon kapaliydi (klonlar). Faz 2'de `evolution.enabled: true`
ile aciliyor: her dogumda gaussian mutasyon uygulaniyor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .brains import genome_size_for


@dataclass
class Genome:
    """Kalitsal materyal."""

    params: dict[str, float]
    weights: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float32))
    lineage: int = 0  # kacinci nesil torun

    # --- kopya / ureme -------------------------------------------------
    def copy(self) -> "Genome":
        return Genome(dict(self.params), self.weights.copy(), self.lineage)

    def child(self, cfg, rng: np.random.Generator) -> "Genome":
        """Ureme sirasinda cagrilir. Mutasyon kapaliysa saf klon dondurur."""
        g = self.copy()
        g.lineage = self.lineage + 1
        if cfg.get("evolution.enabled", False):
            g.mutate(cfg, rng)
        return g

    def diversified(self, cfg, rng: np.random.Generator, spread: float) -> "Genome":
        """Kurucu genomdan cesitlendirilmis bir birey uretir.

        spread = 0 -> birebir klon (Faz 1 davranisi, kontrol grubu)
        spread = 1 -> parametreler tam sigma ile dagilir, agirliklar tamamen
                      bagimsiz rastgele aglar olur
        Aradaki degerler ikisi arasinda dogrusal gecis yapar.
        """
        g = self.copy()
        if spread <= 0.0:
            return g

        sigma = float(cfg.get("evolution.founder_param_sigma", 0.25)) * spread
        bounds = _bounds(cfg)
        for name in list(g.params):
            g.params[name] = _clip(g.params[name] + float(rng.normal(0.0, sigma)), bounds.get(name))

        if g.weights.size:
            fresh = rng.normal(0.0, _init_sigma(cfg), g.weights.shape).astype(np.float32)
            g.weights = ((1.0 - spread) * g.weights + spread * fresh).astype(np.float32)
        return g

    # --- mutasyon ------------------------------------------------------
    def mutate(self, cfg, rng: np.random.Generator) -> None:
        rate = float(cfg.get("evolution.mutation_rate", 0.0))
        sigma = float(cfg.get("evolution.mutation_sigma", 0.0))
        bounds = _bounds(cfg)

        for name in list(self.params):
            if rng.random() < rate:
                self.params[name] = _clip(
                    self.params[name] + float(rng.normal(0.0, sigma)), bounds.get(name)
                )

        if self.weights.size:
            # Agirliklar cok daha kalabalik oldugu icin ayri (daha dusuk) bir
            # oranla mutasyona ugrar; aksi halde her dogum agi darmadagin eder.
            w_rate = float(cfg.get("evolution.weight_mutation_rate", rate))
            w_sigma = float(cfg.get("evolution.weight_mutation_sigma", sigma))
            mask = rng.random(self.weights.shape) < w_rate
            delta = mask * rng.normal(0.0, w_sigma, self.weights.shape)
            limit = float(cfg.get("evolution.weight_clip", 4.0))
            self.weights = np.clip(self.weights + delta, -limit, limit).astype(np.float32)

    # --- olcum ---------------------------------------------------------
    def vector(self, order: list[str] | None = None) -> np.ndarray:
        """Cesitlilik metrikleri icin sabit sirali sayisal temsil."""
        names = order if order is not None else sorted(self.params)
        return np.array([self.params[n] for n in names], dtype=np.float64)


# ---------------------------------------------------------------------- kurucu
def founder_genome(cfg, rng: np.random.Generator | None = None) -> Genome:
    """config.genome.params + secili beyin backend'inin istedigi agirliklar."""
    params = cfg.get("genome.params", {})
    params = params.to_dict() if hasattr(params, "to_dict") else dict(params)
    genome = Genome({k: float(v) for k, v in params.items()})

    size = genome_size_for(cfg)
    if size > 0:
        if rng is None:
            genome.weights = np.zeros(size, dtype=np.float32)
        else:
            genome.weights = rng.normal(0.0, _init_sigma(cfg), size).astype(np.float32)
    return genome


# ---------------------------------------------------------------- yardimcilar
def _init_sigma(cfg) -> float:
    return float(cfg.get("brain.init_sigma", 0.6))


def _bounds(cfg) -> dict:
    b = cfg.get("evolution.param_bounds", {})
    return b.to_dict() if hasattr(b, "to_dict") else dict(b or {})


def _clip(value: float, lo_hi) -> float:
    if not lo_hi:
        return float(value)
    return float(min(max(value, lo_hi[0]), lo_hi[1]))
