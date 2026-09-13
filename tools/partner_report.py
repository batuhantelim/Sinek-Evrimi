#!/usr/bin/env python3
"""Faz 6 partner secimi raporu: UC KOL yan yana, her seed kendi kontroluyle.

Kollar:
  secim     — aday havuzundan genomdaki `pick_*` agirliklariyla secim
  secimsiz  — hedef yine EN YAKIN komsu (Faz 5'in birebir aynisi)
  rastgele  — havuz var ama secim rastgele ("yetenek" mi "akilli secim" mi)

Iki soru AYRI okunur:
  ASIL OLCUT (3): isbirligi orani SECIMSIZ kontrolden yukari ayristi mi?
  OLCUT (4):      bir secim POLITIKASI evrimlesti mi (secilen vs EN YAKIN,
                  rastgele-secim kontroluna karsi)?

Ucu de ancak ONKOSUL saglanmissa okunur: havuz >= 2.0 ve kararlarin >= %50'si
cok adayli. Havuz 1.0'a yakinsa "secim" diye bir sey yoktur ve iki kol birebir
ayni cikar (olculdu; bkz. docs/faz6/olcut.md EK).

    python tools/partner_report.py --seeds 42 7 123
    python tools/partner_report.py --prefix f6 --seeds 42 7 123
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ARMS = ("secim", "secimsiz", "rastgele")

# Onkosul esikleri — KOSUMLARDAN ONCE ilan edildi (docs/faz6/olcut.md EK).
POOL_MIN = 2.0
MULTI_MIN = 0.50
# Olcut 2: dis-grup firsat payi bunun altindaysa AKRABALIK kanadi okunmaz.
OUTGROUP_MIN = 0.10
# Olcut 3: Welch t bu esigi gecmeli VE yukari yonlu olmali.
T_MIN = 2.0


def read(path: str) -> list[dict] | None:
    csvpath = path if path.endswith(".csv") else os.path.join(path, "generations.csv")
    if not os.path.exists(csvpath):
        return None
    with open(csvpath, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tail(rows: list[dict], key: str, frac: float = 0.25) -> np.ndarray:
    """Son `frac` donemin serisi. Bos hucreler atlanir (eski CSV'ler)."""
    vals = [r.get(key) for r in rows]
    cut = int(len(vals) * (1.0 - frac))
    return np.array(
        [float(v) for v in vals[cut:] if v not in (None, "")], dtype=np.float64
    )


def mean(rows: list[dict], key: str, frac: float = 0.25) -> float:
    s = tail(rows, key, frac)
    return float(s.mean()) if s.size else float("nan")


def welch_t(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return 0.0
    se = math.sqrt(np.var(a, ddof=1) / a.size + np.var(b, ddof=1) / b.size)
    return float((a.mean() - b.mean()) / se) if se > 1e-12 else 0.0


def outgroup_share(rows: list[dict]) -> float:
    ok, od = mean(rows, "opp_kin"), mean(rows, "opp_nonkin")
    return od / (ok + od) if (ok + od) > 0 else float("nan")


def collect(prefix: str, seed: int) -> dict[str, list[dict] | None]:
    return {
        arm: read(os.path.join("runs", f"{prefix}_{arm}_s{seed}")) for arm in ARMS
    }


def report(prefix: str, seeds: list[int]) -> int:
    rows_per_seed = {s: collect(prefix, s) for s in seeds}

    print("=" * 92)
    print("ONKOSUL — aday havuzu (saglanmazsa hicbir olcut okunmaz)")
    print("=" * 92)
    print(f"  {'kol/seed':20s} {'havuz':>7s} {'cokAdayli':>10s} {'enYakinDegil':>13s} {'durum':>10s}")
    pre_ok = True
    for s in seeds:
        for arm in ("secim", "rastgele"):
            r = rows_per_seed[s][arm]
            if r is None:
                print(f"  {arm+'/'+str(s):20s}  (kosum yok)")
                pre_ok = False
                continue
            pool, multi = mean(r, "pool_size"), mean(r, "pool_multi")
            ok = pool >= POOL_MIN and multi >= MULTI_MIN
            pre_ok = pre_ok and ok
            print(
                f"  {arm+'/'+str(s):20s} {pool:7.2f} {multi*100:9.1f}% "
                f"{mean(r,'pick_not_nearest')*100:12.1f}% {'GECTI' if ok else 'GECMEDI':>10s}"
            )
    print(f"\n  esik: havuz >= {POOL_MIN}, cok adayli karar >= {MULTI_MIN*100:.0f}%")
    if not pre_ok:
        print("  ⚠ ONKOSUL SAGLANMADI — asagidaki ASIL OLCUT okunmaz.")

    print()
    print("=" * 92)
    print("KORUNUM (olcut 1) ve OLCULEBILIRLIK (olcut 2)")
    print("=" * 92)
    print(f"  {'kol/seed':20s} {'E_yaratilan':>12s} {'N':>6s} {'disPay':>8s} {'etkinSoy':>9s} {'topla/kisi':>11s}")
    for s in seeds:
        for arm in ARMS:
            r = rows_per_seed[s][arm]
            if r is None:
                continue
            ec = mean(r, "energy_created")
            flag = "" if abs(ec) < 1e-6 else "  ⚠GECERSIZ"
            og = outgroup_share(r)
            og_flag = "" if og >= OUTGROUP_MIN else " ⚠"
            print(
                f"  {arm+'/'+str(s):20s} {ec:12.1f} {mean(r,'population'):6.0f} "
                f"{og*100:7.1f}%{og_flag:2s} {mean(r,'lineage_effective'):9.2f} "
                f"{mean(r,'forage_per_capita'):11.5f}{flag}"
            )
    print(f"\n  ⚠ dis-grup firsat payi < {OUTGROUP_MIN*100:.0f}% olan kolda"
          " AKRABALIK ayrimciligi OKUNMAZ (gurultu).")

    print()
    print("=" * 92)
    print("ASIL OLCUT (3) — isbirligi SECIMSIZ kontrolden yukari ayristi mi?")
    print("=" * 92)
    print(f"  {'seed':>6s} {'secim%':>8s} {'secimsiz%':>10s} {'fark(puan)':>11s} {'Welch t':>9s} {'karar':>8s}")
    passed = 0
    usable = 0
    for s in seeds:
        a, b = rows_per_seed[s]["secim"], rows_per_seed[s]["secimsiz"]
        if a is None or b is None:
            print(f"  {s:6d}  (eksik kol)")
            continue
        usable += 1
        sa, sb = tail(a, "cooperation_rate"), tail(b, "cooperation_rate")
        t = welch_t(sa, sb)
        ok = t > T_MIN
        passed += ok
        print(
            f"  {s:6d} {sa.mean()*100:8.2f} {sb.mean()*100:10.2f} "
            f"{(sa.mean()-sb.mean())*100:+11.2f} {t:+9.2f} {'GECTI' if ok else 'hayir':>8s}"
        )
    need = math.ceil(usable * 2 / 3) if usable else 0
    print(f"\n  ozet: {passed}/{usable} seed (olcut: >= 2/3, yani >= {need})"
          f"  ->  {'PARTNER SECIMI ISBIRLIGINI KURDU' if usable and passed >= need else 'KURMADI'}")

    print()
    print("=" * 92)
    print("OLCUT (4) — bir secim POLITIKASI evrimlesti mi?")
    print("=" * 92)
    print("  secicilik = secilen partner profili - EN YAKIN komsunun profili.")
    print("  Politika yoksa 0. Rastgele-secim kontrolune karsi okunur.")
    print()
    print(f"  {'seed':>6s} {'kinSel secim':>13s} {'kinSel rast':>12s} {'t':>7s} "
          f"{'ledSel secim':>13s} {'ledSel rast':>12s} {'t':>7s}")
    pol = 0
    for s in seeds:
        a, b = rows_per_seed[s]["secim"], rows_per_seed[s]["rastgele"]
        if a is None or b is None:
            print(f"  {s:6d}  (eksik kol)")
            continue
        ka, kb = tail(a, "pick_kin_sel"), tail(b, "pick_kin_sel")
        la, lb = tail(a, "pick_ledger_sel"), tail(b, "pick_ledger_sel")
        tk, tl = welch_t(ka, kb), welch_t(la, lb)
        pol += abs(tk) > T_MIN or abs(tl) > T_MIN
        print(
            f"  {s:6d} {ka.mean():+13.4f} {kb.mean():+12.4f} {tk:+7.2f} "
            f"{la.mean():+13.4f} {lb.mean():+12.4f} {tl:+7.2f}"
        )
    print(f"\n  ozet: {pol}/{len(seeds)} seed'de secicilik rastgeleden ayristi")

    print()
    print("=" * 92)
    print("EVRIMIN YONU — gp_pick_* (secim kolunda, son ceyrek ortalamasi)")
    print("=" * 92)
    keys = ["gp_pick_kin", "gp_pick_ledger", "gp_pick_need", "gp_pick_energy",
            "gp_pick_dist"]
    print(f"  {'seed':>6s}" + "".join(f"{k.replace('gp_pick_',''):>12s}" for k in keys))
    for s in seeds:
        r = rows_per_seed[s]["secim"]
        if r is None:
            continue
        print(f"  {s:6d}" + "".join(f"{mean(r,k):+12.4f}" for k in keys))
    print("\n  Hepsi 0.0 basladi. 0'dan uzaklasma mutasyon+surukleme de olabilir;")
    print("  POLITIKA iddiasi icin olcut (4) gerekir (secicilik gercekten degisti mi).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 6 partner secimi raporu")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123])
    ap.add_argument("--prefix", default="f6", help="runs/<prefix>_<kol>_s<seed>")
    args = ap.parse_args(argv)
    return report(args.prefix, args.seeds)


if __name__ == "__main__":
    raise SystemExit(main())
