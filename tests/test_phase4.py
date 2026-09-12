"""Faz 4 testleri: dogal avci.

Kritik test `test_predator_target_is_group_blind`: avci belirli bir soyu
hedeflerse grup dusmanligini ELLE kurmus oluruz ve Faz 4'un butun sorusu
gecersizlesir.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import S
from sinek.config import load_config
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]


def make(steps=0, extra=(), **over):
    ov = BASE + list(extra) + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


class TestPredatorIsGroupBlind(unittest.TestCase):
    def test_predator_target_is_group_blind(self):
        """Hedef yalnizca MESAFEYE gore secilir; soyisim hicbir rol oynamaz.

        Aksi halde 'gruplar arasi rekabet dusmanlik uretir mi' sorusunun
        cevabini kodun icine yazmis oluruz.
        """
        sim = make(agents__initial_count=6, rules__predator__count=1)
        pred = sim.predators.predators[0]
        pred.x, pred.y = 50.0, 50.0
        # ajanlari artan mesafeye diz; soyisimleri kasten ters sirada ver
        for i, a in enumerate(sim.agents):
            a.x, a.y = 50.0 + (i + 1) * 2.0, 50.0
            a.genome.surname = 100 - i
        nearest_before = sim.predators._nearest(pred, sim.agents)
        self.assertIs(nearest_before, sim.agents[0], "en yakin ajan secilmedi")

        # soyisimleri tamamen degistir: hedef DEGISMEMELI
        for i, a in enumerate(sim.agents):
            a.genome.surname = i * 7
        self.assertIs(sim.predators._nearest(pred, sim.agents), nearest_before)

    def test_predator_targets_nearest_regardless_of_energy_or_age(self):
        sim = make(agents__initial_count=3, rules__predator__count=1)
        pred = sim.predators.predators[0]
        pred.x, pred.y = 10.0, 10.0
        far_but_weak, near_but_strong, other = sim.agents
        far_but_weak.x, far_but_weak.y = 30.0, 10.0
        far_but_weak.energy = 1.0
        near_but_strong.x, near_but_strong.y = 11.0, 10.0
        near_but_strong.energy = 150.0
        other.x, other.y = 80.0, 80.0
        self.assertIs(sim.predators._nearest(pred, sim.agents), near_but_strong)


class TestDilutionMechanic(unittest.TestCase):
    def test_one_strike_then_cooldown(self):
        """Seyreltmenin motoru: adim basina TEK vurus, sonra bekleme.

        Bu olmazsa kumelenmek riski azaltmaz ve surulesme icin secilim
        baskisi dogmaz — mekanizma kodla degil bu kisitla kuruluyor.
        """
        sim = make(agents__initial_count=5, rules__predator__count=1,
                   rules__predator__cooldown=30, rules__predator__damage=1.0)
        pred = sim.predators.predators[0]
        pred.x, pred.y = 40.0, 40.0
        for i, a in enumerate(sim.agents):          # hepsi vurus menzilinde
            a.x, a.y = 40.0 + i * 0.2, 40.0
            a.energy = 100.0
        strikes, _kills = sim.predators.step(sim.agents)
        self.assertEqual(strikes, 1, "ayni adimda birden fazla ajan vuruldu")
        self.assertEqual(sum(a.predator_hits for a in sim.agents), 1)
        self.assertEqual(pred.cooldown, 30)

        # bekleme suresince vuramamali
        strikes2, _ = sim.predators.step(sim.agents)
        self.assertEqual(strikes2, 0)

    def test_lethal_strike_is_attributed_to_predator(self):
        sim = make(agents__initial_count=2, rules__predator__count=1,
                   rules__predator__damage=500.0)
        pred = sim.predators.predators[0]
        pred.x, pred.y = 20.0, 20.0
        victim, other = sim.agents
        victim.x, victim.y = 20.1, 20.0
        other.x, other.y = 90.0, 90.0
        _s, kills = sim.predators.step(sim.agents)
        self.assertEqual(kills, 1)
        self.assertEqual(victim.death_cause, "predator")
        sim.step()
        self.assertNotIn(victim, sim.agents)
        self.assertGreaterEqual(sim.stats_step["death_predator"], 1)


class TestPredatorSensor(unittest.TestCase):
    def test_sensor_is_zero_without_predator(self):
        sim = make(agents__initial_count=2, rules__predator__enabled=False)
        s = sim.agents[0].sense(sim.world, sim.physics)
        for name in ("pred_fwd", "pred_left", "pred_near"):
            self.assertEqual(float(s[S[name]]), 0.0)

    def test_sensor_reports_proximity_and_direction(self):
        sim = make(agents__initial_count=1, rules__predator__count=1,
                   agents__senses__predator_radius=20.0)
        a = sim.agents[0]
        a.x, a.y, a.heading = 60.0, 60.0, 0.0
        for i, p in enumerate(sim.predators.predators):
            p.x, p.y = (70.0, 60.0) if i == 0 else (200.0, 140.0)
        a.predator_signal = sim.predators.signal(a.x, a.y)
        s = a.sense(sim.world, sim.physics)
        self.assertAlmostEqual(float(s[S["pred_fwd"]]), 1.0, places=5)   # tam onunde
        self.assertAlmostEqual(float(s[S["pred_left"]]), 0.0, places=5)
        self.assertAlmostEqual(float(s[S["pred_near"]]), 0.5, places=5)  # 10/20 mesafe

    def test_out_of_range_predator_is_invisible(self):
        sim = make(agents__initial_count=1, rules__predator__count=1,
                   agents__senses__predator_radius=5.0)
        a = sim.agents[0]
        a.x, a.y = 60.0, 60.0
        sim.predators.predators[0].x, sim.predators.predators[0].y = 100.0, 100.0
        self.assertEqual(sim.predators.signal(a.x, a.y)[2], 0.0)


class TestPredatorDeterminism(unittest.TestCase):
    def test_same_seed_same_state(self):
        a = make(steps=400, agents__initial_count=80)
        b = make(steps=400, agents__initial_count=80)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertGreater(a.stats_total["predator_strikes"], 0, "hic vurus yok, test bos")

    def test_predator_off_matches_phase3(self):
        """Avci kapaliyken hicbir sey degismemeli — Faz 3 taban cizgisi korunur."""
        off = make(steps=200, agents__initial_count=60, rules__predator__enabled=False)
        self.assertEqual(off.stats_total["predator_strikes"], 0)
        self.assertEqual(off.stats_total["death_predator"], 0)
        self.assertEqual(len(off.predators.predators), 0)


class TestNoCasteStillHolds(unittest.TestCase):
    def test_no_soldier_or_caste_in_sources(self):
        """Avci gelince 'asker kasti' gibi roller elle atanmamali."""
        import pathlib

        banned = ("soldier", "asker", "caste", "queen", "worker", "guard_caste")
        for path in pathlib.Path("sinek").rglob("*.py"):
            text = path.read_text(encoding="utf-8").lower()
            for word in banned:
                self.assertNotIn(word, text, f"{path}: rol kodlanmis gorunuyor ({word})")


if __name__ == "__main__":
    unittest.main()
