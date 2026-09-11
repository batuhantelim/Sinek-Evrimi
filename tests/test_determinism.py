"""Determinizm: ayni seed -> ayni sonuc; farkli seed -> farkli sonuc."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false", "agents.initial_count=40"]

# Faz 1 (refleks + klon) ve Faz 2 (rnn + mutasyon + nesil dongusu) ayri ayri
# sinanir: mutasyon ve secilim de rastgelelik tuketir, akis bozulursa hash kacar.
PHASE1 = ["brain.type=reflex", "evolution.enabled=false", "evolution.mode=steady_state",
          "evolution.founder_spread=0.0", "rules.share.enabled=false"]
PHASE2 = ["brain.type=rnn", "evolution.enabled=true", "evolution.mode=generational",
          "evolution.generation_length=40", "evolution.founder_spread=1.0",
          "rules.share.enabled=false"]
PHASE3 = ["brain.type=rnn", "evolution.enabled=true", "evolution.mode=steady_state",
          "rules.share.enabled=true"]


def run(steps=120, phase=PHASE2, **over):
    ov = BASE + list(phase) + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    sim.run(steps)
    return sim


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_state_phase1(self):
        a, b = run(phase=PHASE1), run(phase=PHASE1)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertEqual(a.population, b.population)

    def test_same_seed_same_state_phase2(self):
        """Nesil sinirlarini asarak: mutasyon + secilim de deterministik olmali."""
        a, b = run(), run()
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertGreaterEqual(a.generation, 2, "test nesil sinirini asmali")

    def test_same_seed_same_state_phase3(self):
        """Paylasim transferleri de deterministik sirada uygulanmali."""
        a, b = run(phase=PHASE3), run(phase=PHASE3)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertGreater(a.stats_total["share_events"], 0, "hic paylasim olmadi, test bos")

    def test_different_seed_diverges(self):
        a, b = run(seed=1), run(seed=2)
        self.assertNotEqual(a.state_hash(), b.state_hash())

    def test_step_by_step_matches_run(self):
        a = run(steps=0)
        for _ in range(60):
            a.step()
        b = run(steps=60)
        self.assertEqual(a.state_hash(), b.state_hash())


if __name__ == "__main__":
    unittest.main()
