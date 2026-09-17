#!/usr/bin/env python3
"""FAZ 9 (revize) — SUREKLI AKRABALIK: zemin olculebilir kaldi mi?

Olcut: docs/faz9/olcut_surekli.md (koşumlardan ONCE ilan edildi).

  OLCUT B (ASIL)  melez ACIKKEN, surekli kolda son ceyrekte:
                    1. dis-grup firsat payi >= %10   (bilesen 1'de 1/3 seed)
                    2. etkin soy >= 5.0
                    3. genetic_r >= melez-yok kolunun YARISI
                    4. koloni saglikli: N >= %50, kisi basi toplama >= %70
  OLCUT C         lineage_effective ile dis-grup payi artik AYNI yonde mi
                  (bilesen 1'de ZIT yonde hareket ediyorlardi)
  OLCUT D         mandal (melez payi doyumu) hala duruyor mu — GOZLEM

Kollar: runs/<prefix>_{melezyok,ikili,surekli}_s<seed>

    python tools/continuous_kin_report.py --seeds 42 7 123
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.hybrid_report import energy_created, mean, rows  # noqa: E402

ARMS = ("melezyok", "ikili", "surekli")

#: Esikler olcut dosyalarindan gelir (test ikisini karsilastirir).
OUTGROUP_MIN = 0.10        # docs/faz7/olcut.md + olcut_surekli.md
LINEAGE_MIN = 5.0
GENETIC_R_MIN = 0.50       # melez-yok koluna oran
POP_MIN = 0.50
FORAGE_MIN = 0.70


def out_share(rs: list[dict]) -> float:
    """Dis-grup FIRSAT payi: yabanciyla karsilasma / tum karsilasmalar."""
    k, n = mean(rs, "opp_kin"), mean(rs, "opp_nonkin")
    return n / (k + n) if (k + n) else float("nan")


def out_share_series(rs: list[dict]) -> np.ndarray:
    out = []
    for r in rs:
        try:
            k, n = float(r["opp_kin"]), float(r["opp_nonkin"])
        except (KeyError, TypeError, ValueError):
            continue
        if k + n:
            out.append(n / (k + n))
    return np.array(out, dtype=float)


def collect(prefix: str, seeds: list[int]) -> dict:
    return {
        (arm, s): rows(os.path.join("runs", f"{prefix}_{arm}_s{s}"))
        for arm in ARMS for s in seeds
    }


def report(prefix: str, seeds: list[int]) -> int:
    d = collect(prefix, seeds)

    print("=" * 102)
    print("OLCUT B — melez ACIKKEN zemin olculebilir kaldi mi (surekli kol)")
    print("=" * 102)
    print(f"  {'seed':>5} {'kol':>10s} {'disPay':>8s} {'etkinSoy':>9s} {'genetic_r':>12s} "
          f"{'N':>7s} {'topla/kisi':>11s} {'melezPay':>9s} {'kin_r':>7s} {'durum':>8s}")
    passed = 0
    usable = 0
    for s in seeds:
        base = d[("melezyok", s)]
        if not base:
            print(f"  {s:5d}  (melez-yok kolu yok)")
            continue
        gr_b, n_b, f_b = (mean(base, "genetic_r"), mean(base, "population"),
                          mean(base, "forage_per_capita"))
        for arm in ARMS:
            r = d[(arm, s)]
            if not r:
                continue
            osh, le = out_share(r), mean(r, "lineage_effective")
            gr, n, f = mean(r, "genetic_r"), mean(r, "population"), mean(r, "forage_per_capita")
            ok = (osh >= OUTGROUP_MIN and le >= LINEAGE_MIN
                  and gr >= GENETIC_R_MIN * gr_b
                  and n >= POP_MIN * n_b and f >= FORAGE_MIN * f_b)
            if arm == "surekli":
                usable += 1
                passed += ok
            ratio = gr / gr_b if gr_b else float("nan")
            print(f"  {s:5d} {arm:>10s} {osh*100:7.1f}% {le:9.2f} "
                  f"{f'{gr:.2f} ({ratio:.2f}x)':>12s} {n:7.0f} {f:11.4f} "
                  f"{mean(r,'hybrid_share')*100:8.1f}% {mean(r,'kin_r_mean'):7.3f} "
                  f"{('GECTI' if ok else '-'):>8s}")
        print()
    print(f"  esikler: dis-grup >= {OUTGROUP_MIN*100:.0f}%, etkin soy >= {LINEAGE_MIN:.1f}, "
          f"genetic_r >= {GENETIC_R_MIN:.2f}x, N >= {POP_MIN:.2f}x, toplama >= {FORAGE_MIN:.2f}x")
    print(f"  OLCUT B: {passed}/{usable} seed  ->  "
          f"{'GECTI' if usable and passed == usable else 'GECMEDI'}")
    if not (usable and passed == usable):
        print("  ⚠ B gecmedi: bilesen 2 (soy-arasi matris) ve 3 (isbirligi kontrolu)")
        print("    BU ZEMINE KURULMAZ — bilesen 1'in dersi aynen gecerli.")

    print()
    print("=" * 102)
    print("KORUNUM — enerji defteri (her kol, her seed)")
    print("=" * 102)
    bad = 0
    for s in seeds:
        line = [f"  {s:5d}"]
        for arm in ARMS:
            run = os.path.join("runs", f"{prefix}_{arm}_s{s}")
            if not os.path.isdir(run):
                continue
            ec = energy_created(run)
            bad += abs(ec) > 1e-6
            line.append(f"{arm}={ec:+.3f}")
        print("  ".join(line))
    print(f"  energy_created != 0 olan kol: {bad}  "
          f"({'TAMAM' if not bad else '⚠ GECERSIZ'})")

    print()
    print("=" * 102)
    print("OLCUT C — `lineage_effective` ile dis-grup payi AYNI yonde mi")
    print("=" * 102)
    xs, ys = [], []
    for s in seeds:
        for arm in ARMS:
            r = d[(arm, s)]
            if not r:
                continue
            le, osh = mean(r, "lineage_effective"), out_share(r)
            if not (np.isnan(le) or np.isnan(osh)):
                xs.append(le); ys.append(osh)
    if len(xs) >= 3 and np.std(xs) > 1e-9 and np.std(ys) > 1e-9:
        c = float(np.corrcoef(xs, ys)[0, 1])
        print(f"  kol x seed noktalari (n={len(xs)}): corr(etkin soy, dis-grup payi) = {c:+.3f}")
        print(f"  {'-> AYNI yonde (bilesen 1: ZIT yondeydi)' if c > 0 else '-> HALA ZIT yonde'}")
    else:
        print("  yetersiz nokta")
    print("  Not: bu bir OLCUT DEGIL, rapor edilen gozlemdir (olcut dosyasi boyle yaziyor).")

    print()
    print("=" * 102)
    print("OLCUT D — MANDAL hala duruyor mu (GOZLEM)")
    print("=" * 102)
    print(f"  {'seed':>5} {'kol':>10s} {'melez payi (ilk ceyrek -> son ceyrek)':>40s}")
    for s in seeds:
        for arm in ("ikili", "surekli"):
            r = d[(arm, s)]
            if not r:
                continue
            first = np.array([float(x["hybrid_share"]) for x in r[: max(1, len(r) // 4)]
                              if x.get("hybrid_share") not in (None, "")], float)
            f0 = float(first.mean()) if first.size else float("nan")
            f1 = mean(r, "hybrid_share")
            span = "%%%.1f -> %%%.1f" % (f0 * 100, f1 * 100)
            print(f"  {s:5d} {arm:>10s} {span:>40s}")
    print("  Surekli akrabalik mandali COZMEZ (kural ayni: melez saf doller);")
    print("  yalnizca mandalin olcum zeminine verdigi zarari tolere edip etmedigini sinar.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 9 revize: surekli akrabalik raporu")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123])
    ap.add_argument("--prefix", default="f9c", help="runs/<prefix>_<kol>_s<seed>")
    args = ap.parse_args(argv)
    return report(args.prefix, args.seeds)


if __name__ == "__main__":
    raise SystemExit(main())
