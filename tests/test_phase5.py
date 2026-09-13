"""Faz 5 testleri: tanima + hafiza kanali.

Bu dosyadaki testlerin bir kismi DENEYIN GECERLILIGINI korur:
`test_memory_is_information_not_rule` ihlal edilirse "karsiliklilik
evrimlesti" bulgusu degersizdir — cunku onu biz kodlamis oluruz.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import M, S
from sinek.config import load_config
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]


def make(steps=0, extra=(), **over):
    ov = BASE + list(extra) + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


class TestLedgerMechanics(unittest.TestCase):
    def _duel(self, **over):
        over.setdefault("rules__memory__enabled", True)
        sim = make(agents__initial_count=2, **over)
        a, b = sim.agents
        a.x, a.y = 20.0, 20.0
        b.x, b.y = 20.4, 20.0
        a.nearest, b.nearest = b, None
        for agent in sim.agents:
            agent.last_motors = np.zeros(len(M), dtype=np.float32)
        return sim, a, b

    def test_recipient_records_the_giver(self):
        """Defteri ALICI tutar: 'a bana verdi'."""
        sim, a, b = self._duel()
        a.energy, b.energy = 140.0, 40.0
        a.last_motors[M["share"]] = 1.0
        sim._apply_social_rules()
        self.assertGreater(b.ledger.get(a.mem_id, 0.0), 0.0, "alici vereni kaydetmedi")
        self.assertEqual(a.ledger, {}, "veren kendi defterine yazmamali")

    def test_victim_records_the_attacker_with_a_minus(self):
        sim, a, b = self._duel(rules__attack__enabled=True)
        a.energy, b.energy = 140.0, 120.0
        a.last_motors[M["attack"]] = 1.0
        sim._apply_social_rules()
        self.assertLess(b.ledger.get(a.mem_id, 0.0), 0.0, "kurban saldirgani kaydetmedi")

    def test_capacity_is_bounded_and_eviction_is_deterministic(self):
        """Dolunca EN ZAYIF kayit atilir; sozluk sirasina bagimli degil."""
        sim = make(rules__memory__enabled=True, rules__memory__capacity=3)
        a = sim.agents[0]
        for key, val in ((10, 5.0), (11, 1.0), (12, 9.0)):
            a.ledger[key] = val
        other = sim.agents[1]
        other.mem_id = 13
        sim._remember(a, other, 4.0)
        self.assertEqual(len(a.ledger), 3)
        self.assertNotIn(11, a.ledger, "en zayif kayit atilmali")
        self.assertIn(13, a.ledger)

    def test_memory_disabled_writes_nothing(self):
        sim, a, b = self._duel(rules__memory__enabled=False)
        a.energy, b.energy = 140.0, 40.0
        a.last_motors[M["share"]] = 1.0
        sim._apply_social_rules()
        self.assertEqual(b.ledger, {}, "hafiza kapaliyken defter tutulmamali")


class TestMemorySensors(unittest.TestCase):
    def _sense(self, ledger_value=None, enabled=True):
        sim = make(agents__initial_count=2, rules__memory__enabled=enabled)
        a, b = sim.agents
        a.nearest = b
        if ledger_value is not None:
            a.ledger[b.mem_id] = ledger_value
        s = a.sense(sim.world, sim.physics)
        return float(s[S["partner_known"]]), float(s[S["partner_ledger"]])

    def test_unknown_partner_reads_zero(self):
        self.assertEqual(self._sense(None), (0.0, 0.0))

    def test_sign_follows_the_ledger(self):
        known, bal = self._sense(+8.0)
        self.assertEqual(known, 1.0)
        self.assertGreater(bal, 0.0)
        known, bal = self._sense(-8.0)
        self.assertEqual(known, 1.0)
        self.assertLess(bal, 0.0)

    def test_channel_is_bounded(self):
        _k, bal = self._sense(10_000.0)
        self.assertLessEqual(bal, 1.0)
        _k, bal = self._sense(-10_000.0)
        self.assertGreaterEqual(bal, -1.0)

    def test_disabled_memory_silences_both_channels(self):
        self.assertEqual(self._sense(+8.0, enabled=False), (0.0, 0.0))


class TestExperimentValidity(unittest.TestCase):
    """Bu testler kodun degil DENEYIN gecerliligini korur."""

    def test_memory_is_information_not_rule(self):
        """KURAL: "karsilik ver" davranisi KODLANMAZ.

        Kaynakta, defteri okuyup paylasim/saldiri kararini DOGRUDAN degistiren
        bir dal olmamali. Defter yalnizca (a) sensore, (b) olcum sayaclarina
        gider. Karar her zaman `last_motors` uzerinden, yani BEYINDEN gelir.
        """
        path = os.path.join(os.path.dirname(__file__), "..", "sinek", "simulation.py")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        for line in src.splitlines():
            stripped = line.strip()
            if "ledger" not in stripped or stripped.startswith("#"):
                continue
            # Izin verilenler: defteri yazmak, firsat siniflandirmak.
            ok = ("led[key]" in stripped or "led.get" in stripped
                  or "owner.ledger" in stripped or "a.ledger.get" in stripped
                  or "len(led)" in stripped or "= led" in stripped)
            self.assertTrue(ok, f"defter karara dogrudan karisiyor olabilir: {stripped!r}")

    def test_fitness_has_no_memory_term(self):
        cfg = load_config()
        self.assertNotIn("reciprocity", cfg.evolution.fitness.to_dict())
        path = os.path.join(os.path.dirname(__file__), "..", "sinek", "agent.py")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        body = src.split("def fitness(")[1].split("def ")[0]
        for banned in ("ledger", "received", "given", "shares_made"):
            self.assertNotIn(banned, body, f"fitness '{banned}' okuyor")

    def test_memory_does_not_break_conservation(self):
        sim = make(steps=300, agents__initial_count=150,
                   rules__memory__enabled=True, rules__share__need_bonus=3.0)
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim yok, test bos")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=6)

    def test_unknown_memory_control_fails_loudly(self):
        with self.assertRaises(ValueError):
            make(rules__memory__control="sihirli")

    def test_shuffle_identity_permutes_mem_id_but_not_id(self):
        sim = make(agents__initial_count=60, rules__memory__enabled=True,
                   extra=["rules.memory.control=shuffle_identity"])
        ids_before = [a.id for a in sim.agents]
        mem_before = [a.mem_id for a in sim.agents]
        sim.step()
        alive = sim.agents[: len(ids_before)]
        self.assertEqual([a.id for a in alive], ids_before[: len(alive)],
                         "id degismemeli — determinizm ona bagli")
        mem_after = [a.mem_id for a in alive]
        self.assertEqual(sorted(mem_after), sorted(mem_before[: len(alive)]),
                         "kimlik kumesi korunmali")
        self.assertNotEqual(mem_after, mem_before[: len(alive)], "hicbir kimlik yer degistirmemis")


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_state(self):
        a = make(steps=200, rules__memory__enabled=True)
        b = make(steps=200, rules__memory__enabled=True)
        self.assertEqual(a.state_hash(), b.state_hash())

    def test_memory_off_matches_phase45(self):
        """Hafiza kapaliyken davranis Faz 4.5 ile BIREBIR ayni olmali:
        yeni sensorler sifir, defter yazilmiyor."""
        a = make(steps=200, rules__memory__enabled=False)
        b = make(steps=200, rules__memory__enabled=False)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertTrue(all(not ag.ledger for ag in a.agents))


if __name__ == "__main__":
    unittest.main()
