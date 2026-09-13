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


def probe(genomes, cfg, samples: int = 200, seed: int = 0,
          channel: str = "kin", values=(1.0, -1.0)) -> dict:
    rng = np.random.default_rng(seed)
    # Ortak sensor havuzu: her genom AYNI girdileri gorur.
    base = rng.uniform(-1.0, 1.0, size=(samples, N_SENSORS)).astype(np.float32)
    base[:, S["bias"]] = 1.0
    for name in ("energy", "age", "food_here", "food_strength", "hazard_near", "crowd",
                 "neighbor_need"):
        base[:, S[name]] = rng.uniform(0.0, 1.0, samples)  # bu kanallar 0..1
    # Komsu HER IKI kosulda da var: tek degisen `channel` olsun.
    base[:, S["near_agent"]] = 1.0
    if channel == "partner_ledger":
        # Faz 5: partner TANINIYOR olsun; tek degisen defterin ISARETI olsun.
        base[:, S["partner_known"]] = 1.0

    motors = [m for m in ("share", "attack") if m in M]
    diffs: dict[str, list[float]] = {m: [] for m in motors}
    for genome in genomes:
        brain = make_brain(cfg, genome)
        outs = {}
        for kin_value in values:
            vals = []
            for row in base:
                s = row.copy()
                s[S[channel]] = kin_value
                brain.reset()
                out = None
                for _ in range(SETTLE):  # ayni girdiyi tekrarlayip durumu oturt
                    out = brain.act(s, rng)
                vals.append([float(out[M[m]]) for m in motors])
            outs[kin_value] = np.array(vals)
        delta = (outs[values[0]] - outs[values[1]]).mean(axis=0)
        for i, m in enumerate(motors):
            diffs[m].append(float(delta[i]))

    result = {"n": len(genomes)}
    for m in motors:
        d = np.array(diffs[m])
        result[m] = {
            "mean": float(d.mean()),
            "median": float(np.median(d)),
            "pos_frac": float((d > 0).mean()),
        }
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="akrabalik sensoru sondasi")
    ap.add_argument("populations", nargs="+", help="runs/<name>/population.npz")
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    ap.add_argument(
        "--channel", default="kin",
        help="hangi kanal cevrilsin: kin (varsayilan) | partner_ledger (Faz 5)",
    )
    args = ap.parse_args(argv)

    cfg = load_config(overrides=args.overrides)
    etiket = {"kin": ("akrabalik", "akraba", "yabanci"),
              "partner_ledger": ("defter", "bana VERDI", "bana SALDIRDI")}
    ad, poz, neg = etiket.get(args.channel, (args.channel, "+1", "-1"))
    print(f"Sonda: ayni sensor vektoru, yalnizca {ad} kanali degisiyor.")
    print(f"       fark = ortalama(motor | {poz}) - ortalama(motor | {neg})")
    print(f"       {args.samples} sensor ornegi x genom basina\n")
    print(
        f"  {'kayit':30s} {'genom':>6} | {'PAYLAS fark':>12} {'kayiran':>8} "
        f"| {'SALDIR fark':>12} {'kayiran':>8}"
    )
    for path in args.populations:
        genomes, _meta = load_population(path, cfg)
        r = probe(genomes, cfg, args.samples, args.seed, args.channel)
        label = os.path.basename(os.path.dirname(path)) or path
        sh = r.get("share", {"mean": 0.0, "pos_frac": 0.0})
        at = r.get("attack")
        line = f"  {label:30s} {r['n']:6d} | {sh['mean']:+12.4f} {sh['pos_frac'] * 100:7.1f}%"
        if at:
            line += f" | {at['mean']:+12.4f} {at['pos_frac'] * 100:7.1f}%"
        print(line)
    print(f"\n  fark ~0 ve kayiran ~%50 ise beyin {ad} kanalini OKUMUYOR demektir.")
    print("  Parochial imza: PAYLAS farki POZITIF (akrabaya cok) ve")
    print("                  SALDIR farki NEGATIF (akrabaya az) olmali.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
