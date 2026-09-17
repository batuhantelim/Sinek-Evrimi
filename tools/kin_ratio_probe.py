#!/usr/bin/env python3
"""FAZ 9 (revize) — SUREKLI AKRABALIK FORMULUNU SECEN SONDA.

Iki aday var (docs/faz9/olcut_surekli.md, koşumlardan ONCE ilan edildi):

    jaccard : |kesisim| / |birlesim|        -> {A,B} vs {B,C} = 1/3
    mean    : |kesisim| / ortalama etiket boyu -> {A,B} vs {B,C} = 1/2

SECIM KURALI (onceden yazildi): kazanan, CIFT BAZINDA GENOM BENZERLIGIYLE
daha yuksek Pearson korelasyonu veren formuldur. Cift bazinda benzerlik,
`metrics.genetic_relatedness`'in regresyon tanimi cift karsiligidir:

    sim(a,b) = Sum_k (a_k - mu_k)(b_k - mu_k) / Sum_k (a_k - mu_k)^2

⚠ NEDEN OLCULUYOR: etiket akrabaligini SECMEK bir varsayimdir; hangi formulun
gercek genetik benzerligi daha iyi temsil ettigi ANCAK olculerek soylenebilir
(Faz 4.6 dersi: "r'yi etiketten degil genomdan okuyun"). Formul, olculebilirlik
sonucuna gore DEGIL, bu korelasyona gore secilir.

    python tools/kin_ratio_probe.py --seeds 42 7 123
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sinek.config import load_config  # noqa: E402
from sinek.lineage import kin_ratio  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

#: Melez ACIK olmali — yoksa butun etiketler saf, iki formul de OZDES olur
#: ve kalibrasyonun olcecegi hicbir sey kalmaz.
CONFIG = "experiments/faz9_surekli.yaml"
#: ⚠ KALIBRASYON TARAFSIZ ZEMINDE YAPILIR: kosum `binary` modda dondurulur,
#: yani populasyonu iki adaydan HICBIRI sekillendirmez. Aday formulle
#: kosup ayni formulu secmek kendi varsayimini olcmek olurdu (Faz 4.6 dersi:
#: "bir katsayiyi muhasebeye koyup onunla kanit uretmeyin").
BASE = ["viz.mode=none", "metrics.enabled=false",
        "rules.kinship.kin_mode=binary"]
MIN_PAIRS = 2000          # olcut dosyasinda ilan edilen asgari ornek


class Collector:
    """Son ceyrekte cift toplar: iki etiket orani + genom benzerligi."""

    def __init__(self, start_step: int, every: int = 25):
        self.start = start_step
        self.every = every
        self.jac: list[float] = []
        self.mean: list[float] = []
        self.A: list[np.ndarray] = []
        self.B: list[np.ndarray] = []
        self.hybrid_pairs = 0

    def observe(self, sim) -> None:
        if sim.step_index < self.start or sim.step_index % self.every:
            return
        for a in sim.agents:
            o = getattr(a, "nearest", None)
            if o is None or not o.alive or not a.genome.weights.size:
                continue
            g1, g2 = a.genome, o.genome
            args = (g1.surname, g1.surname2, g2.surname, g2.surname2)
            self.jac.append(kin_ratio(*args, "jaccard"))
            self.mean.append(kin_ratio(*args, "mean"))
            self.A.append(g1.weights)
            self.B.append(g2.weights)
            self.hybrid_pairs += (g1.surname2 >= 0) or (g2.surname2 >= 0)

    def report(self) -> dict:
        n = len(self.jac)
        if n < 20:
            return {"cift": n}
        A = np.array(self.A, dtype=np.float64)
        B = np.array(self.B, dtype=np.float64)
        mu = 0.5 * (A.mean(axis=0) + B.mean(axis=0))
        Ac, Bc = A - mu, B - mu
        var = float((Ac * Ac).sum()) / n      # cift basina ortalama varyans
        if var < 1e-12:
            return {"cift": n, "uyari": "genom varyansi yok"}
        sim_pair = (Ac * Bc).sum(axis=1) / var
        out = {"cift": n, "melezli_cift": int(self.hybrid_pairs),
               "genom_r_ort": float(sim_pair.mean())}
        for ad, vals in (("jaccard", self.jac), ("mean", self.mean)):
            v = np.array(vals, dtype=np.float64)
            out[f"{ad}_ort"] = float(v.mean())
            out[f"{ad}_std"] = float(v.std())
            if v.std() < 1e-12 or sim_pair.std() < 1e-12:
                out[f"{ad}_korelasyon"] = float("nan")
            else:
                out[f"{ad}_korelasyon"] = float(np.corrcoef(v, sim_pair)[0, 1])
        return out


def probe(seed: int, steps: int, extra: list[str]) -> dict:
    cfg = load_config(os.path.join(ROOT, CONFIG),
                      overrides=BASE + list(extra) + [f"seed={seed}"])
    sim = Simulation(cfg)
    col = Collector(start_step=int(steps * 0.75))
    sim.run(steps, on_step=col.observe)
    d = col.report()
    d["seed"] = seed
    d["populasyon"] = len(sim.agents)
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="surekli akrabalik formul sondasi")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123])
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--set", dest="extra", action="append", default=[])
    args = ap.parse_args(argv)

    rows = [probe(s, args.steps, args.extra) for s in args.seeds]
    print("=" * 84)
    print(f"SUREKLI AKRABALIK FORMUL SONDASI — {args.steps} adim, melez ACIK")
    print("=" * 84)
    print(f"{'seed':>6} {'cift':>7} {'melezli':>8} {'jaccard r':>11} {'mean r':>9} "
          f"{'jac ort':>8} {'mean ort':>9}")
    wins = {"jaccard": 0, "mean": 0}
    for d in rows:
        if d.get("cift", 0) < 20:
            print(f"{d['seed']:>6} {d.get('cift', 0):>7}   ORNEKLEM YETERSIZ")
            continue
        j, m = d["jaccard_korelasyon"], d["mean_korelasyon"]
        if not (np.isnan(j) or np.isnan(m)):
            wins["jaccard" if j > m else "mean"] += 1
        flag = "" if d["cift"] >= MIN_PAIRS else "  <- ORNEKLEM < %d" % MIN_PAIRS
        print(f"{d['seed']:>6} {d['cift']:>7} {d['melezli_cift']:>8} "
              f"{j:>11.4f} {m:>9.4f} {d['jaccard_ort']:>8.3f} {d['mean_ort']:>9.3f}{flag}")
    print("-" * 84)
    print(f"  genom benzerligiyle daha yuksek korelasyon: "
          f"jaccard {wins['jaccard']} seed, mean {wins['mean']} seed")
    if wins["jaccard"] and wins["mean"]:
        print("  ⚠ ISARET DONUYOR -> olcut geregi JACCARD secilir "
              "(fark olculemedi, yabanciyi daha genis tanimlayan alinir)")
    else:
        print(f"  SECILEN: {'jaccard' if wins['jaccard'] else 'mean'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
