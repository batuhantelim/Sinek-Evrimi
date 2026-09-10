"""Metrik toplama ve CSV yazimi.

Basari olcutunu gozle degil sayiyla takip edebilmek icin her adimda
populasyon, enerji, kaynak ve davranis istatistikleri kaydedilir.
Faz 2/3 icin ayrilan sutunlar (cooperation_rate, behavior_diversity)
Faz 1'de 0 doner ama sutun semasi bastan sabittir — grafik kodu bozulmasin.
"""

from __future__ import annotations

import csv
import math
import os

import numpy as np

COLUMNS = [
    "step",
    "population",
    "births",
    "deaths",
    "death_starved",
    "death_hazard",
    "death_old_age",
    "mean_energy",
    "std_energy",
    "mean_age",
    "max_lineage",
    "food_total",
    "food_fill",       # food_total / kapasite
    "food_eaten",      # bu adimda yenen birim
    "mean_speed",
    "mean_food_eaten", # ajan basina yasam boyu
    "clustering",      # komsu yakinligi (0..1) — surulesme gostergesi
    "cooperation_rate",   # Faz 3
    "behavior_diversity", # Faz 2 (genom std ortalamasi)
]


class Metrics:
    """Adim adim kayit tutar, istege bagli olarak CSV'ye yazar."""

    def __init__(self, cfg, out_dir: str):
        self.cfg = cfg
        self.enabled = bool(cfg.get("metrics.enabled", True))
        self.every = max(1, int(cfg.get("metrics.every", 1)))
        self.rows: list[dict] = []
        self._fh = None
        self._writer = None
        if self.enabled:
            os.makedirs(out_dir, exist_ok=True)
            self.path = os.path.join(out_dir, str(cfg.get("metrics.csv", "metrics.csv")))
            self._fh = open(self.path, "w", newline="", encoding="utf-8")
            self._writer = csv.DictWriter(self._fh, fieldnames=COLUMNS)
            self._writer.writeheader()
        else:
            self.path = ""

    # ------------------------------------------------------------------
    def record(self, sim) -> dict | None:
        if not self.enabled or sim.step_index % self.every != 0:
            return None
        row = self._collect(sim)
        self.rows.append(row)
        self._writer.writerow(row)
        return row

    def _collect(self, sim) -> dict:
        agents = sim.agents
        n = len(agents)
        if n:
            energy = np.fromiter((a.energy for a in agents), dtype=np.float64, count=n)
            age = np.fromiter((a.age for a in agents), dtype=np.float64, count=n)
            speed = np.fromiter(
                (float(a.last_motors[1]) * float(sim.cfg.agents.motors.max_speed) for a in agents),
                dtype=np.float64,
                count=n,
            )
            eaten = np.fromiter((a.food_eaten for a in agents), dtype=np.float64, count=n)
            lineage = max(a.genome.lineage for a in agents)
        else:
            energy = age = speed = eaten = np.zeros(0)
            lineage = 0

        return {
            "step": sim.step_index,
            "population": n,
            "births": sim.stats_step["births"],
            "deaths": sim.stats_step["deaths"],
            "death_starved": sim.stats_step["death_starved"],
            "death_hazard": sim.stats_step["death_hazard"],
            "death_old_age": sim.stats_step["death_old_age"],
            "mean_energy": _r(energy.mean() if n else 0.0),
            "std_energy": _r(energy.std() if n else 0.0),
            "mean_age": _r(age.mean() if n else 0.0),
            "max_lineage": lineage,
            "food_total": _r(sim.world.food_total, 2),
            "food_fill": _r(sim.world.food_total / max(1e-9, sim.world.food_capacity_total), 4),
            "food_eaten": _r(sim.stats_step["food_eaten"], 4),
            "mean_speed": _r(speed.mean() if n else 0.0, 4),
            "mean_food_eaten": _r(eaten.mean() if n else 0.0),
            "clustering": _r(clustering_index(sim), 4),
            "cooperation_rate": _r(sim.stats_step.get("cooperation_rate", 0.0), 4),
            "behavior_diversity": _r(behavior_diversity(agents), 5),
        }

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    # ------------------------------------------------------------------
    def summary(self) -> str:
        if not self.rows:
            return "(metrik yok)"
        first, last = self.rows[0], self.rows[-1]
        pop = [r["population"] for r in self.rows]
        en = [r["mean_energy"] for r in self.rows]
        half = len(self.rows) // 2
        lines = [
            f"  adim              : {first['step']} -> {last['step']}",
            f"  populasyon        : baslangic {first['population']}, son {last['population']}, "
            f"tepe {max(pop)}, dip {min(pop)}",
            f"  ortalama enerji   : ilk yari {np.mean(en[:half or 1]):.1f}, "
            f"son yari {np.mean(en[half:]):.1f}",
            f"  toplam dogum      : {sum(r['births'] for r in self.rows)}",
            f"  toplam olum       : {sum(r['deaths'] for r in self.rows)} "
            f"(aclik {sum(r['death_starved'] for r in self.rows)}, "
            f"tehlike {sum(r['death_hazard'] for r in self.rows)}, "
            f"yaslilik {sum(r['death_old_age'] for r in self.rows)})",
            f"  en uzun soy zinciri: {last['max_lineage']} nesil",
            f"  yemek doluluk     : baslangic {first['food_fill']:.3f}, son {last['food_fill']:.3f}",
            f"  kumelenme indeksi : {np.mean([r['clustering'] for r in self.rows]):.3f}",
            f"  davranis cesitliligi: {last['behavior_diversity']:.5f}"
            f"   {'(Faz 1: klonlar, beklenen 0)' if last['behavior_diversity'] == 0 else ''}",
        ]
        return "\n".join(lines)


def _r(v, nd: int = 3) -> float:
    v = float(v)
    return round(v, nd) if math.isfinite(v) else 0.0


def clustering_index(sim) -> float:
    """Morisita benzeri kumelenme indeksi (O(n), her adimda ucuz).

    Dunya komsu-yaricapi buyuklugunde kutulara bolunur, ajanlarin kutulara
    dagilimi rastgele dagilimla karsilastirilir.
      ~0  : rastgele dagilim
      >0  : kumelenme / surulesme (kaynak yamalarina toplanma)
      <0  : birbirinden kacinma / duzgun yayilma
    """
    agents = sim.agents
    n_agents = len(agents)
    if n_agents < 4:
        return 0.0
    world = sim.world
    box = max(2.0, float(sim.cfg.agents.senses.neighbor_radius))
    nx = max(2, int(world.width / box))
    ny = max(2, int(world.height / box))
    counts = np.zeros(nx * ny, dtype=np.int64)
    for a in agents:
        i = min(int(a.x / world.width * nx), nx - 1)
        j = min(int(a.y / world.height * ny), ny - 1)
        counts[j * nx + i] += 1
    denom = n_agents * (n_agents - 1)
    if denom <= 0:
        return 0.0
    morisita = counts.size * float((counts * (counts - 1)).sum()) / denom
    if morisita <= 1e-9:
        return -1.0
    return float(np.clip(1.0 - 1.0 / morisita, -1.0, 1.0))


def behavior_diversity(agents) -> float:
    """Genom parametrelerinin ortalama standart sapmasi.

    Faz 1'de tum ajanlar klon oldugu icin tam olarak 0.0 olmali —
    bu ayni zamanda 'mutasyon gercekten kapali mi' testidir.
    """
    if len(agents) < 2:
        return 0.0
    names = sorted(agents[0].genome.params)
    mat = np.array([a.genome.vector(names) for a in agents], dtype=np.float64)
    spread = float(mat.std(axis=0).mean())
    # np.std ozdes degerlerde ~1e-15 artik uretir; klonlarda tam 0 gormek istiyoruz
    return 0.0 if spread < 1e-12 else spread
