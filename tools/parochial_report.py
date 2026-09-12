#!/usr/bin/env python3
"""Dort hucreli in/out matrisi + in-grup fedakarlik ile dis-grup dusmanligin
birlikte hareket edip etmedigi.

Asil felsefi soru: "iyilik ve oteki'ne kotuluk ayni madalyonun iki yuzu mu?"
Olcumu su: nesil-nesil in-grup paylasim egrisi ile dis-grup saldiri egrisi
BIRLIKTE mi yukseliyor (Pearson r)?

Her sey karistirma kontroluyle yan yana yazilir — etiket bilgisizken iki
egri de duz kalmali. Kalmiyorsa sinyal yapayliktir.

    python tools/parochial_report.py runs/faz3b_saldiri runs/faz3b_kontrol
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CELLS = [
    ("coop_in_group", "PAYLAS  in-grup"),
    ("coop_out_group", "PAYLAS  dis-grup"),
    ("attack_in_group", "SALDIR  in-grup"),
    ("attack_out_group", "SALDIR  dis-grup"),
]


def read(run: str) -> list[dict]:
    path = run if run.endswith(".csv") else os.path.join(run, "generations.csv")
    if not os.path.exists(path):
        raise SystemExit(f"bulunamadi: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def col(rows: list[dict], key: str) -> np.ndarray:
    return np.array([float(r[key]) for r in rows], dtype=np.float64)


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3 or a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def trend(y: np.ndarray) -> float:
    """Egrinin egimi (donem basina), basit dogrusal regresyon."""
    if y.size < 3:
        return 0.0
    x = np.arange(y.size, dtype=np.float64)
    return float(np.polyfit(x, y, 1)[0])


def quarters(rows: list[dict], key: str) -> list[float]:
    y = col(rows, key)
    q = max(1, y.size // 4)
    return [float(y[i * q : (i + 1) * q].mean()) for i in range(4)]


def report(runs: list[str]) -> None:
    data = [(os.path.basename(r.rstrip("/")), read(r)) for r in runs]

    print("=" * 78)
    print("DORT HUCRELI MATRIS — son ceyrek ortalamasi (firsata kosullu, %)")
    print("=" * 78)
    header = f"  {'hucre':22s}" + "".join(f"{n[:18]:>19s}" for n, _ in data)
    print(header)
    for key, label in CELLS:
        line = f"  {label:22s}"
        for _n, rows in data:
            line += f"{quarters(rows, key)[-1] * 100:18.3f}%"
        print(line)

    print()
    print("  Parochial imza beklentisi: in-grupta PAYLAS yuksek + SALDIR dusuk,")
    print("  dis-grupta tam tersi. Kontrolde dort hucre de birbirine yakin olmali.")

    print()
    print("=" * 78)
    print("CEYREKLER BOYUNCA EGILIM (4 ceyrek, % ve donem basina egim)")
    print("=" * 78)
    for name, rows in data:
        print(f"  -- {name} ({len(rows)} donem) --")
        for key, label in CELLS:
            q = quarters(rows, key)
            sl = trend(col(rows, key)) * 100
            arrow = "yukseliyor" if sl > 1e-4 else ("dusuyor" if sl < -1e-4 else "duz")
            print(
                f"     {label:22s} " + " -> ".join(f"{v * 100:6.3f}" for v in q)
                + f"   egim {sl:+.4f}/donem  {arrow}"
            )

    print()
    print("=" * 78)
    print("BIRLIKTE HAREKET — in-grup fedakarlik vs dis-grup dusmanlik")
    print("=" * 78)
    print(f"  {'kosum':24s} {'r(ic-paylas, dis-saldir)':>26s} {'r(duzeltilmis)':>16s}")
    for name, rows in data:
        r_raw = pearson(col(rows, "coop_in_group"), col(rows, "attack_out_group"))
        r_adj = pearson(col(rows, "kin_bias_adj"), -col(rows, "attack_kin_bias_adj"))
        print(f"  {name:24s} {r_raw:26.3f} {r_adj:16.3f}")
    print()
    print("  Birinci sutun: iki ham egri birlikte mi hareket ediyor.")
    print("  Ikinci sutun: konfound duzeltilmis ayrimcilik olculeri — paylasimda")
    print("  akraba kayirma ile saldirida akraba ESIRGEME birlikte mi gidiyor.")
    print("  ASIL KANIT bu ikincisidir; birincisi ortak trendlerden sisebilir.")

    print()
    print("=" * 78)
    print("ORNEKLEM VE BAGLAM (son ceyrek)")
    print("=" * 78)
    for name, rows in data:
        q = len(rows) // 4 or 1
        tail = rows[-q:]
        g = lambda k: float(np.mean([float(r[k]) for r in tail]))
        print(
            f"  {name:24s} opp_kin {g('opp_kin'):8.0f}  opp_dis {g('opp_nonkin'):8.0f}  "
            f"r(assort) {g('kin_assortment'):.3f}  soy {g('lineage_effective'):5.1f}  "
            f"oldurme {g('attack_kills'):7.0f}"
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="dort hucreli parochial altruism raporu")
    ap.add_argument("runs", nargs="+", help="runs/<name> dizinleri (ilki asil kosum)")
    args = ap.parse_args(argv)
    report(args.runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
