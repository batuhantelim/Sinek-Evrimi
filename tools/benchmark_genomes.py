#!/usr/bin/env python3
"""Evrimlesmis koloni vs acemi (rastgele beyinli) koloni — ayni dunyada.

Nesil dongusu icindeki fitness artisi, secilimin ISE YARADIGINI gosterir ama
"ne ogrendiler" sorusuna cevap vermez. Bu arac kaydedilmis bir koloniyi
rastgele beyinlerle yan yana kosturur; ureme ve secilim KAPALI, yani olculen
sey saf davranis.

    python tools/benchmark_genomes.py runs/faz2/population.npz --steps 500
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import S  # noqa: E402
from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

FROZEN = [  # evrim ve ureme kapali: sadece davranisi olcuyoruz
    "viz.mode=none",
    "metrics.enabled=false",
    "evolution.enabled=false",
    "evolution.mode=steady_state",
    "agents.reproduction.enabled=false",
]


def measure(genomes, seed: int, steps: int, extra=()) -> dict:
    cfg = load_config(overrides=FROZEN + [f"seed={seed}"] + list(extra))
    sim = Simulation(cfg, initial_genomes=genomes)
    start = sim.population

    align = hazard = on_food = 0.0
    samples = 0
    for _ in range(steps):
        sim.step()
        if not sim.agents:
            break
        if sim.step_index % 5 == 0:  # ucuz olsun diye seyrek ornekleme
            sensors = np.array([a.sense(sim.world, cfg) for a in sim.agents])
            align += float(sensors[:, S["food_fwd"]].mean())
            hazard += float((sensors[:, S["hazard_near"]] > 0.8).mean())
            on_food += float((sensors[:, S["food_here"]] > 0.05).mean())
            samples += 1

    survivors = sim.population
    eaten = np.array([a.food_eaten for a in sim.agents], dtype=np.float64) if survivors else np.zeros(1)
    k = max(1, samples)
    return {
        "hayatta": survivors / max(1, start),
        "yemek": float(eaten.mean()),
        "hizalanma": align / k,
        "tehlikede": hazard / k,
        "yem_ustunde": on_food / k,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="evrimlesmis vs acemi koloni kiyasi")
    ap.add_argument("population", help="runs/<name>/population.npz")
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--repeats", type=int, default=3, help="kac farkli dunya/seed")
    ap.add_argument("--top", type=int, default=None, help="kayittan en iyi N genom")
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    args = ap.parse_args(argv)

    cfg = load_config(overrides=FROZEN + args.overrides)
    genomes, meta = load_population(args.population, cfg, top=args.top)
    print(
        f"kayit: {len(genomes)} genom | beyin {meta['brain_type']} "
        f"(hidden {meta['brain_hidden']}) | nesil {meta['generation']}"
    )
    print(f"olcum: {args.steps} adim x {args.repeats} dunya, ureme ve secilim KAPALI\n")

    rows = {"evrimlesmis": [], "acemi": []}
    for i in range(args.repeats):
        seed = 1000 + i
        rows["evrimlesmis"].append(measure(genomes, seed, args.steps, args.overrides))
        # acemi: ayni dunya, kurucu genomdan tamamen rastgele aglar
        rows["acemi"].append(
            measure(None, seed, args.steps, args.overrides + ["evolution.founder_spread=1.0"])
        )

    keys = ["hayatta", "yemek", "hizalanma", "yem_ustunde", "tehlikede"]
    labels = {
        "hayatta": "hayatta kalan orani",
        "yemek": "ajan basina yemek",
        "hizalanma": "koku gradyaniyla hizalanma",
        "yem_ustunde": "yemek uzerinde gecen zaman",
        "tehlikede": "tehlike icinde gecen zaman",
    }
    print(f"  {'olcut':32s} {'evrimlesmis':>12s} {'acemi':>10s} {'oran':>8s}")
    for k in keys:
        a = float(np.mean([r[k] for r in rows["evrimlesmis"]]))
        b = float(np.mean([r[k] for r in rows["acemi"]]))
        ratio = a / b if abs(b) > 1e-9 else math.inf
        print(f"  {labels[k]:32s} {a:12.3f} {b:10.3f} {ratio:7.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
