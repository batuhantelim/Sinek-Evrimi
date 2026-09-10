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

BASE_COLUMNS = [
    "step",
    "generation",
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
    "behavior_diversity", # Faz 2: genom parametrelerinin std ortalamasi
    "weight_diversity",   # Faz 2: sinir agi agirliklarinin std ortalamasi
]


class Metrics:
    """Adim adim kayit tutar, istege bagli olarak CSV'ye yazar.

    Genom parametreleri icin `gp_<ad>` sutunlari calisma aninda eklenir:
    evrimin YONUNU (hangi parametre nereye kaydi) izleyebilmek icin.
    """

    def __init__(self, cfg, out_dir: str, param_names=()):
        self.cfg = cfg
        self.enabled = bool(cfg.get("metrics.enabled", True))
        self.every = max(1, int(cfg.get("metrics.every", 1)))
        self.param_names = sorted(param_names)
        self.columns = BASE_COLUMNS + [f"gp_{n}" for n in self.param_names]
        self.rows: list[dict] = []
        self._fh = None
        self._writer = None
        self._gen_fh = None
        self._gen_writer = None
        self._gen_written = 0
        self.gen_path = ""
        self.out_dir = out_dir
        if self.enabled:
            os.makedirs(out_dir, exist_ok=True)
            self.path = os.path.join(out_dir, str(cfg.get("metrics.csv", "metrics.csv")))
            self._fh = open(self.path, "w", newline="", encoding="utf-8")
            self._writer = csv.DictWriter(self._fh, fieldnames=self.columns)
            self._writer.writeheader()
        else:
            self.path = ""

    # ------------------------------------------------------------------
    def record(self, sim) -> dict | None:
        self.sync_generations(sim)
        if not self.enabled or sim.step_index % self.every != 0:
            return None
        row = self._collect(sim)
        self.rows.append(row)
        self._writer.writerow(row)
        return row

    def sync_generations(self, sim) -> None:
        """Yeni tamamlanan nesil satirlarini generations.csv'ye ekler."""
        rows = getattr(sim, "generation_rows", None)
        if not self.enabled or not rows or self._gen_written >= len(rows):
            return
        if self._gen_writer is None:
            self.gen_path = os.path.join(self.out_dir, "generations.csv")
            self._gen_fh = open(self.gen_path, "w", newline="", encoding="utf-8")
            self._gen_writer = csv.DictWriter(self._gen_fh, fieldnames=list(rows[0]))
            self._gen_writer.writeheader()
        for row in rows[self._gen_written :]:
            self._gen_writer.writerow(row)
        self._gen_fh.flush()
        self._gen_written = len(rows)

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

        row = {
            "step": sim.step_index,
            "generation": getattr(sim, "generation", 0),
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
            "weight_diversity": _r(weight_diversity(agents), 5),
        }
        means = genome_param_means(agents)
        for name in self.param_names:
            row[f"gp_{name}"] = _r(means.get(name, 0.0), 4)
        return row

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None
        if self._gen_fh:
            self._gen_fh.close()
            self._gen_fh = None

    # ------------------------------------------------------------------
    def summary(self, sim=None) -> str:
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
            f"   {'(klonlar)' if last['behavior_diversity'] == 0 else ''}",
            f"  agirlik cesitliligi : {last.get('weight_diversity', 0.0):.5f}",
        ]
        lines += self._evolution_summary(sim)
        return "\n".join(lines)

    def _evolution_summary(self, sim) -> list[str]:
        rows = getattr(sim, "generation_rows", None) if sim is not None else None
        if not rows:
            return []
        first, last = rows[0], rows[-1]
        half = max(1, len(rows) // 3)
        early = np.mean([r["mean_fitness"] for r in rows[:half]])
        late = np.mean([r["mean_fitness"] for r in rows[-half:]])
        change = (late - early) / abs(early) * 100.0 if abs(early) > 1e-9 else 0.0
        out = [
            "",
            f"  --- EVRIM ({len(rows)} nesil, mod: {getattr(sim, 'mode', '?')}) ---",
            f"  ort. fitness      : nesil {first['generation']} -> {last['generation']}: "
            f"{first['mean_fitness']:.1f} -> {last['mean_fitness']:.1f}",
            f"  ilk/son ucte bir  : {early:.1f} -> {late:.1f}  ({change:+.1f}%)",
            f"  en iyi fitness    : {max(r['max_fitness'] for r in rows):.1f}",
            f"  ort. yenen yemek  : {first['mean_food_eaten']:.2f} -> {last['mean_food_eaten']:.2f}",
        ]
        used = _params_used_by_brain(self.cfg)
        drift = [
            (name[3:], first[name], last[name])
            for name in last
            if name.startswith("gp_") and abs(last[name] - first[name]) > 1e-6
        ]
        drift.sort(key=lambda t: -abs(t[2] - t[1]))
        effective = [d for d in drift if used is None or d[0] in used]
        neutral = [d for d in drift if used is not None and d[0] not in used]

        if effective:
            out.append("  genom kaymasi — beynin OKUDUGU parametreler:")
            for name, a, b in effective[:5]:
                out.append(f"    {name:18s} {a:+.3f} -> {b:+.3f}  ({b - a:+.3f})")
        if neutral:
            out.append(
                f"  notr suruklenme   : {len(neutral)} parametre "
                f"(bu beyin okumuyor; en cok {neutral[0][0]} {neutral[0][2] - neutral[0][1]:+.3f}) "
                "-> yerlesik drift referansi"
            )
        if self.gen_path:
            out.append(f"  nesil CSV         : {self.gen_path}")
        return out


def _params_used_by_brain(cfg) -> tuple[str, ...] | None:
    """Secili beyin backend'inin fiilen okudugu genom parametreleri.

    rnn beyninde davranis agirliklarda saklidir; isimli parametrelerin cogu
    okunmaz. Bunlari "evrimlesti" diye raporlamak yaniltici olur.
    """
    from .brains import brain_class  # gec import: dairesel bagimlilik olmasin

    try:
        return brain_class(cfg).uses_params
    except KeyError:
        return None


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


def genome_param_means(agents) -> dict[str, float]:
    """Genom parametrelerinin populasyon ortalamasi — evrimin YONUNU gosterir."""
    if not agents:
        return {}
    names = sorted(agents[0].genome.params)
    mat = np.array([a.genome.vector(names) for a in agents], dtype=np.float64)
    return {n: float(v) for n, v in zip(names, mat.mean(axis=0))}


def weight_diversity(agents) -> float:
    """Sinir agi agirliklarinin ortalama standart sapmasi.

    `behavior_diversity` isimli parametreleri olcer; rnn beyninde asil
    davranis agirliklarda saklidir, bu yuzden ayri bir sutun tutuluyor.
    """
    if len(agents) < 2 or not agents[0].genome.weights.size:
        return 0.0
    mat = np.array([a.genome.weights for a in agents], dtype=np.float64)
    spread = float(mat.std(axis=0).mean())
    return 0.0 if spread < 1e-12 else spread


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
