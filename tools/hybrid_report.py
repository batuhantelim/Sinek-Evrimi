#!/usr/bin/env python3
"""Faz 9 melez raporu: melez DISLANIYOR mu, KOPRU mu, FARK YOK mu?

Olcut (docs/faz9/olcut.md, kosumlardan ONCE ilan edildi):

  ONKOSUL  melez payi >= %5 VE `opp_hybrid` >= 1000 (kucuk ornek tuzagi)
  DISLAMA  melez-akrabaya paylasim SAF akrabadan dusuk VE saldiri yuksek
           (ikisi de |Welch t| > 2, kendi KARISTIRMA kontroluna karsi)
  KOPRU    paylasim saf akrabadan dusuk DEGIL (t > -2) VE yabancidan yuksek
  FARK YOK ikisi de saglanmiyor

Her olcu enerji KATMANLI (`stratified_kin_bias`) ve kendi eslesmis kontroluna
karsi okunur — ham fark tek basina kanit degildir (Faz 3'ten beri ayni kural).

    python tools/hybrid_report.py --seeds 42 7 123
    python tools/hybrid_report.py --prefix f9 --seeds 42 7 123
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ARMS = ("melez", "melezyok", "karistirma")

HYBRID_SHARE_MIN = 0.05   # onkosul 1
OPP_HYBRID_MIN = 1000     # onkosul 2
T_MIN = 2.0               # ayrisma esigi


def rows(run: str, name: str = "generations.csv") -> list[dict]:
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


def welch_t(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return 0.0
    se = math.sqrt(np.var(a, ddof=1) / a.size + np.var(b, ddof=1) / b.size)
    return float((a.mean() - b.mean()) / se) if se > 1e-12 else 0.0


def energy_created(run: str) -> float:
    total = 0.0
    for r in rows(run, "metrics.csv"):
        v = r.get("energy_created")
        if v not in (None, ""):
            total += float(v)
    return total


def collect(prefix: str, seed: int) -> dict:
    return {arm: rows(os.path.join("runs", f"{prefix}_{arm}_s{seed}")) for arm in ARMS}


def report(prefix: str, seeds: list[int]) -> int:
    data = {s: collect(prefix, s) for s in seeds}

    print("=" * 100)
    print("ONKOSUL — melez gercekten olusuyor mu, ornek yeterli mi")
    print("=" * 100)
    print(f"  {'seed':>5} {'melez payi':>11s} {'opp_hybrid':>11s} {'melez dogum':>12s} "
          f"{'E_yaratilan':>12s} {'durum':>9s}")
    pre_ok = 0
    usable = 0
    for s in seeds:
        r = data[s]["melez"]
        if not r:
            print(f"  {s:5d}  (kosum yok)")
            continue
        usable += 1
        hs, oh = mean(r, "hybrid_share"), mean(r, "opp_hybrid")
        ec = energy_created(os.path.join("runs", f"{prefix}_melez_s{s}"))
        ok = hs >= HYBRID_SHARE_MIN and oh >= OPP_HYBRID_MIN
        pre_ok += ok
        flag = "" if abs(ec) < 1e-6 else "  ⚠GECERSIZ"
        print(f"  {s:5d} {hs*100:10.1f}% {oh:11.0f} {mean(r,'hybrid_births'):12.1f} "
              f"{ec:12.1f} {'GECTI' if ok else 'GECMEDI':>9s}{flag}")
    print(f"\n  esik: melez payi >= {HYBRID_SHARE_MIN*100:.0f}%, "
          f"opp_hybrid >= {OPP_HYBRID_MIN}")
    print(f"  ozet: {pre_ok}/{usable} seed onkosulu gecti")
    if pre_ok < usable:
        print("  ⚠ Onkosulu gecmeyen seed'de asagidaki siniflandirma OKUNMAZ.")

    print()
    print("=" * 100)
    print("ZEMIN BOZULDU MU — melez-yok koluna karsi (olcut 2/3)")
    print("=" * 100)
    print(f"  {'seed':>5} {'etkinSoy':>19s} {'disPay':>15s} {'genetic_r':>17s} "
          f"{'N':>13s} {'topla/kisi':>15s}")
    for s in seeds:
        m, y = data[s]["melez"], data[s]["melezyok"]
        if not m or not y:
            continue
        def arrow(key, fmt=".2f"):
            return f"{mean(y, key):{fmt}}->{mean(m, key):{fmt}}"

        okm, odm = mean(m, "opp_kin"), mean(m, "opp_nonkin")
        oky, ody = mean(y, "opp_kin"), mean(y, "opp_nonkin")
        dm = odm / (okm + odm) if (okm + odm) else float("nan")
        dy = ody / (oky + ody) if (oky + ody) else float("nan")
        gr_y, gr_m = mean(y, "genetic_r"), mean(m, "genetic_r")
        ratio = gr_m / gr_y if gr_y else float("nan")
        print(
            f"  {s:5d} {arrow('lineage_effective'):>19s}"
            f" {f'{dy * 100:.1f}%->{dm * 100:.1f}%':>15s}"
            f" {f'{gr_y:.2f}->{gr_m:.2f} ({ratio:.2f}x)':>17s}"
            f" {arrow('population', '.0f'):>13s}"
            f" {arrow('forage_per_capita', '.4f'):>15s}"
        )

    print("\n  ⚠ Melez etiket sayiminda KENDI grubudur: `lineage_effective`'i tanim")
    print("  geregi yukseltebilir. Bu yuzden melez-yok koluna karsi okunur.")
    print(f"  Olcut 3: `genetic_r` orani >= 0.50 kalmali (akrabalik yapisi yasamali).")

    print()
    print("=" * 100)
    print("UC HUCRE — son ceyrek, firsata kosullu (ham oranlar, BILGI icin)")
    print("=" * 100)
    print(f"  {'seed/kol':20s} {'PAYLAS saf':>11s} {'PAYLAS melez':>13s} {'PAYLAS yab':>11s}"
          f" | {'SALDIR saf':>11s} {'SALDIR melez':>13s} {'SALDIR yab':>11s}")
    for s in seeds:
        for arm in ("melez", "karistirma"):
            r = data[s][arm]
            if not r:
                continue
            print(f"  {arm+'/'+str(s):20s} {mean(r,'coop_pure_kin')*100:10.2f}% "
                  f"{mean(r,'coop_hybrid_kin')*100:12.2f}% {mean(r,'coop_out')*100:10.2f}% | "
                  f"{mean(r,'atk_pure_kin')*100:10.2f}% {mean(r,'atk_hybrid_kin')*100:12.2f}% "
                  f"{mean(r,'atk_out')*100:10.2f}%")

    print()
    print("=" * 100)
    print("ASIL OLCUT — melez DISLANIYOR mu, KOPRU mu? (katmanli, kontrole karsi)")
    print("=" * 100)
    print(f"  {'seed':>5} {'paylas(melez-saf)':>19s} {'t':>7s} {'saldir(melez-saf)':>19s} "
          f"{'t':>7s} {'paylas(melez-yab)':>19s} {'t':>7s} {'karar':>10s}")
    verdicts = []
    for s in seeds:
        m, k = data[s]["melez"], data[s]["karistirma"]
        if not m or not k:
            print(f"  {s:5d}  (eksik kol)")
            continue
        sh_m, sh_k = tail(m, "hyb_share_adj"), tail(k, "hyb_share_adj")
        at_m, at_k = tail(m, "hyb_atk_adj"), tail(k, "hyb_atk_adj")
        ou_m, ou_k = tail(m, "hyb_share_vs_out_adj"), tail(k, "hyb_share_vs_out_adj")
        t_sh, t_at, t_ou = welch_t(sh_m, sh_k), welch_t(at_m, at_k), welch_t(ou_m, ou_k)
        if t_sh < -T_MIN and t_at > T_MIN:
            v = "DISLAMA"
        elif t_sh > -T_MIN and t_ou > T_MIN:
            v = "KOPRU"
        else:
            v = "FARK YOK"
        verdicts.append(v)
        print(f"  {s:5d} {sh_m.mean():+19.4f} {t_sh:+7.2f} {at_m.mean():+19.4f} {t_at:+7.2f} "
              f"{ou_m.mean():+19.4f} {t_ou:+7.2f} {v:>10s}")
    if verdicts:
        need = math.ceil(len(verdicts) * 2 / 3)
        for v in ("DISLAMA", "KOPRU"):
            n = verdicts.count(v)
            print(f"\n  {v}: {n}/{len(verdicts)} seed (olcut >= 2/3, yani >= {need})"
                  f"  ->  {'GECTI' if n >= need else 'gecmedi'}")
        print(f"  FARK YOK: {verdicts.count('FARK YOK')}/{len(verdicts)}")
    print("\n  Her uc olcu de enerji KATMANLI ve kendi KARISTIRMA kontroluna karsi")
    print("  okunur. Sifira karsi okunsaydi uzamsal kumelenme konfoundu")
    print("  yanlis pozitif uretirdi (Faz 3: kor beyinle bile +3.80 puan).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 9 melez raporu")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123])
    ap.add_argument("--prefix", default="f9", help="runs/<prefix>_<kol>_s<seed>")
    args = ap.parse_args(argv)
    return report(args.prefix, args.seeds)


if __name__ == "__main__":
    raise SystemExit(main())
