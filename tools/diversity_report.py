#!/usr/bin/env python3
"""Faz 7 cesitlilik raporu: bir kosum "olculebilir cesitlilikte" mi?

Olcut (docs/faz7/olcut.md, kosumlardan ONCE ilan edildi):
  son ceyrekte  etkin soy >= 5.0  VE  dis-grup firsat payi >= %10.

Ucu ayri raporlanir, cunku birbirinin yerine gecmezler:
  ETIKET cesitliligi  `lineage_effective`   (split_rate bunu bedavaya sisirir)
  GENOM cesitliligi   `weight_diversity`    (asil olan)
  GERCEKLESEN akrabalik `genetic_r`         (komsunun genom benzerligi)

Cesitliligin BEDELI de ayni tabloda: korunum, yetkinlik (kisi basi toplama),
cevresel sinirlama (at_cap / repro_blocked), tukenme.

    python tools/diversity_report.py runs/f7a_taze_s42 runs/f7a_tohumlu_s42
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LINEAGE_MIN = 5.0      # olcut 1B (Faz 7) ve olcut 1 (Faz 8)
OUTGROUP_MIN = 0.10    # olcut 1B (Faz 7) ve olcut 2 (Faz 8)
# --- Faz 8 ek olcutleri (docs/faz8/olcut.md, kosumlardan ONCE ilan edildi) ---
LARGEST_MAX = 0.80     # olcut 3: supurge yok
POP_MIN_VS_BASE = 0.50    # olcut 4: populasyon kontrolun en az yarisi
FORAGE_MIN_VS_BASE = 0.70  # olcut 4: kisi basi toplama kontrolun en az %70'i


def rows(run: str, name: str) -> list[dict]:
    path = os.path.join(run, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tail(rs: list[dict], key: str, frac: float = 0.25) -> np.ndarray:
    vals = [r.get(key) for r in rs]
    cut = int(len(vals) * (1.0 - frac))
    return np.array([float(v) for v in vals[cut:] if v not in (None, "")], float)


def mean(rs, key, frac=0.25) -> float:
    s = tail(rs, key, frac)
    return float(s.mean()) if s.size else float("nan")


def energy_created(run: str) -> float:
    total = 0.0
    for r in rows(run, "metrics.csv"):
        v = r.get("energy_created")
        if v not in (None, ""):
            total += float(v)
    return total


def faz8(runs: list[str], base: str) -> int:
    """Faz 8'in DORT PARCALI olcutu: cesitlilik + supurge yok + koloni saglikli.

    Ilk ucu tek basina yetmez: "cesitliligi koloniyi cokerterek korumak"
    gecersizdir (Faz 3/4 dersi), bu yuzden 4. parca kontrole karsi okunur.
    """
    b = rows(base, "generations.csv")
    if not b:
        raise SystemExit(f"taban kosumu bulunamadi: {base}")
    b_pop, b_for = mean(b, "population"), mean(b, "forage_per_capita")
    print("=" * 104)
    print(f"FAZ 8 OLCUTU — taban: {os.path.basename(base.rstrip('/'))} "
          f"(N {b_pop:.0f}, topla/kisi {b_for:.5f})")
    print("=" * 104)
    print(f"  {'kosum':26s} {'etkinSoy':>9s} {'disPay':>8s} {'enBuyuk':>8s} "
          f"{'N/taban':>8s} {'topla/taban':>12s} {'gider':>10s} {'karar':>8s}")
    passed = usable = 0
    for run in runs:
        g = rows(run, "generations.csv")
        name = os.path.basename(run.rstrip("/"))
        if not g:
            print(f"  {name:26s}  (kosum yok)")
            continue
        usable += 1
        lin = mean(g, "lineage_effective")
        ok, od = mean(g, "opp_kin"), mean(g, "opp_nonkin")
        share = od / (ok + od) if (ok + od) > 0 else float("nan")
        largest = mean(g, "lineage_largest")
        pop_r = mean(g, "population") / b_pop if b_pop else float("nan")
        for_r = mean(g, "forage_per_capita") / b_for if b_for else float("nan")
        good = (lin >= LINEAGE_MIN and share >= OUTGROUP_MIN
                and largest < LARGEST_MAX
                and pop_r >= POP_MIN_VS_BASE and for_r >= FORAGE_MIN_VS_BASE)
        passed += good
        print(f"  {name:26s} {lin:9.2f} {share*100:7.1f}% {largest*100:7.1f}% "
              f"{pop_r*100:7.0f}% {for_r*100:11.0f}% {mean(g,'crowding_drain'):10.1f} "
              f"{'GECTI' if good else 'GECMEDI':>8s}")
    print(f"\n  esikler: etkin soy >= {LINEAGE_MIN}, dis-grup >= {OUTGROUP_MIN*100:.0f}%, "
          f"en buyuk soy < {LARGEST_MAX*100:.0f}%,")
    print(f"           N >= taban'in {POP_MIN_VS_BASE*100:.0f}%'i, "
          f"topla/kisi >= taban'in {FORAGE_MIN_VS_BASE*100:.0f}%'i")
    print(f"  ozet: {passed}/{usable} kosum DORT olcutu birden gecti")
    print("\n  ⚠ DONGUSELLIK: ceza dogrudan ETIKETE bakiyor, yani etiket")
    print("  cesitliliginin yukselmesi kismen tanim geregidir. Asagidaki")
    print("  'ETIKET vs GENOM' tablosu olmadan 'cesitlilik korundu' denemez.")
    return 0


def report(runs: list[str]) -> int:
    print("=" * 104)
    print(f"OLCUT 1B — etkin soy >= {LINEAGE_MIN} VE dis-grup payi >= "
          f"{OUTGROUP_MIN*100:.0f}% (son ceyrek)")
    print("=" * 104)
    print(f"  {'kosum':24s} {'etkinSoy':>9s} {'soySayi':>8s} {'disPay':>8s} "
          f"{'ilkDonem':>9s} {'durum':>8s}")
    passed = 0
    usable = 0
    for run in runs:
        g = rows(run, "generations.csv")
        name = os.path.basename(run.rstrip("/"))
        if not g:
            print(f"  {name:24s}  (kosum yok)")
            continue
        usable += 1
        lin = mean(g, "lineage_effective")
        ok, od = mean(g, "opp_kin"), mean(g, "opp_nonkin")
        share = od / (ok + od) if (ok + od) > 0 else float("nan")
        good = lin >= LINEAGE_MIN and share >= OUTGROUP_MIN
        passed += good
        print(f"  {name:24s} {lin:9.2f} {mean(g,'lineage_count'):8.1f} "
              f"{share*100:7.1f}% {float(g[0]['lineage_effective']):9.2f} "
              f"{'GECTI' if good else 'GECMEDI':>8s}")
    print(f"\n  ozet: {passed}/{usable} kosum olculebilir cesitlilikte")
    print("  'ilkDonem' sutunu: baslangicta herkesin benzersiz soyismi vardir;")
    print("  cokus KOSUM ICINDE olur. Ikisi arasindaki fark surukleme degil,")
    print("  cogu zaman bir SECILIM SUPURGESIDIR (tek soy hepsini alir).")

    print()
    print("=" * 104)
    print("ETIKET vs GENOM — ayni sey degildir")
    print("=" * 104)
    print(f"  {'kosum':24s} {'etkinSoy':>9s} {'agirlikCes':>11s} {'paramCes':>10s} "
          f"{'genetic_r':>10s} {'gocmen':>8s}")
    for run in runs:
        g = rows(run, "generations.csv")
        if not g:
            continue
        print(f"  {os.path.basename(run.rstrip('/')):24s} {mean(g,'lineage_effective'):9.2f} "
              f"{mean(g,'weight_diversity'):11.4f} {mean(g,'behavior_diversity'):10.4f} "
              f"{mean(g,'genetic_r'):10.3f} {mean(g,'immigrants'):8.1f}")
    print("\n  `split_rate` yalnizca ilk sutunu buyutur: bolunen soy bolundugu")
    print("  anda ebeveyniyle GENETIK OLARAK AYNIDIR. Bir mekanizma 'cesitlilik")
    print("  uretti' diye raporlanamaz, genom sutunlari da yukselmedikce.")

    print()
    print("=" * 104)
    print("OLCUT 1C — cesitliligin BEDELI")
    print("=" * 104)
    print(f"  {'kosum':24s} {'E_yaratilan':>12s} {'N':>6s} {'topla/kisi':>11s} "
          f"{'isbirligi%':>11s} {'yanan ureme':>12s} {'tukenme':>8s}")
    for run in runs:
        g = rows(run, "generations.csv")
        if not g:
            continue
        ec = energy_created(run)
        flag = "" if abs(ec) < 1e-6 else "  ⚠GECERSIZ"
        n = mean(g, "population")
        print(f"  {os.path.basename(run.rstrip('/')):24s} {ec:12.1f} {n:6.0f} "
              f"{mean(g,'forage_per_capita'):11.5f} {mean(g,'cooperation_rate')*100:10.2f}% "
              f"{mean(g,'repro_blocked'):12.1f} {'EVET' if n < 1 else 'hayir':>8s}{flag}")
    print("\n  Taze koloni ACEMI baslar: `topla/kisi` dusuyorsa cesitliligin")
    print("  bedeli yetkinliktir ve sosyal olcumler o zemine gore okunur.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 7/8 cesitlilik raporu")
    ap.add_argument("runs", nargs="+", help="runs/<name> dizinleri")
    ap.add_argument("--faz8-taban", default=None,
                    help="Faz 8 dort parcali olcutu icin TABAN kosumu (kaldirac kapali)")
    args = ap.parse_args(argv)
    if args.faz8_taban:
        faz8(args.runs, args.faz8_taban)
        print()
    return report(args.runs)


if __name__ == "__main__":
    raise SystemExit(main())
