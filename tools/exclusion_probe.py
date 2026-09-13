#!/usr/bin/env python3
"""DISLAMA sondasi: adaylarin kaci hic secilmiyor, ve secilmeyenler kim?

Faz 6'nin ilan edilmis rapor kalemlerinden biri. Simulasyonu DEGISTIRMEZ:
`sim._note_pick` sarilir, karar anindaki havuz ve secilen kaydedilir.

Iki olcu ayri tutulur:

  YAPISAL dislama  = 1 - karar / aday.  Her kararda bir kisi secildigi icin
                     havuz 3 ise yapisal olarak %67'si secilmez. BILGI DEGIL.
  BIREYSEL dislama = bir ajanin KARSILASTIGI farkli partnerlerin kaci ona
                     hic secilmedi. Politika yoksa bu da yuksek cikar (mekan
                     dayatir), bu yuzden secilmeyenlerin PROFILI ile birlikte
                     okunur: secilmeyenler daha mi yabanci, daha mi fakir,
                     defterleri daha mi negatif?

    python tools/exclusion_probe.py --steps 3000
    python tools/exclusion_probe.py --steps 3000 --load docs/faz5/population_hafiza.npz
    python tools/exclusion_probe.py --steps 3000 --control random   # referans
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config
from sinek.persistence import load_population
from sinek.simulation import Simulation

#: Faz 6 rejimi (experiments/faz6_secim.yaml ile ayni olmali).
REGIME = [
    "agents.max_count=5000",
    "agents.motors.max_speed=0.20",
    "agents.motors.max_turn=0.25",
    "agents.reproduction.spawn_radius=0.3",
    "rules.kinship.radius=5.0",
    "rules.partner.enabled=true",
    "rules.partner.candidates=4",
    "rules.memory.enabled=true",
    "rules.predator.enabled=false",
    "rules.share.need_bonus=3.0",
    "rules.share.need_mode=fitness",
    "rules.attack.enabled=true",
]


class Tally:
    """Ajan basina: karsilasilan farkli partnerler, secilenler, ve profiller."""

    def __init__(self) -> None:
        self.seen: dict[int, set[int]] = {}
        self.chosen: dict[int, set[int]] = {}
        self.pool_n = 0
        self.events = 0
        # secilen / secilmeyen aday profilleri (akraba, defter+, enerji payi)
        self.prof = {
            "secilen": [0, 0, 0.0, 0],      # kin, defter+, enerji toplami, sayi
            "secilmeyen": [0, 0, 0.0, 0],
        }

    def note(self, a, pool, idx: int, emax: float) -> None:
        self.events += 1
        self.pool_n += len(pool)
        seen = self.seen.setdefault(a.id, set())
        chosen = self.chosen.setdefault(a.id, set())
        for i, (o, _d2) in enumerate(pool):
            seen.add(o.id)
            bucket = self.prof["secilen" if i == idx else "secilmeyen"]
            bucket[0] += o.genome.surname == a.genome.surname
            bucket[1] += a.ledger.get(o.mem_id, 0.0) > 0.0
            bucket[2] += o.energy / emax
            bucket[3] += 1
        chosen.add(pool[idx][0].id)

    def summary(self) -> dict:
        rates = [
            1.0 - len(self.chosen.get(aid, ())) / len(s)
            for aid, s in self.seen.items() if s
        ]
        out = {
            "events": self.events,
            "pool": self.pool_n / max(1, self.events),
            "structural": 1.0 - self.events / max(1, self.pool_n),
            "individual": float(np.mean(rates)) if rates else float("nan"),
            "agents": len(rates),
        }
        for label, (kin, led, en, n) in self.prof.items():
            n = max(1, n)
            out[label] = {"n": n, "kin": kin / n, "ledger_pos": led / n, "energy": en / n}
        return out


def probe(steps: int, seed: int, load: str | None, control: str,
          extra: list[str]) -> dict:
    ov = list(REGIME) + ["viz.mode=none", f"seed={seed}"] + list(extra)
    if control != "none":
        ov.append(f"rules.partner.control={control}")
    cfg = load_config(overrides=ov)
    genomes = None
    if load:
        genomes, meta = load_population(load, cfg)
        if meta.get("migrated"):
            print(f"  (tasima: {meta['migrated']})")
    sim = Simulation(cfg, initial_genomes=genomes)
    tally = Tally()
    emax = float(cfg.agents.energy.max)
    original = sim._note_pick

    def wrapped(a, pool, idx):
        tally.note(a, pool, idx, emax)
        original(a, pool, idx)

    sim._note_pick = wrapped        # sondaj: karar mekanigi degismez
    sim.run(steps)
    res = tally.summary()
    res["population"] = len(sim.agents)
    res["cooperation"] = (
        sim.stats_total["share_events"] / max(1, sim.stats_total["opp_kin"]
                                             + sim.stats_total["opp_nonkin"])
    )
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 6 dislama sondasi")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--load", default=None, help="population.npz (tohum)")
    ap.add_argument("--control", default="none", choices=("none", "random"))
    ap.add_argument("--set", dest="extra", action="append", default=[])
    args = ap.parse_args(argv)

    r = probe(args.steps, args.seed, args.load, args.control, args.extra)
    print("=" * 72)
    print(f"DISLAMA SONDASI — kontrol={args.control}, seed={args.seed}, "
          f"{args.steps} adim")
    print("=" * 72)
    print(f"  karar {r['events']:>9d}   ortalama havuz {r['pool']:.2f}   "
          f"N {r['population']}   isbirligi {r['cooperation']*100:.2f}%")
    print(f"  YAPISAL dislama   {r['structural']*100:6.1f}%   "
          "(havuz buyudukce kaciniLMAZ olarak artar — bilgi degil)")
    print(f"  BIREYSEL dislama  {r['individual']*100:6.1f}%   "
          f"({r['agents']} ajan: karsilastigi farkli partnerlerin kaci hic secilmedi)")
    print()
    print(f"  {'aday sinifi':14s} {'sayi':>10s} {'akraba':>9s} {'defter+':>9s} {'enerji':>9s}")
    for label in ("secilen", "secilmeyen"):
        p = r[label]
        print(f"  {label:14s} {p['n']:10d} {p['kin']*100:8.1f}% "
              f"{p['ledger_pos']*100:8.2f}% {p['energy']:9.3f}")
    print()
    print("  Iki satir birbirine yakinsa dislama YAPISALDIR (mekan dayatir),")
    print("  politika degil. Ayrisma varsa yon buradan okunur — ama buyuklugu")
    print("  rastgele-secim kontroluyle kiyaslanmadan kanit sayilmaz.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
