#!/usr/bin/env python3
"""FAZ 4 tani — 'fazla enerji bedava mi?' sondasi.

Populasyon `agents.max_count` tavaninda sikisinca ureme bir SLOT KUYRUGUNA
doner: adim basina ~1 dogum, 700 aday. O anda ureme esiginin (130) UZERINDEKI
bir ajanin fazla enerjisinin marjinal fitness degeri neredeyse sifirdir —
cunku bolunemez ve enerji tavani (160) zaten yakindir.

Eger paylasimlarin buyuk cogunlugu bu "zaten dolu" katmandan geliyorsa,
paylasim SECILIM ICIN NEREDEYSE BEDAVADIR ve secilim onu eleyemez: oran
suruklenerek doyar. Bu, davranisin evrimi degil muhasebenin bir deligidir.

Sonda ajanlari kisa sure kosturur ve paylasim firsatlarini/eylemlerini
VERICI ENERJI KATMANINA gore sayar (simulasyonun kendi katmanlari).

    python tools/surplus_probe.py runs/tani_s777 runs/tani_s42 --steps 600
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import ENERGY_BUCKETS, Simulation  # noqa: E402

from seed_sweep import FIXED, REGIME  # noqa: E402


def probe(run_dir: str, steps: int, seed: int) -> dict:
    pop = os.path.join(run_dir, "population.npz")
    if not os.path.exists(pop):
        raise SystemExit(f"bulunamadi: {pop}")
    cfg = load_config(overrides=FIXED + REGIME + ["rules.predator.enabled=false", f"seed={seed}"])
    genomes, _meta = load_population(pop, cfg)
    sim = Simulation(cfg, initial_genomes=genomes)
    sim.run(steps)
    st = sim.stats_total
    opp = [st.get(f"opp_kin_{b}", 0) + st.get(f"opp_non_{b}", 0) for b in range(ENERGY_BUCKETS)]
    shr = [st.get(f"shr_kin_{b}", 0) + st.get(f"shr_non_{b}", 0) for b in range(ENERGY_BUCKETS)]
    return {
        "name": os.path.basename(run_dir.rstrip("/")),
        "opp": opp,
        "shr": shr,
        "e_max": sim.physics.energy_max,
        "repro": float(cfg.agents.reproduction.energy_threshold),
        "pop": len(sim.agents),
        "cap": int(cfg.agents.max_count),
        "births": st.get("births", 0),
        "steps": steps,
    }


def report(rows: list[dict]) -> None:
    e_max = rows[0]["e_max"]
    repro = rows[0]["repro"]
    width = e_max / ENERGY_BUCKETS
    print("=" * 92)
    print("FAZLA ENERJI BEDAVA MI? — paylasimin VERICI ENERJI katmanina gore dagilimi")
    print(f"  enerji tavani {e_max:.0f} | ureme esigi {repro:.0f} | "
          f"katman genisligi {width:.0f} | populasyon tavani {rows[0]['cap']}")
    print(f"  dogum/adim: " + ", ".join(
        f"{r['name']} {r['births'] / max(1, r['steps']):.2f}" for r in rows))
    print("=" * 92)
    head = f"  {'katman (enerji)':>18} {'ureme?':>8}"
    for r in rows:
        head += f" | {r['name'][:16]:>16}"
    print(head)
    for b in range(ENERGY_BUCKETS):
        lo, hi = b * width, (b + 1) * width
        can = "EVET" if lo >= repro else ("kismi" if hi > repro else "hayir")
        line = f"  {f'{lo:.0f}-{hi:.0f}':>18} {can:>8}"
        for r in rows:
            tot = sum(r["shr"]) or 1
            line += f" | {r['shr'][b] / tot * 100:6.1f}% pay ({r['shr'][b] / max(1, r['opp'][b]) * 100:5.1f}%)"
        print(line)
    print()
    print("  sutunlar: paylasimlarin yuzde kaci o katmandan geldi "
          "(parantez: o katmandaki FIRSAT basina paylasma olasiligi)")
    for r in rows:
        tot = sum(r["shr"]) or 1
        top = r["shr"][ENERGY_BUCKETS - 1] / tot
        probs = [r["shr"][b] / max(1, r["opp"][b]) for b in range(ENERGY_BUCKETS)]
        lo = max(probs[1:3])          # yoksul-orta katmanlar
        hi = probs[-1]                # ureme esigini kapsayan katman
        print(f"  {r['name']:>18}: paylasimlarin %{top * 100:.1f}'i en ust katmandan "
              f"(ureme esigini kapsar); yoksul katmanda paylasma olasiligi "
              f"%{lo * 100:.1f}, en ust katmanda %{hi * 100:.1f}")
    print()
    print("  YORUM: eger paylasim YALNIZCA en ust (fazla) katmandan geliyorsa 'bedava "
          "surplus' aciklamasi tutar. Yoksul katmanda da yuksek olasilikla paylasiliyorsa "
          "paylasim GERCEKTEN maliyetlidir ve aciklama baska yerde aranmalidir.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="fazla enerji bedava mi sondasi")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    report([probe(r, args.steps, args.seed) for r in args.runs])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
