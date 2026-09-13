#!/usr/bin/env python3
"""FAZ 4.5 Bolum 2 — enerji -> ureme -> secilim zinciri saglikli mi?

Eski kurulumda populasyon `agents.max_count` tavanindaydi: ureme bir SLOT
KUYRUGUNA donuyor, adim basina ~456 ureme hakki yaniyordu. O durumda cok
enerji toplamak ureme basarisina zayif donusur — yani SECILIM KIRIKTIR ve
enerji biriminde olculen her fitness argumani (b/c, Hamilton) anlamini
kaybeder.

Bu sonda TAMAMLANMIS yasamlari toplar (olum anindaki kayit) ve sorar:

  1. Cok yemek toplayan gercekten cok mu uruyor?  (food_eaten -> children)
  2. Bu iliski YASA gore duzeltildiginde de duruyor mu? Yaslı ajan hem cok
     yer hem cok urer; ham korelasyon bunu gizler.
  3. Paylasmanin gerceklesen fitness bedeli var mi? (given -> children)
     Almanin faydasi var mi? (received -> children)

Iki rejim yan yana kosulur: eski (tavan bagliyor + enerji yaratan paylasim)
ve yeni (cevresel sinirlama + korunumlu paylasim).

    python tools/selection_probe.py --steps 8000
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from sinek.config import load_config  # noqa: E402
from sinek.persistence import load_population  # noqa: E402
from sinek.simulation import Simulation  # noqa: E402

BASE = ["viz.mode=none", "metrics.enabled=false", "metrics.record_lifetimes=true"]
REGIME = [
    "agents.motors.max_speed=0.20",
    "agents.motors.max_turn=0.25",
    "agents.reproduction.spawn_radius=0.3",
    "rules.share.need_bonus=3.0",
    "rules.attack.enabled=true",
    "rules.predator.enabled=false",
]
#: Iki rejim arasindaki TEK fark bu iki anahtar.
ARMS = {
    "eski (tavan + enerji pompasi)": ["agents.max_count=700", "rules.share.need_mode=energy"],
    "yeni (cevresel + korunumlu)": ["agents.max_count=5000", "rules.share.need_mode=fitness"],
}
SEED_POP = "docs/faz4tani/population_taban.npz"


def partial_corr(x: np.ndarray, y: np.ndarray, *controls: np.ndarray) -> float:
    """x ile y arasindaki korelasyon, verilen kontroller cikarildiktan sonra.

    YAS her zaman kontrol edilmeli: yasli ajan hem cok yer hem cok urer.
    Paylasim sorularinda ayrica YEMEK de kontrol edilmeli: cok toplayan hem
    cok paylasir hem cok urer; kontrolsuz okunursa "paylasmak odullendiriyor"
    gibi gorunur ki bu yanlistir.
    """
    if x.size < 10 or not controls:
        return float("nan")
    z = np.column_stack([np.asarray(c, dtype=np.float64) for c in controls])
    z = np.column_stack([z, np.ones(z.shape[0])])

    def resid(v):
        beta, *_ = np.linalg.lstsq(z, v, rcond=None)
        return v - z @ beta

    rx, ry = resid(x), resid(y)
    if rx.std() < 1e-12 or ry.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def run(extra: list[str], seed: int, steps: int, dump: str | None = None) -> dict:
    cfg = load_config(overrides=BASE + REGIME + extra + [f"seed={seed}"])
    pop = os.path.join(ROOT, SEED_POP)
    genomes, _ = load_population(pop, cfg) if os.path.exists(pop) else (None, None)
    sim = Simulation(cfg, initial_genomes=genomes)
    sim.run(steps)
    rec = np.array(sim.life_records, dtype=np.float64)
    if rec.size == 0:
        raise SystemExit("hic olum kaydi yok")
    if dump:
        np.savez_compressed(dump, records=rec)
    food, kids, age, given, recv = rec[:, 0], rec[:, 1], rec[:, 2], rec[:, 3], rec[:, 4]
    # Kisa yasamis ajanlar zinciri degil dogum kosullarini olcer; en az
    # ureme yasina ulasmis olanlara bakiyoruz.
    min_age = float(cfg.agents.reproduction.min_age)
    m = age >= min_age
    return {
        "n": int(m.sum()),
        "total_deaths": int(rec.shape[0]),
        "pop_end": len(sim.agents),
        "at_cap": len(sim.agents) >= int(cfg.agents.max_count),
        "repro_blocked": sim.stats_total.get("repro_blocked", 0) / max(1, steps),
        "energy_created": sim.stats_total.get("energy_created", 0.0) / max(1, steps),
        "mean_kids": float(kids[m].mean()),
        "childless": float((kids[m] == 0).mean()),
        "r_food_kids": float(np.corrcoef(food[m], kids[m])[0, 1]),
        "pr_food_kids": partial_corr(food[m], kids[m], age[m]),
        "slope": float(np.polyfit(food[m], kids[m], 1)[0]),
        # Paylasim sorularinda YAS ve YEMEK birlikte kontrol edilir.
        "r_given_kids": partial_corr(given[m], kids[m], age[m], food[m]),
        "r_recv_kids": partial_corr(recv[m], kids[m], age[m], food[m]),
        "r_given_naive": partial_corr(given[m], kids[m], age[m]),
        "share_frac": float((given[m] > 0).mean()),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="enerji -> ureme -> secilim zinciri sondasi")
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dump", default=None, help="yasam kayitlarini bu klasore npz olarak yaz")
    args = ap.parse_args(argv)

    out = {}
    for i, (name, extra) in enumerate(ARMS.items()):
        dump = os.path.join(args.dump, f"yasamlar_{i}.npz") if args.dump else None
        if dump:
            os.makedirs(args.dump, exist_ok=True)
        out[name] = run(extra, args.seed, args.steps, dump)

    print("=" * 96)
    print(f"SECILIM ZINCIRI SONDASI — {args.steps} adim, seed {args.seed}, tamamlanmis yasamlar")
    print("=" * 96)
    rows = [
        ("tamamlanmis yasam (n)", "n", "{:.0f}"),
        ("son populasyon", "pop_end", "{:.0f}"),
        ("adim basina yanan ureme hakki", "repro_blocked", "{:.1f}"),
        ("adim basina YARATILAN enerji", "energy_created", "{:.1f}"),
        ("ortalama yavru", "mean_kids", "{:.2f}"),
        ("hic uremeyenlerin payi", "childless", "{:.1%}"),
        ("yemek -> yavru  (ham r)", "r_food_kids", "{:+.3f}"),
        ("yemek -> yavru  (YAS kontrollu)", "pr_food_kids", "{:+.3f}"),
        ("egim (yavru / yemek birimi)", "slope", "{:.4f}"),
        ("paylasan ajan payi", "share_frac", "{:.1%}"),
        ("VERMEK -> yavru (yalniz yas kontrollu)", "r_given_naive", "{:+.3f}"),
        ("VERMEK -> yavru (yas+YEMEK kontrollu)", "r_given_kids", "{:+.3f}"),
        ("ALMAK  -> yavru (yas+YEMEK kontrollu)", "r_recv_kids", "{:+.3f}"),
    ]
    names = list(out)
    print(f"  {'olcum':34s}" + "".join(f"{n[:28]:>30}" for n in names))
    for label, key, fmt in rows:
        line = f"  {label:34s}"
        for n in names:
            line += f"{fmt.format(out[n][key]):>30}"
        print(line)
    print()
    a, b = out[names[0]], out[names[1]]
    print(f"  YORUM: yas kontrollu 'yemek -> yavru' bagi {a['pr_food_kids']:+.3f} -> "
          f"{b['pr_food_kids']:+.3f}")
    print("         Zincir saglikliysa bu bag POZITIF ve belirgin olmali: cok toplayan")
    print("         cok urer. Tavan bagliyorken ureme bir slot kuyrugudur ve bag zayiflar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
