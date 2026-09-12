#!/usr/bin/env python3
"""Faz 3 adim 2'yi BIREBIR ayni rejimde birden cok seed'de tekrarlar.

Yeni mekanik yok: tek degisen seed. Her seed icin hem asil kosum hem
soyisim-karistirma kontrolu calisir — kontrolsuz sonuc okunmaz.

Amac: adim 2'nin bulgusu (in-grup fedakarlik ayrisiyor, dis-grup dusmanlik
akrabaliga kor) seed'e ozgu bir tesaduf mu, tekrarlanabilir mi?

    python tools/seed_sweep.py --seeds 42 123 --out sonuc.jsonl
    python tools/seed_sweep.py --summary sonuc.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

# experiments/faz3b_saldiri.yaml ile BIREBIR ayni rejim.
REGIME = [
    "agents.motors.max_speed=0.20",
    "agents.motors.max_turn=0.25",
    "agents.reproduction.spawn_radius=0.3",
    "rules.share.need_bonus=3.0",
    # Bu rejim, need_bonus'un ENERJI olarak uygulandigi surumde olculdu.
    # Varsayilan artik korunumlu (Faz 4.5); eski taramalar yeniden
    # uretilebilsin diye acikca pinleniyor.
    "rules.share.need_mode=energy",
    "rules.attack.enabled=true",
    # Faz 4 avcisi bu rejimin parcasi DEGIL: config.yaml varsayilani ilerledi
    # diye adim 2 taramasi sessizce baska bir deney olmasin.
    "rules.predator.enabled=false",
]
FIXED = ["viz.mode=none", "metrics.enabled=false"]
SEED_POP = "docs/faz2/population.npz"

CELLS = ["coop_in_group", "coop_out_group", "attack_in_group", "attack_out_group"]


def run(
    seed: int, steps: int, control: bool, seed_pop: str | None, extra: list[str] | None = None
) -> list[dict]:
    """Tek kosum. `extra` cevresel tarama icin ek override'lar (bkz. env_sweep)."""
    ov = FIXED + REGIME + list(extra or []) + [f"seed={seed}"]
    if control:
        ov.append("rules.kinship.control=shuffle_surnames")
    cfg = load_config(overrides=ov)
    genomes = None
    if seed_pop and os.path.exists(seed_pop):
        genomes, _meta = load_population(seed_pop, cfg)
    sim = Simulation(cfg, initial_genomes=genomes)
    sim.run(steps)
    return sim.generation_rows


def series(rows: list[dict], key: str, frac: float = 0.5) -> np.ndarray:
    """Son `frac` kadarlik dilim — baslangic gecici rejimini disarida birakir."""
    if not rows:
        return np.zeros(0)
    cut = int(len(rows) * (1.0 - frac))
    return np.array([float(r[key]) for r in rows[cut:]], dtype=np.float64)


def welch_t(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return 0.0
    se = math.sqrt(np.var(a, ddof=1) / a.size + np.var(b, ddof=1) / b.size)
    return float((a.mean() - b.mean()) / se) if se > 1e-12 else 0.0


def evaluate(seed: int, steps: int, seed_pop: str | None) -> dict:
    t0 = time.time()
    main = run(seed, steps, False, seed_pop)
    ctrl = run(seed, steps, True, seed_pop)

    share_t = welch_t(series(main, "kin_bias_adj"), series(ctrl, "kin_bias_adj"))
    attack_t = welch_t(series(main, "attack_kin_bias_adj"), series(ctrl, "attack_kin_bias_adj"))
    q = {k: float(series(main, k, 0.25).mean()) for k in CELLS}
    qc = {k: float(series(ctrl, k, 0.25).mean()) for k in CELLS}

    out = {
        "seed": seed,
        "steps": steps,
        "epochs": len(main),
        "seconds": round(time.time() - t0, 1),
        "share_adj_main": float(series(main, "kin_bias_adj").mean()),
        "share_adj_ctrl": float(series(ctrl, "kin_bias_adj").mean()),
        "share_t": share_t,
        "attack_adj_main": float(series(main, "attack_kin_bias_adj").mean()),
        "attack_adj_ctrl": float(series(ctrl, "attack_kin_bias_adj").mean()),
        "attack_t": attack_t,
        "assortment": float(series(main, "kin_assortment").mean()),
        "lineage_eff": float(series(main, "lineage_effective").mean()),
        "opp_kin": float(series(main, "opp_kin").mean()),
        "opp_nonkin": float(series(main, "opp_nonkin").mean()),
        **{f"q_{k}": v for k, v in q.items()},
        **{f"qc_{k}": v for k, v in qc.items()},
    }
    # BASARI olcutu adim 2'deki gibi: kontrolden ayrisma (Welch t > 2) VE yon
    out["share_separates"] = bool(share_t > 2.0 and out["share_adj_main"] > out["share_adj_ctrl"])
    out["attack_verdict"] = (
        "kor" if abs(attack_t) < 2.0 else ("akrabaya" if attack_t > 0 else "yabanciya")
    )
    return out


HEADER = (
    f"  {'seed':>6} {'paylas ic':>10} {'paylas dis':>11} {'saldir ic':>10} {'saldir dis':>11} "
    f"| {'kin_adj':>8} {'kontrol':>8} {'t':>6} {'ayristi':>8} "
    f"| {'atk_t':>6} {'saldiri':>9} | {'r':>5} {'soy':>5}"
)


def fmt(r: dict) -> str:
    return (
        f"  {r['seed']:>6} {r['q_coop_in_group'] * 100:9.2f}% {r['q_coop_out_group'] * 100:10.2f}% "
        f"{r['q_attack_in_group'] * 100:9.2f}% {r['q_attack_out_group'] * 100:10.2f}% "
        f"| {r['share_adj_main'] * 100:+8.2f} {r['share_adj_ctrl'] * 100:+8.2f} "
        f"{r['share_t']:+6.2f} {'EVET' if r['share_separates'] else 'hayir':>8} "
        f"| {r['attack_t']:+6.2f} {r['attack_verdict']:>9} "
        f"| {r['assortment']:5.2f} {r['lineage_eff']:5.1f}"
    )


def summarize(path: str) -> None:
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    rows.sort(key=lambda r: r["seed"])
    if not rows:
        raise SystemExit(f"bos: {path}")

    print("=" * 118)
    print(f"TEKRARLANABILIRLIK TABLOSU — {len(rows)} seed, her biri kontroluyle birlikte")
    print("  (dort hucre: son ceyrek, firsata kosullu; kin_adj: son yari ortalamasi, yuzde puan)")
    print("=" * 118)
    print(HEADER)
    for r in rows:
        print(fmt(r))

    print()
    print("=" * 118)
    print("OZET")
    print("=" * 118)
    sep = sum(1 for r in rows if r["share_separates"])
    blind = sum(1 for r in rows if r["attack_verdict"] == "kor")
    adj = np.array([r["share_adj_main"] for r in rows]) * 100
    adjc = np.array([r["share_adj_ctrl"] for r in rows]) * 100
    ts = np.array([r["share_t"] for r in rows])
    ratio = np.array(
        [r["q_coop_in_group"] / r["q_coop_out_group"] if r["q_coop_out_group"] > 1e-9 else 0.0
         for r in rows]
    )
    print(f"  in-grup fedakarlik kontrolden ayristi : {sep}/{len(rows)} seed")
    print(f"     kin_bias_adj asil   : {adj.mean():+.2f} +- {adj.std(ddof=1):.2f} puan")
    print(f"     kin_bias_adj kontrol: {adjc.mean():+.2f} +- {adjc.std(ddof=1):.2f} puan")
    print(f"     Welch t             : {ts.mean():+.2f} +- {ts.std(ddof=1):.2f}  (min {ts.min():+.2f})")
    print(f"     in/dis orani        : {ratio.mean():.2f}x +- {ratio.std(ddof=1):.2f}")
    print(f"  dis-grup saldiri akrabaliga KOR kaldi : {blind}/{len(rows)} seed")
    verdicts = {}
    for r in rows:
        verdicts[r["attack_verdict"]] = verdicts.get(r["attack_verdict"], 0) + 1
    print(f"     saldiri kararlari   : {verdicts}")
    ok = np.array([r["opp_kin"] for r in rows])
    on = np.array([r["opp_nonkin"] for r in rows])
    print(
        f"  ornek/baglam: opp_kin {ok.mean():.0f}, opp_dis {on.mean():.0f} "
        f"(dis-grup payi {(on / (ok + on)).mean() * 100:.1f}%), "
        f"r {np.mean([r['assortment'] for r in rows]):.2f}, "
        f"etkin soy {np.mean([r['lineage_eff'] for r in rows]):.1f}"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="cok-seed tekrarlanabilirlik taramasi")
    ap.add_argument("--seeds", nargs="*", type=int, default=[])
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-seed-pop", action="store_true", help="Faz 2 tohumunu kullanma")
    ap.add_argument("--summary", default=None, help="JSONL dosyasindan ozet tablo bas")
    args = ap.parse_args(argv)

    if args.summary:
        summarize(args.summary)
        return 0
    if not args.seeds:
        raise SystemExit("--seeds ya da --summary verin")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pop = None if args.no_seed_pop else os.path.join(root, SEED_POP)
    out = open(args.out, "a", encoding="utf-8") if args.out else None
    print(HEADER)
    for seed in args.seeds:
        r = evaluate(seed, args.steps, pop)
        print(fmt(r), flush=True)
        if out:
            out.write(json.dumps(r) + "\n")
            out.flush()
    if out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
