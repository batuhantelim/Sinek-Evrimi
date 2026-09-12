#!/usr/bin/env python3
"""FAZ 4 tani — rejim bistabilitesi: havza haritalama (Bolum A).

Faz 4 adim 1'in asil bulgusu avci degildi: koloni iki kararli rejim arasinda
salaniyor ve bu salinim avcinin etkisinden BUYUK. Melez soyisim eklemeden once
zeminin tek kararli olmasi gerek.

  "seyrek toplayici" : isbirligi dusuk, dagidik, yemek topluyor
  "yogun paylasim yumagi" : isbirligi yuksek, kumelenme ~1, toplayicilik dusuk

Bu arac AVCIYI KAPATIR (bistabilite avcisiz da var; avci bu tanida gurultu) ve
yalnizca seed'i degistirerek ayni rejimi cok kez kosar. Yeni davranis mekanigi
YOK.

Siniflandirma esigi UYDURULMAZ, veriden turetilir: kisi basi toplama hizi
sirlanip en buyuk BOSLUK bulunur, esik o bosugun ortasidir. Bosluk dagilimin
yayilimina gore kucukse "bimodal degil" denir ve esik raporlanmaz.

    python tools/basin_map.py --seeds 1 2 3 --out runs/faz4tani/A.jsonl
    python tools/basin_map.py --summary runs/faz4tani/A.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from seed_sweep import FIXED, REGIME, SEED_POP, series  # noqa: E402

#: Avci bu tanida SABIT: kapali. REGIME zaten kapali tutuyor, burada
#: niyeti acikca yaziyoruz ki bir gun REGIME degisirse tarama sessizce
#: baska bir deney olmasin (`tests/test_tools.py::TestBasinMap`).
PREDATOR_OFF = "rules.predator.enabled=false"

#: Havzayi tanimlayan iki eksen. Ikisi de KISI BASI mutlak hiz (oran degil).
AXIS_FORAGE = "forage_per_capita"
AXIS_COOP = "cooperation_rate"


def run_once(seed: int, steps: int, seed_pop: str | None,
             extra: list[str] | None = None) -> list[dict]:
    """Tek kosum, kontrolsuz: burada in/out ayrimcilik olculmuyor, REJIM olculuyor."""
    from sinek.config import load_config
    from sinek.persistence import load_population
    from sinek.simulation import Simulation

    ov = FIXED + REGIME + [PREDATOR_OFF] + list(extra or []) + [f"seed={seed}"]
    cfg = load_config(overrides=ov)
    genomes = None
    if seed_pop and os.path.exists(seed_pop):
        genomes, _meta = load_population(seed_pop, cfg)
    sim = Simulation(cfg, initial_genomes=genomes)
    sim.run(steps)
    rows = sim.generation_rows
    for r in rows:
        r["_extinct_at"] = sim.extinct_at or 0
    return rows


def read_rows(run_dir: str) -> list[dict]:
    path = run_dir if run_dir.endswith(".csv") else os.path.join(run_dir, "generations.csv")
    if not os.path.exists(path):
        raise SystemExit(f"bulunamadi: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def describe(seed: int, rows: list[dict], label: str = "", seconds: float = 0.0) -> dict:
    """Bir kosumu havza koordinatlarina indirger."""
    if not rows:
        raise SystemExit(f"seed {seed}: kosum bos dondu")

    def q(key, frac=0.25):
        return float(series(rows, key, frac).mean())

    pops = series(rows, "population", 1.0)
    return {
        "seed": seed,
        "label": label,
        "seconds": round(seconds, 1),
        "epochs": len(rows),
        "extinct_at": int(float(rows[-1].get("_extinct_at", 0) or 0)),
        # --- havza koordinatlari (kisi basi, mutlak) ---
        "forage": q(AXIS_FORAGE),
        "coop": q(AXIS_COOP),
        "share_pc": q("share_per_capita"),
        "clustering": q("clustering"),
        # --- koloni sagligi ---
        "population": q("population"),
        "pop_min": float(pops.min()),
        "starve_share": q("death_starved") / max(1e-9, q("deaths")),
        # --- yan etkiler: kaldiracin ne yaptigini olcmeden yorum yok ---
        "assortment": q("kin_assortment", 0.5),
        "lineage_eff": q("lineage_effective"),
        "food_fill": q("food_fill"),
        "opp_kin": q("opp_kin"),
        "opp_nonkin": q("opp_nonkin"),
        "out_share": q("opp_nonkin") / max(1e-9, q("opp_kin") + q("opp_nonkin")),
        "energy_mean": q("mean_fitness") if "mean_fitness" in rows[0] else 0.0,
        "bc_ratio": q("bc_ratio", 0.5),
    }


# ------------------------------------------------------------- esik turetme
def largest_gap_threshold(values: np.ndarray) -> dict:
    """Esigi veriden turet: sirali degerlerdeki EN BUYUK bosluk.

    `gap_ratio` = en buyuk bosluk / (ikinci en buyuk bosluk). 1'e yakinsa
    dagilim duz bir yelpazedir (bimodal degil); buyukse gercek bir catal var.
    `spread_share` = en buyuk bosluk / toplam aralik: catalin ne kadar genis
    oldugu.
    """
    v = np.sort(np.asarray(values, dtype=np.float64))
    if v.size < 4:
        return {"threshold": float("nan"), "gap": 0.0, "gap_ratio": 1.0,
                "spread_share": 0.0, "n_low": 0, "n_high": 0}
    gaps = np.diff(v)
    i = int(np.argmax(gaps))
    biggest = float(gaps[i])
    rest = np.delete(gaps, i)
    second = float(rest.max()) if rest.size else 0.0
    rng = float(v[-1] - v[0])
    thr = float((v[i] + v[i + 1]) / 2.0)
    return {
        "threshold": thr,
        "gap": biggest,
        "gap_ratio": biggest / second if second > 1e-12 else float("inf"),
        "spread_share": biggest / rng if rng > 1e-12 else 0.0,
        "n_low": int(i + 1),
        "n_high": int(v.size - i - 1),
    }


def classify(rows: list[dict], axis: str = "forage") -> tuple[dict, list[str]]:
    """Veriden turetilmis esikle her kosumu etiketler.

    Toplama hizi esigin ALTINDA -> 'yumak' (enerji dolastiriliyor, toplanmiyor),
    USTUNDE -> 'toplayici'.
    """
    vals = np.array([r[axis] for r in rows], dtype=np.float64)
    info = largest_gap_threshold(vals)
    thr = info["threshold"]
    labels = ["?" if np.isnan(thr) else ("yumak" if v < thr else "toplayici") for v in vals]
    return info, labels


def summarize(path: str, axis: str = "forage") -> None:
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    if not rows:
        raise SystemExit(f"bos: {path}")
    rows.sort(key=lambda r: (r.get("label", ""), r["seed"]))

    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r.get("label", ""), []).append(r)

    for label, grp in groups.items():
        info, labels = classify(grp, axis)
        title = f"HAVZA HARITASI — {len(grp)} seed" + (f"  [{label}]" if label else "")
        print("=" * 104)
        print(title)
        print("  toplama/paylasim: ajan-adim basina KISI BASI hiz (oran degil)")
        print("=" * 104)
        print(f"  {'seed':>6} {'toplama':>9} {'paylasim':>9} {'isbirligi':>10} {'kume':>7} "
              f"{'doluluk':>8} {'pop':>6} {'popdip':>7} {'aclik%':>7} {'r':>6} {'soy':>6} {'rejim':>10}")
        order = np.argsort([g[axis] for g in grp])
        for i in order:
            g, lab = grp[int(i)], labels[int(i)]
            print(f"  {g['seed']:>6} {g['forage']:9.4f} {g['share_pc']:9.4f} "
                  f"{g['coop'] * 100:9.2f}% {g['clustering']:7.3f} {g['food_fill']:8.3f} "
                  f"{g['population']:6.0f} {g['pop_min']:7.0f} {g['starve_share'] * 100:6.1f}% "
                  f"{g['assortment']:6.3f} {g['lineage_eff']:6.2f} {lab:>10}")

        print()
        print("  --- esik VERIDEN turetildi (en buyuk bosluk) ---")
        if np.isnan(info["threshold"]):
            print("  yeterli nokta yok (n < 4)")
        else:
            print(f"  esik ({axis})      : {info['threshold']:.4f}")
            print(f"  en buyuk bosluk    : {info['gap']:.4f}  "
                  f"(aralikta %{info['spread_share'] * 100:.0f}'lik pay)")
            print(f"  bosluk orani       : {info['gap_ratio']:.2f}× "
                  f"(ikinci en buyuk bosluga gore)")
            print(f"  bolunme            : {info['n_low']} yumak / {info['n_high']} toplayici")
            verdict = (
                "BIMODAL gorunuyor" if info["gap_ratio"] >= 2.0 and info["spread_share"] >= 0.25
                else "bimodal DEGIL — tek tepe + yayilim gibi"
            )
            print(f"  karar              : {verdict}")

        # rejim basina ozet
        print()
        for name in ("yumak", "toplayici"):
            sel = [g for g, lab in zip(grp, labels) if lab == name]
            if not sel:
                continue
            def m(k):
                return float(np.mean([s[k] for s in sel]))
            def sd(k):
                return float(np.std([s[k] for s in sel], ddof=1)) if len(sel) > 1 else 0.0
            print(f"  [{name}] n={len(sel)}  toplama {m('forage'):.4f}±{sd('forage'):.4f}  "
                  f"paylasim {m('share_pc'):.4f}  isbirligi %{m('coop') * 100:.1f}  "
                  f"kume {m('clustering'):.3f}  pop {m('population'):.0f} (dip {m('pop_min'):.0f})  "
                  f"aclik %{m('starve_share') * 100:.0f}  r {m('assortment'):.3f}  "
                  f"soy {m('lineage_eff'):.1f}")
        print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 4 tani: rejim havzasi haritalama")
    ap.add_argument("--seeds", nargs="*", type=int, default=[])
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default="", help="kosul etiketi (Bolum B/C icin)")
    ap.add_argument("--set", dest="extra", action="append", default=[],
                    help="ek override (Bolum B kaldiraclari)")
    ap.add_argument("--no-seed-pop", action="store_true")
    ap.add_argument("--summary", default=None)
    ap.add_argument("--axis", default="forage", choices=["forage", "coop", "clustering"])
    ap.add_argument("--from-runs", nargs="*", default=None,
                    help="hazir kosum klasorleri (run.py ile paralel kosuldugunda)")
    ap.add_argument("--seed-labels", nargs="*", type=int, default=None)
    args = ap.parse_args(argv)

    if args.summary:
        summarize(args.summary, args.axis)
        return 0

    out = None
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        out = open(args.out, "a", encoding="utf-8")

    records: list[dict] = []
    if args.from_runs:
        labels = args.seed_labels or list(range(len(args.from_runs)))
        for seed, d in zip(labels, args.from_runs):
            records.append(describe(seed, read_rows(d), args.label))
    else:
        if not args.seeds:
            raise SystemExit("--seeds, --from-runs ya da --summary verin")
        pop = None if args.no_seed_pop else os.path.join(ROOT, SEED_POP)
        for seed in args.seeds:
            t0 = time.time()
            rows = run_once(seed, args.steps, pop, args.extra)
            records.append(describe(seed, rows, args.label, time.time() - t0))
            print(f"  seed {seed}: toplama {records[-1]['forage']:.4f} "
                  f"isbirligi %{records[-1]['coop'] * 100:.1f} "
                  f"kume {records[-1]['clustering']:.3f}", flush=True)

    for r in records:
        if out:
            out.write(json.dumps(r) + "\n")
    if out:
        out.close()
        print(f"\nyazildi: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
