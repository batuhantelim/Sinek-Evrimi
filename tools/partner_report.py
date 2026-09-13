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
# Olcut 3'un IKINCI yarisi: "Faz 4.5/4.6/5'te taban %0.6-2.4 bandindaydi;
# 'kurdu' demek icin bu banttan CIKMASI gerekir." Kontrolden istatistiksel
# ayrisma tek basina yetmez — 0.44% -> 0.89% ayrisir ama hala tabandir.
BASELINE_HIGH = 0.024


def energy_created(run: str) -> float:
    """Korunum kontrolu ADIM bazli CSV'den okunur: `energy_created` bir donem
    sutunu DEGIL, adim sayacidir. generations.csv'de arayan bir ilk surum
    sessizce `nan` aliyordu — korunum ihlali boyle gozden kacar."""
    path = os.path.join(run, "metrics.csv") if not run.endswith(".csv") else run
    if not os.path.exists(path):
        return float("nan")
    total = 0.0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            v = row.get("energy_created")
            if v not in (None, ""):
                total += float(v)
    return total


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
            ec = energy_created(os.path.join("runs", f"{prefix}_{arm}_s{s}"))
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
    print("  Ucuncu blok SART: artis 'secme yetenegi'nden mi (havuz varligi) yoksa")
    print("  'akilli secim'den mi (evrimlesen politika) geliyor. Rastgele secim de")
    print("  ayni artisi veriyorsa politika degil MEKANIK is yapiyor.")
    print()
    print(f"  {'seed':>6s} {'secim%':>8s} {'secimsiz%':>10s} {'fark(puan)':>11s} {'Welch t':>9s} {'karar':>14s}"
          f" | {'rastgele%':>10s} {'t(secim-rast)':>14s}")
    passed = 0
    sep_n = 0
    mech = 0
    usable = 0
    for s in seeds:
        a, b = rows_per_seed[s]["secim"], rows_per_seed[s]["secimsiz"]
        if a is None or b is None:
            print(f"  {s:6d}  (eksik kol)")
            continue
        usable += 1
        sa, sb = tail(a, "cooperation_rate"), tail(b, "cooperation_rate")
        t = welch_t(sa, sb)
        sep = t > T_MIN                       # kontrolden ayristi mi
        band = sa.mean() > BASELINE_HIGH      # taban bandindan cikti mi
        ok = sep and band
        passed += ok
        sep_n += sep
        verdict = "GECTI" if ok else ("ayristi/taban" if sep else "hayir")
        c = rows_per_seed[s]["rastgele"]
        sc = tail(c, "cooperation_rate") if c is not None else np.zeros(0)
        tr = welch_t(sa, sc) if sc.size else float("nan")
        if sc.size and tr <= T_MIN:
            mech += 1
        print(
            f"  {s:6d} {sa.mean()*100:8.2f} {sb.mean()*100:10.2f} "
            f"{(sa.mean()-sb.mean())*100:+11.2f} {t:+9.2f} {verdict:>14s}"
            f" | {sc.mean()*100 if sc.size else float('nan'):10.2f} {tr:+14.2f}"
        )
    need = math.ceil(usable * 2 / 3) if usable else 0
    print(f"\n  kontrolden AYRISMA : {sep_n}/{usable} seed (t > {T_MIN:g}, yukari)")
    print(f"  TABAN BANDINDAN CIKMA: {passed}/{usable} seed "
          f"(son ceyrek paylasim orani > {BASELINE_HIGH*100:.1f}%)")
    print(f"  olcut: ikisi birlikte, >= 2/3 (yani >= {need})"
          f"  ->  {'PARTNER SECIMI ISBIRLIGINI KURDU' if usable and passed >= need else 'KURMADI'}")
    print(f"  RASTGELE SECIM de ayni isi yapiyor: {mech}/{usable} seed "
          "(secim, rastgeleden yukari AYRISMIYOR)")
    if mech >= need:
        print("  -> artisin kaynagi POLITIKA degil, HAVUZUN VARLIGI (mekanik).")
    if sep_n >= need and passed < need:
        print("  ⚠ Ayrisma var ama seviye taban bandinin ICINDE: 'kontrolden")
        print("    yukari ayristi' ile 'isbirligini kurdu' AYNI SEY DEGIL.")

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
        lin = mean(a, "lineage_effective")
        ka, kb = tail(a, "pick_kin_sel"), tail(b, "pick_kin_sel")
        la, lb = tail(a, "pick_ledger_sel"), tail(b, "pick_ledger_sel")
        tk, tl = welch_t(ka, kb), welch_t(la, lb)
        # OKUNMAZ kanal ozete girmez: etkin soy ~1 iken kinSel iki sifirin farki.
        pol += bool(abs(tl) > T_MIN or (lin >= 2.0 and abs(tk) > T_MIN))
        # Etkin soy ~1 ise HERKES akrabadir: kinSel yapisal olarak ~0 ve iki
        # sifirin Welch t'si buyuk cikabilir. O hucre OKUNMAZ.
        note = "" if lin >= 2.0 else f"   ⚠kinSel OKUNMAZ (etkin soy {lin:.2f})"
        print(
            f"  {s:6d} {ka.mean():+13.4f} {kb.mean():+12.4f} {tk:+7.2f} "
            f"{la.mean():+13.4f} {lb.mean():+12.4f} {tl:+7.2f}{note}"
        )
    print(f"\n  ozet: {pol}/{len(seeds)} seed'de OKUNABILIR secicilik rastgeleden ayristi")

    print()
    print("=" * 92)
    print("KIME — paylasim ve saldiri, defter isaretine kosullu (katmanli)")
    print("=" * 92)
    print("  ⚠ Secim SADECE paylasimi degil, SALDIRIYI da ayni partnere yoneltir")
    print("  (ikisi ayni hedefi paylasir ve birbirini disar). Yani `pick_*_sel`")
    print("  tek basina 'kime vermeyi sectim' demez; asagidaki iki sutun ayrimi")
    print("  eylem bazinda gosterir.")
    print()
    print(f"  {'kol/seed':20s} {'paylasim%':>10s} {'recip_adj':>10s} {'saldiri%':>9s} "
          f"{'retal_adj':>10s} {'defter+ firsat':>15s}")
    for s in seeds:
        for arm in ARMS:
            r = rows_per_seed[s][arm]
            if r is None:
                continue
            print(
                f"  {arm+'/'+str(s):20s} {mean(r,'cooperation_rate')*100:10.2f} "
                f"{mean(r,'recip_bias_adj'):+10.4f} {mean(r,'hostility_rate')*100:9.2f} "
                f"{mean(r,'retal_bias_adj'):+10.4f} {mean(r,'opp_ledger_pos'):15.0f}"
            )
    print("\n  recip_adj/retal_adj kendi ESLESMIS kontroluna karsi okunur, sifira")
    print("  karsi DEGIL (Faz 5 dersi: misilleme gorunusu tamamen konfoundluydu).")

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
