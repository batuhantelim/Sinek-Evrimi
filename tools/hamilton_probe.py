#!/usr/bin/env python3
"""FAZ 4.6 — Hamilton esitsizligini DOLAYLI DEGIL OLCEREK sinar.

Neden gerekli: `bc_ratio_fit` (need_bonus carpanli) bir VARSAYIMDIR. Ondan
"r*b/c > 1" cikarmak kendi varsayimini olcmektir. Bu sonda b ve c'yi
simulasyonun kendi para biriminde — YAVRU sayisinda — olcer:

    yavru ~ 1 + yas + yemek + VERILEN + ALINAN

  b_hat = ALINAN katsayisi   (birim enerji almak kac yavru getirdi)
  c_hat = -VERILEN katsayisi (birim enerji vermek kac yavruya mal oldu)

Yas ve yemek KONTROL EDILIR: yasli ajan hem cok yer hem cok urer, cok
toplayan hem cok paylasir hem cok urer (Faz 4.5 dersi).

Hamilton: r * b_hat / c_hat > 1 ise akraba fedakarligi pozitif secilim gorur.
`r` etiketten degil GENOMDAN okunur (`genetic_r`).

    python tools/hamilton_probe.py --set agents.motors.max_speed=0.05 --steps 8000
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sinek.config import load_config  # noqa: E402
from sinek.metrics import genetic_relatedness  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

BASE = ["viz.mode=none", "metrics.enabled=false", "metrics.record_lifetimes=true"]
#: experiments/faz45_ekoloji.yaml ile ayni rejim (test bunu sabitler).
REGIME = [
    "agents.max_count=5000",
    "agents.motors.max_speed=0.20",
    "agents.motors.max_turn=0.25",
    "agents.reproduction.spawn_radius=0.3",
    "rules.share.need_bonus=3.0",
    "rules.share.need_mode=fitness",
    "rules.attack.enabled=true",
    "rules.predator.enabled=false",
    # Faz 5 hafizasi bu rejimin parcasi DEGIL: varsayilan ilerledi diye
    # eski tarama sessizce baska bir deney olmasin.
    "rules.memory.enabled=false",
    "rules.partner.enabled=false",
]
SEED_POP = "docs/faz45/population_ekoloji.npz"


def ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Katsayilar ve t degerleri."""
    X = np.column_stack([X, np.ones(X.shape[0])])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = max(1, X.shape[0] - X.shape[1])
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.maximum(np.diag(xtx_inv) * sigma2, 1e-30))
    return beta, beta / se


def probe(extra: list[str], seed: int, steps: int) -> dict:
    cfg = load_config(overrides=BASE + REGIME + list(extra) + [f"seed={seed}"])
    pop = os.path.join(ROOT, SEED_POP)
    genomes, _ = load_population(pop, cfg) if os.path.exists(pop) else (None, None)
    sim = Simulation(cfg, initial_genomes=genomes)
    r_hist: list[float] = []
    sim.run(steps, on_step=lambda s: r_hist.append(
        genetic_relatedness(s.agents)["genetic_r"]) if s.step_index % 500 == 0 else None)

    rec = np.array(sim.life_records, dtype=np.float64)
    if rec.shape[0] < 50:
        raise SystemExit("yeterli tamamlanmis yasam yok")
    food, kids, age, given, recv = rec[:, 0], rec[:, 1], rec[:, 2], rec[:, 3], rec[:, 4]
    m = age >= float(cfg.agents.reproduction.min_age)
    X = np.column_stack([age[m], food[m], given[m], recv[m]])
    beta, tvals = ols(kids[m], X)
    c_hat, b_hat = -beta[2], beta[3]          # vermenin maliyeti, almanin faydasi
    r_gen = float(np.mean([v for v in r_hist if v != 0.0])) if r_hist else 0.0

    total_amount = sim.stats_total.get("share_energy", 0.0)
    created = sim.stats_total.get("energy_created", 0.0)
    return {
        "n": int(m.sum()),
        "pop": len(sim.agents),
        "genetic_r": r_gen,
        "coop": sim.stats_total.get("share_events", 0) / max(1e-9, sim.stats_total.get("opp_kin", 0)
                                                             + sim.stats_total.get("opp_nonkin", 0)),
        "bc_energy": sim.stats_total.get("share_benefit", 0.0)
        / max(1e-9, sim.stats_total.get("share_cost", 0.0)),
        "bc_fit": sim.stats_total.get("share_benefit_fit", 0.0)
        / max(1e-9, sim.stats_total.get("share_cost", 0.0)),
        "b_hat": b_hat, "t_b": tvals[3],
        "c_hat": c_hat, "t_c": -tvals[2],
        "bc_emp": b_hat / c_hat if abs(c_hat) > 1e-12 else float("nan"),
        "created": created,
        "created_rel": created / max(1e-9, total_amount),
        "share_energy": total_amount,
    }


def report(rows: list[tuple[str, dict]]) -> None:
    print("=" * 100)
    print("HAMILTON SONDASI — b ve c YAVRU biriminde OLCULUR (varsayilmaz)")
    print("  yavru ~ yas + yemek + VERILEN + ALINAN   (yas ve yemek kontrollu)")
    print("=" * 100)
    hdr = f"  {'kosul':16s} {'r(genom)':>9} {'b/c enerji':>11} {'b/c fit*':>9} " \
          f"{'b_hat':>9} {'t':>6} {'c_hat':>9} {'t':>6} {'b/c OLCULEN':>12} {'r*b/c':>8} {'korunum':>9}"
    print(hdr)
    for name, d in rows:
        valid = abs(d["created_rel"]) < 1e-6
        print(f"  {name:16s} {d['genetic_r']:9.4f} {d['bc_energy']:11.3f} {d['bc_fit']:9.3f} "
              f"{d['b_hat']:9.5f} {d['t_b']:+6.1f} {d['c_hat']:9.5f} {d['t_c']:+6.1f} "
              f"{d['bc_emp']:12.3f} {d['genetic_r'] * d['bc_emp']:8.3f} "
              f"{'TAMAM' if valid else 'IHLAL!':>9}")
    print()
    print("  * b/c fit: need_bonus carpanli TAHMIN — bir varsayimdir, kanit degildir.")
    print("  r*b/c > 1 ise teori akraba fedakarligini pozitif secilimde bekler.")
    print("  c_hat <= 0 ise 'vermek maliyetli degil' demektir: Hamilton sorusu dusmez.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Hamilton esitsizligi sondasi")
    ap.add_argument("--set", dest="extra", action="append", default=[])
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--name", default="kosul")
    args = ap.parse_args(argv)
    report([(args.name, probe(args.extra, args.seed, args.steps))])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
