"""Faz 6 testleri: partner secimi.

En onemlisi `test_choice_policy_is_not_hardcoded` ve
`test_zero_weights_match_no_choice`: birincisi kaynakta elle yazilmis bir
tercih katsayisi olmadigini, ikincisi agirliklar 0 iken davranisin secimsiz
kolla OZDES oldugunu — yani secimin kendisinin bir yanlilik getirmedigini —
dogrular. Ikisi de ihlal edilirse "partner secimi isbirligini kurdu"
bulgusu degersizdir.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]
#: Secimin kendi etkisini izole etmek icin: kurucular ozdes, mutasyon kapali.
CLONE = ["evolution.enabled=false", "evolution.founder_spread=0.0"]


def make(steps=0, extra=(), **over):
    ov = BASE + list(extra) + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


class TestCandidatePool(unittest.TestCase):
    def test_candidates_are_sorted_by_distance(self):
        sim = make(agents__initial_count=6)
        a = sim.agents[0]
        a.x, a.y = 50.0, 50.0
        for i, other in enumerate(sim.agents[1:], start=1):
            other.x, other.y = 50.0 + 0.3 * i, 50.0
        sim.hash.build(sim.agents)
        pool = sim.hash.candidates(a, 5.0, sim.world, 4)
        dists = [d2 for _o, d2 in pool]
        self.assertEqual(dists, sorted(dists))
        self.assertLessEqual(len(pool), 4)
        self.assertNotIn(a.id, [o.id for o, _ in pool], "kendini aday saymamali")

    def test_candidates_respect_the_radius(self):
        sim = make(agents__initial_count=3)
        a, b, c = sim.agents
        a.x, a.y = 10.0, 10.0
        b.x, b.y = 10.5, 10.0      # menzilde
        c.x, c.y = 90.0, 90.0      # disarida
        sim.hash.build(sim.agents)
        pool = sim.hash.candidates(a, 2.0, sim.world, 4)
        self.assertEqual([o.id for o, _ in pool], [b.id])

    def test_candidates_k1_matches_nearest(self):
        sim = make(agents__initial_count=40)
        sim.hash.build(sim.agents)
        for a in sim.agents[:10]:
            pool = sim.hash.candidates(a, sim.kin_radius, sim.world, 1)
            near = sim.hash.nearest(a, sim.kin_radius, sim.world)
            self.assertEqual(pool[0][0].id if pool else None,
                             near.id if near else None)


class TestChoiceIsEvolvable(unittest.TestCase):
    def test_zero_weights_match_no_choice(self):
        """Agirliklar 0 iken skor herkeste esittir ve beraberligi MESAFE bozar:
        davranis secimsiz kolla OZDES olmali. Aksi halde secim mekanigi tek
        basina bir yanlilik getiriyor demektir."""
        with_choice = make(steps=250, extra=CLONE, rules__partner__enabled=True)
        without = make(steps=250, extra=CLONE, rules__partner__enabled=False)
        self.assertEqual(with_choice.state_hash(), without.state_hash())

    def test_a_weight_actually_changes_the_target(self):
        """pick_kin buyukse akraba olmayan en yakini gecebilmeli."""
        sim = make(agents__initial_count=3, rules__partner__enabled=True)
        a, near, far = sim.agents
        a.x, a.y = 30.0, 30.0
        near.x, near.y = 30.3, 30.0
        far.x, far.y = 30.8, 30.0
        a.genome.surname = 1
        near.genome.surname = 2      # yabanci, ama daha yakin
        far.genome.surname = 1       # akraba, ama uzak
        sim.hash.build(sim.agents)
        for w in a.genome.params:
            if w.startswith("pick"):
                a.genome.params[w] = 0.0
        self.assertEqual(sim._choose_partner(a).id, near.id, "agirlik 0 iken en yakin")
        a.genome.params["pick_kin"] = 2.0
        self.assertEqual(sim._choose_partner(a).id, far.id, "akrabalik agirligi ise yaramadi")

    def test_choice_policy_is_not_hardcoded(self):
        """KURAL: kodda elle yazilmis tercih katsayisi olmamali.

        `_choose_partner` icindeki her agirlik `genome.params`'tan gelmeli.
        """
        path = os.path.join(os.path.dirname(__file__), "..", "sinek", "simulation.py")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        body = src.split("def _choose_partner(")[1].split("\n    def ")[0]
        for name in ("pick_kin", "pick_ledger", "pick_need", "pick_energy", "pick_dist"):
            self.assertIn(f'p.get("{name}"', body, f"{name} genomdan okunmuyor")
        # skor satirinda ciplak sayisal katsayi olmamali (1.0/-1.0 kin isareti haric)
        score = body.split("score = (")[1].split(")")[0]
        for tok in score.replace("+", " ").replace("*", " ").split():
            if tok.replace(".", "").isdigit():
                self.assertIn(tok, ("1.0",), f"skorda elle yazilmis katsayi: {tok}")

    def test_weights_are_in_config_and_bounded(self):
        cfg = load_config()
        params = cfg.genome.params.to_dict()
        bounds = cfg.evolution.param_bounds.to_dict()
        for name in ("pick_kin", "pick_ledger", "pick_need", "pick_energy", "pick_dist"):
            self.assertIn(name, params)
            self.assertEqual(params[name], 0.0, "politika sifirdan baslamali")
            self.assertIn(name, bounds, "mutasyon sinirlari eksik")


class TestControls(unittest.TestCase):
    def test_random_control_ignores_the_weights(self):
        """Rastgele kontrolde genom agirliklari hicbir sey yapmamali."""
        sim = make(agents__initial_count=3, rules__partner__enabled=True,
                   extra=["rules.partner.control=random"])
        a, near, far = sim.agents
        a.x, a.y = 30.0, 30.0
        near.x, near.y = 30.3, 30.0
        far.x, far.y = 30.8, 30.0
        a.genome.surname, near.genome.surname, far.genome.surname = 1, 2, 1
        a.genome.params["pick_kin"] = 5.0
        sim.hash.build(sim.agents)
        picks = {sim._choose_partner(a).id for _ in range(40)}
        self.assertEqual(picks, {near.id, far.id}, "rastgele kontrol iki adayi da secmeli")

    def test_unknown_partner_control_fails_loudly(self):
        with self.assertRaises(ValueError):
            make(rules__partner__control="sihirli")

    def test_choice_off_matches_phase5(self):
        a = make(steps=200, extra=CLONE, rules__partner__enabled=False)
        b = make(steps=200, extra=CLONE, rules__partner__enabled=False)
        self.assertEqual(a.state_hash(), b.state_hash())


class TestExperimentValidity(unittest.TestCase):
    def test_choice_does_not_break_conservation(self):
        sim = make(steps=300, agents__initial_count=150,
                   rules__partner__enabled=True, rules__share__need_bonus=3.0)
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim yok, test bos")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=6)

    def test_selectivity_is_measured_against_the_pool(self):
        """`pick_kin_sel` havuz ortalamasina karsi okunmali: politika yoksa ~0."""
        from sinek.metrics import social_rates
        sim = make(steps=300, agents__initial_count=120, extra=CLONE,
                   rules__partner__enabled=True)
        r = social_rates(sim.stats_total)
        self.assertGreater(sim.stats_total["pick_events"], 0)
        self.assertAlmostEqual(r["pick_kin_sel"], 0.0, places=2,
                               msg="politika yokken secicilik 0 olmali")

    def test_fitness_has_no_choice_term(self):
        path = os.path.join(os.path.dirname(__file__), "..", "sinek", "agent.py")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        body = src.split("def fitness(")[1].split("def ")[0]
        for banned in ("pick_", "ledger", "given", "received"):
            self.assertNotIn(banned, body, f"fitness '{banned}' okuyor")


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_state(self):
        a = make(steps=200, rules__partner__enabled=True)
        b = make(steps=200, rules__partner__enabled=True)
        self.assertEqual(a.state_hash(), b.state_hash())


if __name__ == "__main__":
    unittest.main()
