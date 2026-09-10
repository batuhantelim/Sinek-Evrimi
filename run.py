#!/usr/bin/env python3
"""Sinek Evrimi — komut satiri girisi.

Ornekler:
    python run.py                                   # config.yaml ile calistir
    python run.py --steps 1000 --viz none
    python run.py --viz pygame                      # canli pencere
    python run.py --set genome.params.food_attraction=0.0 --name kontrol
    python run.py --config deneylerim/kitlik.yaml
    python run.py --check-determinism
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from sinek.config import DEFAULT_CONFIG_PATH, load_config
from sinek.metrics import Metrics
from sinek.simulation import Simulation
from sinek.sinks import make_sink

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evrimlesen sinek kolonisi — yapay yasam simulasyonu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="YAML config yolu")
    p.add_argument("--seed", type=int, default=None, help="config'teki seed'i ezer")
    p.add_argument("--steps", type=int, default=None, help="adim sayisi")
    p.add_argument("--name", default=None, help="kosum adi (runs/<name>/)")
    p.add_argument("--out", default=os.path.join(REPO_ROOT, "runs"), help="cikti kok dizini")
    p.add_argument("--viz", choices=["none", "frames", "pygame"], default=None)
    p.add_argument("--no-metrics", action="store_true", help="CSV yazma")
    p.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="ANAHTAR=DEGER",
        help="config'i ez, orn: --set world.food.regrowth_rate=0.02 (tekrarlanabilir)",
    )
    p.add_argument(
        "--check-determinism",
        action="store_true",
        help="ayni seed'le iki kez calistirip durum parmak izlerini karsilastir",
    )
    p.add_argument("--quiet", action="store_true")
    return p.parse_args(argv)


def build_config(args: argparse.Namespace):
    cfg = load_config(args.config, args.overrides)
    if args.seed is not None:
        cfg.set("seed", args.seed)
    if args.steps is not None:
        cfg.set("run.steps", args.steps)
    if args.name is not None:
        cfg.set("run.name", args.name)
    if args.viz is not None:
        cfg.set("viz.mode", args.viz)
    if args.no_metrics:
        cfg.set("metrics.enabled", False)
    return cfg


def check_determinism(cfg, steps: int) -> int:
    hashes = []
    for i in range(2):
        cfg.set("viz.mode", "none")
        cfg.set("metrics.enabled", False)
        sim = Simulation(cfg)
        sim.run(steps)
        hashes.append((sim.state_hash(), sim.population))
        print(f"  kosum {i + 1}: hash={hashes[-1][0]}  populasyon={hashes[-1][1]}")
    ok = hashes[0] == hashes[1]
    print("DETERMINIZM:", "TAMAM (ayni seed -> ayni sonuc)" if ok else "BOZUK!")
    return 0 if ok else 1


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = build_config(args)
    steps = int(cfg.run.steps)

    if args.check_determinism:
        return check_determinism(cfg, min(steps, 300))

    out_dir = os.path.join(args.out, str(cfg.run.name))
    os.makedirs(out_dir, exist_ok=True)
    cfg.dump(os.path.join(out_dir, "config_used.yaml"))

    sim = Simulation(cfg)
    metrics = Metrics(cfg, out_dir)
    sink = make_sink(cfg, out_dir)
    log_every = max(1, int(cfg.get("run.log_every", 200)))

    if not args.quiet:
        print(f"== Sinek Evrimi | kosum '{cfg.run.name}' | seed {sim.seed} ==")
        print(
            f"   dunya {sim.world.width}x{sim.world.height} | "
            f"beyin '{cfg.brain.type}' | mutasyon "
            f"{'ACIK' if cfg.get('evolution.enabled') else 'KAPALI (klonlar)'} | "
            f"{steps} adim"
        )
        print(f"   cikti: {out_dir}")
        print(f"   {'adim':>6} {'N':>5} {'enerji':>7} {'yemek%':>7} {'dogum':>6} {'olum':>6} {'kume':>6}")

    t0 = time.time()
    try:
        for _ in range(steps):
            sim.step()
            row = metrics.record(sim)
            if row is not None:
                sim.last_metrics = row
            sink.emit(sim)

            if not args.quiet and sim.step_index % log_every == 0:
                r = sim.last_metrics or {}
                print(
                    f"   {sim.step_index:6d} {sim.population:5d} "
                    f"{r.get('mean_energy', 0):7.1f} {r.get('food_fill', 0) * 100:7.1f} "
                    f"{r.get('births', 0):6d} {r.get('deaths', 0):6d} {r.get('clustering', 0):6.2f}"
                )
            if not sink.alive:
                print("   (pencere kapatildi)")
                break
            if not sim.agents and bool(cfg.get("run.stop_if_extinct", True)):
                print(f"   !! koloni {sim.step_index}. adimda tukendi")
                break
    except KeyboardInterrupt:
        print("\n   (kullanici durdurdu)")
    finally:
        sink.close()
        metrics.close()

    elapsed = time.time() - t0
    summary = [
        "",
        f"== OZET ({elapsed:.1f} s, {sim.step_index} adim, "
        f"{elapsed / max(1, sim.step_index) * 1000:.1f} ms/adim) ==",
        metrics.summary(),
    ]
    if metrics.path:
        summary.append(f"  metrik CSV        : {metrics.path}")
    frames = getattr(sink, "paths", None)
    if frames:
        summary.append(f"  kareler           : {len(frames)} adet -> {os.path.dirname(frames[0])}")
    text = "\n".join(summary)
    print(text)
    with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8") as fh:
        fh.write(text.strip() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
