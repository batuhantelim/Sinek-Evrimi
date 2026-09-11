#!/usr/bin/env python3
"""Akrabalik sensoru SONDASI: beyin akrabaligi gercekten okuyor mu?

Simulasyondaki `kin_bias` metriginin ciddi bir gizli degiskeni var: akrabalar
uzamsal olarak kumelenir, kumeler yemek yamalarindadir, yamadaki sinekler daha
tok olur ve tok sinegin paylasacak butcesi vardir. Yani "akrabaya daha cok
paylasildi" bulgusu, hicbir ayrimcilik olmadan da ortaya cikabilir.

Bu arac o dugumu keser: ajanlari hic calistirmaz. Ayni sensor vektorunu
beyne iki kez verir; SADECE akrabalik kanali degisir (+1 akraba / -1 yabanci)
ve paylasim motorundaki farki olcer. Uzamsal etki, enerji, yogunluk — hepsi
sabit. Kalan fark saf ayrimciliktir.

    python tools/kin_probe.py runs/faz3/population.npz
    python tools/kin_probe.py runs/faz3/population.npz runs/faz3_kontrol/population.npz
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import M, N_SENSORS, S  # noqa: E402
from sinek.brains import make_brain  # noqa: E402
from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402

SETTLE = 6  # recurrent durumun oturmasi icin tekrar sayisi


def probe(genomes, cfg, samples: int = 200, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    # Ortak sensor havuzu: her genom AYNI girdileri gorur.
    base = rng.uniform(-1.0, 1.0, size=(samples, N_SENSORS)).astype(np.float32)
    base[:, S["bias"]] = 1.0
    for name in ("energy", "age", "food_here", "food_strength", "hazard_near", "crowd",
                 "neighbor_need"):
        base[:, S[name]] = rng.uniform(0.0, 1.0, samples)  # bu kanallar 0..1
    # Komsu HER IKI kosulda da var: tek degisen akrabalik olsun.
    base[:, S["near_agent"]] = 1.0

    diffs = []
    for genome in genomes:
        brain = make_brain(cfg, genome)
        outs = {}
        for kin_value in (1.0, -1.0):
            vals = []
            for row in base:
                s = row.copy()
                s[S["kin"]] = kin_value
                brain.reset()
                out = None
                for _ in range(SETTLE):  # ayni girdiyi tekrarlayip durumu oturt
                    out = brain.act(s, rng)
                vals.append(float(out[M["share"]]))
            outs[kin_value] = np.array(vals)
        diffs.append(float((outs[1.0] - outs[-1.0]).mean()))

    d = np.array(diffs)
    return {
        "n": len(d),
        "mean": float(d.mean()),
        "median": float(np.median(d)),
        "std": float(d.std()),
        "pos_frac": float((d > 0).mean()),
        "abs_mean": float(np.abs(d).mean()),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="akrabalik sensoru sondasi")
    ap.add_argument("populations", nargs="+", help="runs/<name>/population.npz")
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    args = ap.parse_args(argv)

    cfg = load_config(overrides=args.overrides)
    print("Sonda: ayni sensor vektoru, yalnizca akrabalik kanali degisiyor.")
    print(f"       paylasim motoru farki = ortalama(share | akraba) - ortalama(share | yabanci)")
    print(f"       {args.samples} sensor ornegi x genom basina\n")
    print(f"  {'kayit':34s} {'genom':>6} {'fark':>9} {'medyan':>9} {'akrabayi kayiran':>17}")
    for path in args.populations:
        genomes, _meta = load_population(path, cfg)
        r = probe(genomes, cfg, args.samples, args.seed)
        label = os.path.basename(os.path.dirname(path)) or path
        print(
            f"  {label:34s} {r['n']:6d} {r['mean']:+9.4f} {r['median']:+9.4f} "
            f"{r['pos_frac'] * 100:16.1f}%"
        )
    print("\n  fark ~0 ve kayirma ~%50 ise beyin akrabalik kanalini OKUMUYOR demektir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
