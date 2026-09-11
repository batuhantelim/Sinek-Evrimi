"""Faz 3 testleri: akrabalik etiketi, paylasim mekanigi, kontrol gruplari.

Bu dosyadaki testlerin bir kismi DENEYIN GECERLILIGINI korur, kodun degil:
`test_fitness_has_no_sharing_term` ve `test_sharing_has_net_cost_to_giver`
ihlal edilirse isbirligi bulgusu bilimsel olarak degersizdir.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import M, S
from sinek.config import load_config
from sinek.metrics import lineage_stats, social_rates, stratified_kin_bias
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]


def make(steps=0, extra=(), **over):
    ov = BASE + list(extra) + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


def force_share(sim, value=1.0):
    """Tum ajanlari paylasmaya zorlar (mekanigi beyinden bagimsiz sinamak icin)."""
    for a in sim.agents:
        a.last_motors = np.zeros(len(M), dtype=np.float32)
        a.last_motors[M["share"]] = value


class TestLineageLabels(unittest.TestCase):
    def test_founders_get_unique_surnames(self):
        sim = make(agents__initial_count=50)
        names = [a.genome.surname for a in sim.agents]
        self.assertEqual(len(set(names)), 50)

    def test_children_inherit_surname(self):
        sim = make(rules__kinship__split_rate=0.0)
        parent = sim.agents[0]
        child_genome = parent.genome.child(sim.cfg, sim.rng)
        self.assertEqual(child_genome.surname, parent.genome.surname)
        self.assertEqual(child_genome.lineage, parent.genome.lineage + 1)

    def test_lineage_stats(self):
        class G:
            def __init__(self, s):
                self.surname = s

        class A:
            def __init__(self, s):
                self.genome = G(s)

        # 4 ajan, 2 esit soy -> etkin soy sayisi 2
        st = lineage_stats([A(1), A(1), A(2), A(2)])
        self.assertEqual(st["lineage_count"], 2)
        self.assertAlmostEqual(st["lineage_effective"], 2.0, places=2)
        self.assertAlmostEqual(st["lineage_largest"], 0.5)
        # tek soy -> etkin 1
        st = lineage_stats([A(7)] * 5)
        self.assertEqual(st["lineage_count"], 1)
        self.assertAlmostEqual(st["lineage_effective"], 1.0, places=2)


class TestKinSensor(unittest.TestCase):
    def _sense_kin(self, same: bool | None):
        sim = make(agents__initial_count=2)
        a, b = sim.agents[0], sim.agents[1]
        if same is None:
            a.nearest = None
        else:
            a.nearest = b
            b.genome.surname = a.genome.surname if same else a.genome.surname + 1
        return float(a.sense(sim.world, sim.physics)[S["kin"]])

    def test_kin_sensor_values(self):
        self.assertEqual(self._sense_kin(True), 1.0)
        self.assertEqual(self._sense_kin(False), -1.0)
        self.assertEqual(self._sense_kin(None), 0.0, "komsu yoksa sensor 0 olmali")


class TestShareMechanics(unittest.TestCase):
    def test_sharing_has_net_cost_to_giver(self):
        """KURAL 2: veren, alicinin kazandigindan DAHA COK kaybetmeli."""
        sim = make(agents__initial_count=2, rules__share__overhead=1.5)
        a, b = sim.agents
        a.x, a.y = 20.0, 20.0
        b.x, b.y = 20.5, 20.0
        a.energy, b.energy = 120.0, 20.0
        a.nearest, b.nearest = b, None
        force_share(sim, 1.0)
        before_a, before_b = a.energy, b.energy

        sim._apply_social_rules()

        lost = before_a - a.energy
        gained = b.energy - before_b
        self.assertGreater(gained, 0.0, "transfer olmadi")
        self.assertAlmostEqual(lost - gained, 1.5, places=5, msg="islem maliyeti uygulanmadi")

    def test_giver_never_falls_below_floor(self):
        sim = make(agents__initial_count=2, rules__share__min_donor_energy=30.0)
        a, b = sim.agents
        a.x, a.y = 10.0, 10.0
        b.x, b.y = 10.4, 10.0
        a.energy, b.energy = 33.0, 10.0
        a.nearest, b.nearest = b, None
        force_share(sim, 1.0)
        sim._apply_social_rules()
        self.assertGreaterEqual(a.energy, 30.0 - 1e-6)

    def test_surplus_above_cap_is_wasted(self):
        """Azalan verim: tok bir sinege vermek israf, ac olana vermek hayat kurtarir."""
        sim = make(agents__initial_count=2)
        e_max = sim.physics.energy_max
        a, b = sim.agents
        a.x, a.y = 5.0, 5.0
        b.x, b.y = 5.3, 5.0
        a.energy, b.energy = e_max, e_max - 1.0
        a.nearest, b.nearest = b, None
        force_share(sim, 1.0)
        before_a = a.energy
        sim._apply_social_rules()
        self.assertLess(a.energy, before_a, "veren yine de odedi")
        self.assertLessEqual(b.energy, e_max + 1e-6, "alici tavani asti")

    def test_out_of_range_neighbour_is_not_shared_with(self):
        sim = make(agents__initial_count=2, rules__kinship__radius=2.0)
        a, b = sim.agents
        a.x, a.y = 5.0, 5.0
        b.x, b.y = 60.0, 60.0
        a.energy = 120.0
        a.nearest, b.nearest = b, None
        force_share(sim, 1.0)
        before = a.energy
        sim._apply_social_rules()
        self.assertEqual(a.energy, before)
        self.assertEqual(sim.stats_step["share_events"], 0)

    def test_share_is_recorded_by_kinship(self):
        sim = make(agents__initial_count=2)
        a, b = sim.agents
        a.x, a.y = 5.0, 5.0
        b.x, b.y = 5.3, 5.0
        a.energy, b.energy = 120.0, 20.0
        b.genome.surname = a.genome.surname      # akraba
        a.nearest, b.nearest = b, None
        force_share(sim, 1.0)
        sim._apply_social_rules()
        self.assertEqual(sim.stats_step["share_kin"], 1)
        self.assertEqual(sim.stats_step["share_nonkin"], 0)
        self.assertEqual(sim.stats_step["opp_kin"], 1)


class TestExperimentValidity(unittest.TestCase):
    def test_fitness_has_no_sharing_term(self):
        """KURAL 2: paylasim ASLA dogrudan odullendirilmez.

        Ne config'te bir paylasim agirligi olabilir, ne de fitness paylasim
        muhasebesine bakabilir. Kâr yalnizca DOLAYLI olmali.
        """
        cfg = load_config()
        weights = cfg.get("evolution.fitness").to_dict()
        for banned in ("given", "shares_made", "share", "received", "cooperation"):
            self.assertNotIn(banned, weights, f"fitness'a paylasim terimi sizmis: {banned}")

        sim = make(agents__initial_count=2)
        a = sim.agents[0]
        base = a.fitness(sim.fitness_weights)
        a.given, a.received, a.shares_made = 500.0, 500.0, 99
        self.assertEqual(a.fitness(sim.fitness_weights), base)

    def test_social_rates_are_conditional_probabilities(self):
        """Ham sayim degil, FIRSATA kosullu oran olculmeli."""
        # akrabayla 100 firsat, 40 paylasim; yabanciyla 10 firsat, 5 paylasim
        r = social_rates(
            {"opp_kin": 100, "opp_nonkin": 10, "share_kin": 40, "share_nonkin": 5,
             "share_events": 45, "share_energy": 1.0}
        )
        self.assertAlmostEqual(r["coop_in_group"], 0.40)
        self.assertAlmostEqual(r["coop_out_group"], 0.50)
        # ham sayida akraba onde (40 > 5) ama ORANDA geride: bias negatif olmali
        self.assertAlmostEqual(r["kin_bias"], -0.10)

    def test_stratified_bias_removes_a_pure_confound(self):
        """Katmanli olcu, enerjiden kaynaklanan sahte ayrimciligi silmeli.

        Kurgu: her katmanda paylasim orani akraba ve yabanci icin AYNI, ama
        akrabalar yuksek enerji katmaninda toplanmis (uzamsal kumelenmenin
        yaptigi sey). Ham fark buyuk pozitif cikar; katmanli olcu 0 demeli.
        """
        stats = {}
        # katman 0 (fakir): oran %10 — firsatlarin cogu YABANCI
        stats.update(opp_kin_0=100, shr_kin_0=10, opp_non_0=1000, shr_non_0=100)
        # katman 4 (zengin): oran %90 — firsatlarin cogu AKRABA
        stats.update(opp_kin_4=1000, shr_kin_4=900, opp_non_4=100, shr_non_4=90)
        for b in (1, 2, 3):
            stats.update({f"opp_kin_{b}": 0, f"opp_non_{b}": 0})

        raw_in = (10 + 900) / (100 + 1000)
        raw_out = (100 + 90) / (1000 + 100)
        self.assertGreater(raw_in - raw_out, 0.5, "kurgu yeterince carpitilmis olmali")
        self.assertAlmostEqual(stratified_kin_bias(stats), 0.0, places=9)

    def test_stratified_bias_keeps_a_real_effect(self):
        """Gercek ayrimcilik varsa katmanli olcu onu KORUMALI."""
        stats = {f"opp_kin_{b}": 0 for b in range(5)}
        stats.update({f"opp_non_{b}": 0 for b in range(5)})
        stats.update(opp_kin_2=500, shr_kin_2=300, opp_non_2=500, shr_non_2=100)
        self.assertAlmostEqual(stratified_kin_bias(stats), 0.4, places=6)

    def test_attack_still_guarded(self):
        """Faz 3 adim 2 sinirina saygi: sessizce yok sayma, patla."""
        sim = make(rules__attack__enabled=True)
        with self.assertRaises(NotImplementedError):
            sim.step()

    def test_no_caste_is_hardcoded(self):
        """KURAL 1: kraliçe/isci gibi roller kodda gecmemeli."""
        import pathlib

        banned = ("queen", "worker", "drone", "caste", "kralice", "isci_ajan")
        for path in pathlib.Path("sinek").rglob("*.py"):
            text = path.read_text(encoding="utf-8").lower()
            for word in banned:
                self.assertNotIn(word, text, f"{path}: rol kodlanmis gorunuyor ({word})")


class TestControls(unittest.TestCase):
    def test_random_surname_at_birth_breaks_heritability(self):
        normal = make(steps=600, rules__kinship__split_rate=0.0)
        control = make(
            steps=600,
            extra=["rules.kinship.control=random_surname_at_birth"],
            rules__kinship__split_rate=0.0,
        )
        matches_normal = sum(
            1 for a in normal.agents if a.parent_id >= 0 and a.genome.lineage > 0
        )
        self.assertGreater(matches_normal, 0, "test anlamli olacak kadar dogum olmadi")
        # kalitsal etiket -> soy sayisi ancak azalir; kalitsiz -> ayni havuzdan
        # rastgele cekilir, dolayisiyla cok daha fazla farkli etiket yasar
        self.assertGreater(
            lineage_stats(control.agents)["lineage_count"],
            lineage_stats(normal.agents)["lineage_count"],
        )

    def test_shuffle_surnames_reassigns_labels(self):
        sim = make(extra=["rules.kinship.control=shuffle_surnames"], agents__initial_count=60)
        before = [a.genome.surname for a in sim.agents]
        sim.step()
        after = [a.genome.surname for a in sim.agents[: len(before)]]
        self.assertEqual(sorted(after), sorted(before), "etiket kumesi korunmali")
        self.assertNotEqual(after, before, "hicbir etiket yer degistirmemis")

    def test_scatter_offspring_breaks_spatial_kin_structure(self):
        sim = make(extra=["rules.kinship.control=scatter_offspring"], agents__initial_count=80)
        parents = {a.id: (a.x, a.y) for a in sim.agents}
        for _ in range(400):
            sim.step()
            newborns = [a for a in sim.agents if a.parent_id in parents and a.age == 0]
            if len(newborns) >= 5:
                break
            parents = {a.id: (a.x, a.y) for a in sim.agents}
        self.assertGreaterEqual(len(newborns), 1, "hic dogum olmadi")
        far = sum(
            1
            for c in newborns
            if abs(sim.world.delta(*parents[c.parent_id], c.x, c.y)[0]) > 10.0
        )
        self.assertGreater(far, 0, "yavrular hala ebeveyn yaninda doguyor")


class TestDeterminismWithSharing(unittest.TestCase):
    def test_same_seed_same_state(self):
        a = make(steps=400, agents__initial_count=60)
        b = make(steps=400, agents__initial_count=60)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertGreater(a.stats_total["share_events"], 0, "hic paylasim olmadi, test bos")

    def test_controls_are_also_deterministic(self):
        for control in ("shuffle_surnames", "random_surname_at_birth", "scatter_offspring"):
            x = make(steps=200, extra=[f"rules.kinship.control={control}"], agents__initial_count=50)
            y = make(steps=200, extra=[f"rules.kinship.control={control}"], agents__initial_count=50)
            self.assertEqual(x.state_hash(), y.state_hash(), control)


if __name__ == "__main__":
    unittest.main()
