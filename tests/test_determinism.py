"""Determinizm: ayni seed -> ayni sonuc; farkli seed -> farkli sonuc."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false", "agents.initial_count=40"]


def run(steps=120, **over):
    ov = BASE + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    sim.run(steps)
    return sim


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_state(self):
        a, b = run(), run()
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertEqual(a.population, b.population)

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
