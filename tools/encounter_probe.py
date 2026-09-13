#!/usr/bin/env python3
"""FAZ 5 onkosul 1 — TEKRARLI KARSILASMA var mi?

Karsiliklilik (Axelrod) ucu birden gerektirir: tekrarli karsilasma, tanima,
hafiza. Ucu de olmadan "karsiliklilik evrimlesmedi" demek YANLIS olur —
dogru cumle "kosul yoktu"dur. Bu sonda, HICBIR MEKANIK EKLEMEDEN birincisini
olcer: ayni iki birey birden cok kez karsilasiyor mu?

⚠ KRITIK AYRIM — EPIZOT vs ADIM:
Bir sinek 100 adim boyunca ayni komsunun yaninda durursa bu 100 karsilasma
DEGIL, tek bir uzun karsilasmadir. Axelrod'un tekrarli oyunu, araya baska
partnerlerin girdigi AYRI bulusmalar ister. Bu yuzden iki sayi ayri verilir:

  adim-tekrari   : ayni ciftin gorulduğu ajan-adimlarin orani (SISIRILMIS)
  EPIZOT-tekrari : ayri bulusmalarin orani — asil olcu

    python tools/encounter_probe.py --steps 4000
    python tools/encounter_probe.py --set agents.motors.max_speed=0.05
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

BASE = ["viz.mode=none", "metrics.enabled=false"]
#: experiments/faz45_ekoloji.yaml ile ayni rejim (test sabitler).
REGIME = [
    "agents.max_count=5000",
    "agents.motors.max_speed=0.20",
    "agents.motors.max_turn=0.25",
    "agents.reproduction.spawn_radius=0.3",
    "rules.share.need_bonus=3.0",
    "rules.share.need_mode=fitness",
    "rules.attack.enabled=true",
    "rules.predator.enabled=false",
]
SEED_POP = "docs/faz45/population_ekoloji.npz"


class Tracker:
    """Her ajanin partner gecmisini tutar; epizotlari adimlardan ayirir."""

    def __init__(self):
        self.episodes: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.last_partner: dict[int, int] = {}
        self.steps_total = 0
        self.steps_repeat = 0
        self.episodes_total = 0
        self.episodes_repeat = 0
        self.gaps: list[int] = []          # ayni partnere donus araligi (adim)
        self.last_seen: dict[tuple[int, int], int] = {}

    def observe(self, step: int, agents) -> None:
        for a in agents:
            p = getattr(a, "nearest", None)
            if p is None:
                self.last_partner.pop(a.id, None)
                continue
            self.steps_total += 1
            hist = self.episodes[a.id]
            if hist.get(p.id, 0) > 0:
                self.steps_repeat += 1
            # YENI EPIZOT: partner degistiyse (ya da arada komsusuz kaldiysa)
            if self.last_partner.get(a.id) != p.id:
                self.episodes_total += 1
                if hist[p.id] > 0:
                    self.episodes_repeat += 1
                    prev = self.last_seen.get((a.id, p.id))
                    if prev is not None:
                        self.gaps.append(step - prev)
                hist[p.id] += 1
                self.last_partner[a.id] = p.id
            self.last_seen[(a.id, p.id)] = step

    def report(self) -> dict:
        counts = [c for hist in self.episodes.values() for c in hist.values()]
        per_agent = [len(h) for h in self.episodes.values() if h]
        # "karsiliklilik zemini": ayni partnerle >= 3 AYRI bulusma yasamis ajan
        ground = [1 for h in self.episodes.values() if h and max(h.values()) >= 3]
        gaps = np.array(self.gaps, dtype=np.float64) if self.gaps else np.zeros(0)
        return {
            "adim_tekrari": self.steps_repeat / max(1, self.steps_total),
            "epizot_tekrari": self.episodes_repeat / max(1, self.episodes_total),
            "epizot_sayisi": self.episodes_total,
            "ajan_basina_partner": float(np.mean(per_agent)) if per_agent else 0.0,
            "partner_basina_bulusma": float(np.mean(counts)) if counts else 0.0,
            "en_cok_bulusma": int(max(counts)) if counts else 0,
            "zemin_payi": len(ground) / max(1, len(per_agent)),
            "ort_donus_araligi": float(gaps.mean()) if gaps.size else 0.0,
            "medyan_donus_araligi": float(np.median(gaps)) if gaps.size else 0.0,
        }


def probe(extra: list[str], seed: int, steps: int) -> dict:
    cfg = load_config(overrides=BASE + REGIME + list(extra) + [f"seed={seed}"])
    pop = os.path.join(ROOT, SEED_POP)
    genomes, _ = load_population(pop, cfg) if os.path.exists(pop) else (None, None)
    sim = Simulation(cfg, initial_genomes=genomes)
    t = Tracker()
    sim.run(steps, on_step=lambda s: t.observe(s.step_index, s.agents))
    out = t.report()
    out["populasyon"] = len(sim.agents)
    out["omur"] = float(cfg.agents.lifespan)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="tekrarli karsilasma sondasi")
    ap.add_argument("--set", dest="extra", action="append", default=[])
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--name", default="kosul")
    args = ap.parse_args(argv)
    d = probe(args.extra, args.seed, args.steps)
    print("=" * 88)
    print(f"TEKRARLI KARSILASMA SONDASI — {args.name}, {args.steps} adim, seed {args.seed}")
    print("=" * 88)
    print(f"  populasyon (son)            : {d['populasyon']:.0f}")
    print(f"  ajan basina farkli partner  : {d['ajan_basina_partner']:.1f}")
    print(f"  partner basina AYRI bulusma : {d['partner_basina_bulusma']:.2f}  (en cok {d['en_cok_bulusma']})")
    print(f"  adim-tekrari (SISIRILMIS)   : %{d['adim_tekrari'] * 100:.1f}")
    print(f"  EPIZOT-tekrari (asil olcu)  : %{d['epizot_tekrari'] * 100:.1f}")
    print(f"  >=3 ayri bulusma yasayan    : %{d['zemin_payi'] * 100:.1f} ajan  <- KARSILIKLILIK ZEMINI")
    print(f"  ayni partnere donus araligi : ort {d['ort_donus_araligi']:.0f} adim, "
          f"medyan {d['medyan_donus_araligi']:.0f}  (omur {d['omur']:.0f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
