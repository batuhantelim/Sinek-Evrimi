#!/usr/bin/env python3
"""Hamilton kurali (r*b > c) taramasi: paylasim hangi rejimde hayatta kaliyor?

Faz 3 adim 1 negatifti. Bu arac iki ihtimali AYIRMAK icin var:
  (A) kin altruizmi dogasi geregi zor evrimlesir,
  (B) kurulumumuz Hamilton kuralini yapisal olarak saglanamaz kildi.

Uc kol taranir:
  c (maliyet)   : rules.share.overhead
  b (fayda)     : kitlik — ac aliciya verilen enerjinin marjinal degeri
  r (akrabalik) : mekansal bag — hiz ve dogum yaricapi

HER rejim, soyisim-karistirma KONTROLUYLE birlikte kosulur. Ham metrige
guvenilmez: adim 1'de ham kin_bias kontrolden ayirt edilemiyordu.

    python tools/sweep_hamilton.py taban c_sifir r_bagli --steps 6000
    python tools/sweep_hamilton.py --list
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

# --- taranan rejimler -------------------------------------------------------
# Her biri config.yaml uzerine binen kismi override listesi.
REGIMES: dict[str, list[str]] = {
    "taban": [],
    # --- c kolu: paylasmanin verene maliyeti ---
    "c_yari": ["rules.share.overhead=0.6"],
    "c_dusuk": ["rules.share.overhead=0.2"],
    "c_sifir": ["rules.share.overhead=0.0"],
    # --- b kolu: aliciya faydasi (kitlik marjinal degeri yukseltir) ---
    "b_kitlik": ["world.food.regrowth_rate=0.004", "world.food.initial_fill=0.35"],
    "b_sert_kitlik": [
        "world.food.regrowth_rate=0.002",
        "world.food.initial_fill=0.25",
        "world.food.patches=14",
    ],
    # --- r kolu: akrabalarin mekansal bagi ---
    "r_yavas": ["agents.motors.max_speed=0.35", "agents.reproduction.spawn_radius=0.5"],
    "r_cok_bagli": [
        "agents.motors.max_speed=0.20",
        "agents.reproduction.spawn_radius=0.3",
        "agents.motors.max_turn=0.25",
    ],
    # --- kombinasyonlar ---
    "rc": ["agents.motors.max_speed=0.35", "agents.reproduction.spawn_radius=0.5",
           "rules.share.overhead=0.0"],
    "rb": ["agents.motors.max_speed=0.35", "agents.reproduction.spawn_radius=0.5",
           "world.food.regrowth_rate=0.004", "world.food.initial_fill=0.35"],
    "rbc": ["agents.motors.max_speed=0.35", "agents.reproduction.spawn_radius=0.5",
            "world.food.regrowth_rate=0.004", "world.food.initial_fill=0.35",
            "rules.share.overhead=0.0"],
    # --- azalan verim kuralı (b/c tavanini kaldirir) ---
    "rbc_azalan": ["agents.motors.max_speed=0.35", "agents.reproduction.spawn_radius=0.5",
                   "world.food.regrowth_rate=0.004", "world.food.initial_fill=0.35",
                   "rules.share.overhead=0.0", "rules.share.need_bonus=3.0"],
    "r_azalan": ["agents.motors.max_speed=0.20", "agents.reproduction.spawn_radius=0.3",
                 "agents.motors.max_turn=0.25", "rules.share.need_bonus=3.0"],
    "rbc_uc": ["agents.motors.max_speed=0.20", "agents.reproduction.spawn_radius=0.3",
               "agents.motors.max_turn=0.25",
               "world.food.regrowth_rate=0.002", "world.food.initial_fill=0.25",
               "world.food.patches=14", "rules.share.overhead=0.0",
               "rules.share.amount=12.0"],
}

FIXED = ["viz.mode=none", "metrics.enabled=false"]
SEED_POP = "docs/faz2/population.npz"


def run_one(overrides: list[str], steps: int, seed_path: str | None) -> dict:
    cfg = load_config(overrides=FIXED + overrides)
    genomes = None
    if seed_path and os.path.exists(seed_path):
        genomes, _meta = load_population(seed_path, cfg)
    sim = Simulation(cfg, initial_genomes=genomes)
    sim.run(steps)
    return {
        "rows": sim.generation_rows,
        "population": sim.population,
        "extinct": sim.extinct_at,
    }


def late(rows: list[dict], key: str) -> list[float]:
    """Son yarinin degerleri — baslangic gecici rejimini disarida birakir."""
    return [float(r[key]) for r in rows[len(rows) // 2 :]] if rows else []


def welch_t(a: list[float], b: list[float]) -> float:
    """Iki orneklem arasindaki farkin standart hata cinsinden buyuklugu."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    se = math.sqrt(va + vb)
    return (float(np.mean(a)) - float(np.mean(b))) / se if se > 1e-12 else 0.0


def evaluate(name: str, steps: int, seed_path: str | None) -> dict:
    overrides = REGIMES[name]
    t0 = time.time()
    main = run_one(overrides, steps, seed_path)
    ctrl = run_one(overrides + ["rules.kinship.control=shuffle_surnames"], steps, seed_path)

    m_rows, c_rows = main["rows"], ctrl["rows"]
    m_adj, c_adj = late(m_rows, "kin_bias_adj"), late(c_rows, "kin_bias_adj")
    share = late(m_rows, "cooperation_rate")
    result = {
        "regime": name,
        "overrides": overrides,
        "steps": steps,
        "seconds": round(time.time() - t0, 1),
        "population": main["population"],
        "extinct": main["extinct"],
        "share_rate": float(np.mean(share)) if share else 0.0,
        "share_rate_last": float(share[-1]) if share else 0.0,
        "kin_adj_main": float(np.mean(m_adj)) if m_adj else 0.0,
        "kin_adj_ctrl": float(np.mean(c_adj)) if c_adj else 0.0,
        "t_stat": welch_t(m_adj, c_adj),
        "assortment": float(np.mean(late(m_rows, "kin_assortment"))) if m_rows else 0.0,
        "bc_ratio": float(np.mean(late(m_rows, "bc_ratio"))) if m_rows else 0.0,
        "rescue_share": float(np.mean(late(m_rows, "rescue_share"))) if m_rows else 0.0,
        "lineage_eff": float(np.mean(late(m_rows, "lineage_effective"))) if m_rows else 0.0,
        "opp_kin": float(np.mean(late(m_rows, "opp_kin"))) if m_rows else 0.0,
    }
    # BASARI = paylasim elenmemis VE kontrolden ayrilmis
    result["survives"] = result["share_rate"] > 0.03
    result["separates"] = result["t_stat"] > 2.0 and result["kin_adj_main"] > result["kin_adj_ctrl"]
    result["verdict"] = "VAR" if result["survives"] and result["separates"] else "yok"
    return result


HEADER = (
    f"  {'rejim':14s} {'paylasim':>9s} {'r':>7s} {'b/c':>6s} {'r*b/c':>7s} {'kurtar':>7s} "
    f"{'soy':>5s} {'kin_adj':>8s} {'kontrol':>8s} {'t':>6s} {'N':>5s}  karar"
)


def format_row(r: dict) -> str:
    return (
        f"  {r['regime']:14s} {r['share_rate'] * 100:8.2f}% {r['assortment']:7.3f} "
        f"{r['bc_ratio']:6.3f} {r['assortment'] * r['bc_ratio']:7.3f} "
        f"{r['rescue_share'] * 100:6.1f}% {r['lineage_eff']:5.1f} "
        f"{r['kin_adj_main'] * 100:+8.3f} {r['kin_adj_ctrl'] * 100:+8.3f} "
        f"{r['t_stat']:+6.2f} {r['population']:5d}  {r['verdict']}"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Hamilton kurali b/c taramasi")
    ap.add_argument("regimes", nargs="*", default=[], help=f"secenekler: {', '.join(REGIMES)}")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--no-seed", action="store_true", help="Faz 2 tohumunu kullanma")
    ap.add_argument("--out", default=None, help="sonuclari JSONL olarak da yaz")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.list or not args.regimes:
        for name, ov in REGIMES.items():
            print(f"  {name:14s} {ov}")
        return 0

    seed = None if args.no_seed else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), SEED_POP
    )
    print(f"adim={args.steps}  tohum={'yok' if seed is None else SEED_POP}")
    print("kin_adj ve kontrol YUZDE PUAN cinsinden; t = Welch t (>2 ayrisma sayilir)")
    print(HEADER)
    out = open(args.out, "a", encoding="utf-8") if args.out else None
    for name in args.regimes:
        if name not in REGIMES:
            raise SystemExit(f"bilinmeyen rejim {name!r}; secenekler: {', '.join(REGIMES)}")
        r = evaluate(name, args.steps, seed)
        print(format_row(r), flush=True)
        if out:
            out.write(json.dumps(r) + "\n")
            out.flush()
    if out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
