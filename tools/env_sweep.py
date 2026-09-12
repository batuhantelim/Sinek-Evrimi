#!/usr/bin/env python3
"""Cevresel tarama: dis-grup bollugu (H1) ve kaynak kitligi (H2).

Sagam­lik taramasinda saldiri 4/5 seed'de akrabaliga kordu; tek istisna seed
2024 hem en yuksek dis-grup firsat payina hem en dusuk kumelenmeye sahipti.
Bu iki sey O SEED'DE IC ICEYDI. Burada onlari ayirmaya calisiyoruz.

YENI MEKANIK YOK — yalnizca dunya parametreleri degisir. Rejim adim 2 /
saglamlik taramasiyla ayni (r_azalan + need_bonus + neighbor_need).

EKSEN A iki ALT-KALDIRACLA surulur, cunku tek kaldirac iki degiskeni birden
oynatir ve hangisinin surdugu ayirt edilemez:

  A1 "bolunme"  (rules.kinship.split_rate) : soy sayisini artirir.
                 Dis-grup payi yukselir; MEKANSAL yapi bozulmaz.
  A2 "karisma"  (max_speed + spawn_radius) : akrabalar dagilir.
                 Hem dis-grup payi yukselir hem assortment DUSER.

Ikisi ayri ayri surulup her kosulda `kin_assortment` ve dis-grup payi
OLCULUR. Saldiri ayrimciligi yalnizca A2 ile hareket ediyorsa surucu
"yabanci bollugu" degil "akrabaligin zayiflamasi"dir.

EKSEN B kaynak bollugu/kitligidir (world.food.*).

    python tools/env_sweep.py --conditions A1_dusuk A1_yuksek --seeds 42 7
    python tools/env_sweep.py --summary sonuc.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from seed_sweep import CELLS, FIXED, REGIME, SEED_POP, run, series, welch_t  # noqa: E402

# --- EKSEN A: dis-grup bollugu -------------------------------------------
# A1: soy bolunme hizi. Populasyonu, hizi, mekansal yapiyi DEGISTIRMEZ.
A1 = {
    "A1_cok_dusuk": ["rules.kinship.split_rate=0.002"],
    "A1_taban": [],                                    # split_rate 0.010 (varsayilan)
    "A1_yuksek": ["rules.kinship.split_rate=0.040"],
    "A1_cok_yuksek": ["rules.kinship.split_rate=0.120"],
}
# A2: karisma. Akrabalari mekansal olarak dagitir -> assortment DUSER.
A2 = {
    "A2_orta_karisma": ["agents.motors.max_speed=0.45", "agents.reproduction.spawn_radius=0.8"],
    "A2_tam_karisma": ["agents.motors.max_speed=0.85", "agents.reproduction.spawn_radius=1.5"],
}
# --- EKSEN B: kaynak bollugu/kitligi (sonraki parti) ----------------------
B = {
    "B_bol": ["world.food.regrowth_rate=0.020", "world.food.initial_fill=0.80"],
    "B_kit": ["world.food.regrowth_rate=0.004", "world.food.initial_fill=0.35"],
    "B_cok_kit": ["world.food.regrowth_rate=0.002", "world.food.initial_fill=0.20",
                  "world.food.patches=14"],
}
# --- kose kombinasyonlari ------------------------------------------------
CORNERS = {
    "kit_cok_yabanci": B["B_kit"] + A2["A2_tam_karisma"],
    "kit_az_yabanci": B["B_kit"] + A1["A1_cok_dusuk"],
    "bol_cok_yabanci": B["B_bol"] + A2["A2_tam_karisma"],
}
CONDITIONS: dict[str, list[str]] = {**A1, **A2, **B, **CORNERS}


def evaluate(name: str, seed: int, steps: int, seed_pop: str | None) -> dict:
    extra = CONDITIONS[name]
    t0 = time.time()
    main = run(seed, steps, False, seed_pop, extra=extra)
    ctrl = run(seed, steps, True, seed_pop, extra=extra)
    if not main:
        return {"condition": name, "seed": seed, "extinct": True}

    ok = float(series(main, "opp_kin").mean())
    on = float(series(main, "opp_nonkin").mean())
    share_t = welch_t(series(main, "kin_bias_adj"), series(ctrl, "kin_bias_adj"))
    attack_t = welch_t(series(main, "attack_kin_bias_adj"), series(ctrl, "attack_kin_bias_adj"))
    out = {
        "condition": name,
        "seed": seed,
        "steps": steps,
        "seconds": round(time.time() - t0, 1),
        "extinct": False,
        # --- eksen degiskenleri: kaldiracin ne yaptigini OLCUYORUZ ---
        "outgroup_share": on / (ok + on) if (ok + on) > 0 else 0.0,
        "assortment": float(series(main, "kin_assortment").mean()),
        "food_fill": float(series(main, "food_fill").mean()),
        "lineage_eff": float(series(main, "lineage_effective").mean()),
        "population": float(series(main, "population").mean()),
        # --- sonuclar ---
        "share_t": share_t,
        "attack_t": attack_t,
        "share_adj_main": float(series(main, "kin_bias_adj").mean()),
        "attack_adj_main": float(series(main, "attack_kin_bias_adj").mean()),
        "hostility": float(series(main, "hostility_rate").mean()),
        "cooperation": float(series(main, "cooperation_rate").mean()),
        **{f"q_{k}": float(series(main, k, 0.25).mean()) for k in CELLS},
    }
    out["share_separates"] = bool(share_t > 2.0 and out["share_adj_main"] > 0)
    out["attack_verdict"] = (
        "kor" if abs(attack_t) < 2.0 else ("akrabaya" if attack_t > 0 else "yabanciya")
    )
    return out


HEADER = (
    f"  {'kosul':17s} {'seed':>5} {'dis%':>6} {'assort':>7} {'yemek%':>7} {'soy':>5} {'N':>5} "
    f"| {'saldiri%':>9} {'atk_t':>7} {'karar':>10} | {'paylas%':>8} {'share_t':>8}"
)


def fmt(r: dict) -> str:
    if r.get("extinct"):
        return f"  {r['condition']:17s} {r['seed']:>5}  (koloni tukendi)"
    return (
        f"  {r['condition']:17s} {r['seed']:>5} {r['outgroup_share'] * 100:5.1f}% "
        f"{r['assortment']:7.3f} {r['food_fill'] * 100:6.1f}% {r['lineage_eff']:5.1f} "
        f"{r['population']:5.0f} | {r['hostility'] * 100:8.2f}% {r['attack_t']:+7.2f} "
        f"{r['attack_verdict']:>10} | {r['cooperation'] * 100:7.2f}% {r['share_t']:+8.2f}"
    )


def summarize(path: str) -> None:
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    rows = [r for r in rows if not r.get("extinct")]
    if not rows:
        raise SystemExit(f"kullanilabilir satir yok: {path}")
    rows.sort(key=lambda r: (r["condition"], r["seed"]))

    print("=" * 112)
    print("KOSUL BASINA (her satir bir seed; her koşum kendi karistirma kontroluyle okundu)")
    print("=" * 112)
    print(HEADER)
    last = None
    for r in rows:
        if last and r["condition"] != last:
            print()
        print(fmt(r))
        last = r["condition"]

    # --- kosul ortalamalari ---
    print()
    print("=" * 112)
    print("KOSUL ORTALAMALARI (seedler arasi)")
    print("=" * 112)
    print(
        f"  {'kosul':17s} {'n':>2} {'dis%':>6} {'assort':>7} {'yemek%':>7} "
        f"| {'saldiri%':>9} {'atk_t ort':>10} {'kararlar':>28}"
    )
    names = sorted({r["condition"] for r in rows}, key=lambda n: list(CONDITIONS).index(n))
    for name in names:
        g = [r for r in rows if r["condition"] == name]
        v = {}
        for r in g:
            v[r["attack_verdict"]] = v.get(r["attack_verdict"], 0) + 1
        print(
            f"  {name:17s} {len(g):>2} {np.mean([r['outgroup_share'] for r in g]) * 100:5.1f}% "
            f"{np.mean([r['assortment'] for r in g]):7.3f} "
            f"{np.mean([r['food_fill'] for r in g]) * 100:6.1f}% "
            f"| {np.mean([r['hostility'] for r in g]) * 100:8.2f}% "
            f"{np.mean([r['attack_t'] for r in g]):+10.2f} {str(v):>28}"
        )

    # --- iki eksen ayrilabildi mi? ---
    print()
    print("=" * 112)
    print("AYRISTIRMA — saldiri ayrimciligini hangisi suruyor?")
    print("=" * 112)
    x1 = np.array([r["outgroup_share"] for r in rows])
    x2 = np.array([r["assortment"] for r in rows])
    x3 = np.array([r["food_fill"] for r in rows])
    y = np.array([r["attack_t"] for r in rows])
    print(f"  n = {len(rows)} kosum")
    print(f"  korelasyon  dis-grup payi ~ saldiri_t : {np.corrcoef(x1, y)[0, 1]:+.3f}")
    print(f"  korelasyon  assortment    ~ saldiri_t : {np.corrcoef(x2, y)[0, 1]:+.3f}")
    print(f"  korelasyon  yemek doluluk ~ saldiri_t : {np.corrcoef(x3, y)[0, 1]:+.3f}")
    coll = np.corrcoef(x1, x2)[0, 1]
    print(f"  DOGRUSAL BAGIMLILIK dis-grup ~ assortment : {coll:+.3f}", end="  ")
    print("(|r|>0.9 ise ikisi ayrilamaz — kaldiraclar yetmemis)")
    if abs(coll) < 0.95 and len(rows) >= 5:
        A = np.column_stack([np.ones_like(x1), x1, x2])
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        print(
            f"  cok degiskenli regresyon: saldiri_t = {beta[0]:+.2f} "
            f"{beta[1]:+.2f}*dis_pay {beta[2]:+.2f}*assortment"
        )
        print("  (iki degisken birlikte konuldugunda hangisinin katsayisi hayatta kaliyor)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="cevresel tarama: dis-grup bollugu x kitlik")
    ap.add_argument("--conditions", nargs="*", default=[])
    ap.add_argument("--seeds", nargs="*", type=int, default=[42])
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--summary", default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.summary:
        summarize(args.summary)
        return 0
    if args.list or not args.conditions:
        for name, ov in CONDITIONS.items():
            print(f"  {name:17s} {ov}")
        return 0

    pop = os.path.join(ROOT, SEED_POP)
    out = open(args.out, "a", encoding="utf-8") if args.out else None
    print(HEADER)
    for name in args.conditions:
        if name not in CONDITIONS:
            raise SystemExit(f"bilinmeyen kosul {name!r}; secenekler: {', '.join(CONDITIONS)}")
        for seed in args.seeds:
            r = evaluate(name, seed, args.steps, pop)
            print(fmt(r), flush=True)
            if out:
                out.write(json.dumps(r) + "\n")
                out.flush()
    if out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
