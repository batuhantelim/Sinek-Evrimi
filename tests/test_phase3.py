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
from sinek.metrics import kin_assortment, lineage_stats, social_rates, stratified_kin_bias
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


class TestNeedSensor(unittest.TestCase):
    def test_neighbour_need_tracks_recipient_energy(self):
        sim = make(agents__initial_count=2)
        a, b = sim.agents
        a.nearest = b
        e_max = sim.physics.energy_max

        b.energy = e_max
        self.assertAlmostEqual(float(a.sense(sim.world, sim.physics)[S["neighbor_need"]]), 0.0)
        b.energy = e_max * 0.25
        self.assertAlmostEqual(
            float(a.sense(sim.world, sim.physics)[S["neighbor_need"]]), 0.75, places=5
        )
        a.nearest = None
        self.assertEqual(float(a.sense(sim.world, sim.physics)[S["neighbor_need"]]), 0.0)


class TestHamiltonAccounting(unittest.TestCase):
    def test_raw_energy_benefit_never_exceeds_cost(self):
        """Ham enerjide b <= c YAPISALDIR: veren amount+overhead kaybeder,
        alici en fazla amount kazanir. Hamilton kurali ancak enerjinin
        fitness'a donusumunun dogrusal olmadigi yerde saglanabilir."""
        sim = make(steps=400, agents__initial_count=150)
        cost = sim.stats_total["share_cost"]
        benefit = sim.stats_total["share_benefit"]
        self.assertGreater(cost, 0.0, "hic paylasim olmadi, test bos")
        self.assertLessEqual(benefit, cost + 1e-6)
        self.assertLessEqual(social_rates(sim.stats_total)["bc_ratio"], 1.0 + 1e-9)

    def test_kin_assortment_scale(self):
        """0 = akrabalar rastgele dagilmis, 1 = komsular daima akraba."""
        self.assertAlmostEqual(kin_assortment(20, 80, 0.20)["kin_assortment"], 0.0, places=6)
        self.assertAlmostEqual(kin_assortment(100, 0, 0.20)["kin_assortment"], 1.0, places=6)
        self.assertLess(kin_assortment(5, 95, 0.20)["kin_assortment"], 0.0)

    def test_lineage_stats_reports_mixing_baseline(self):
        class G:
            def __init__(self, s):
                self.surname = s

        class A:
            def __init__(self, s):
                self.genome = G(s)

        # yari yariya iki soy -> iyi karismis dunyada akraba olasiligi 0.5
        self.assertAlmostEqual(
            lineage_stats([A(1), A(1), A(2), A(2)])["kin_expected"], 0.5, places=5
        )


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

    def test_sharing_conserves_energy_by_default(self):
        """KORUNUM. Paylasim enerji YARATMAMALI.

        Faz 4.5'te eklendi: `need_bonus` "alicinin donusum verimi" diye
        belgelenmisken GERCEK enerji olarak uygulaniyordu. %90 isbirligi olan
        bir kosumda paylasimin urettigi enerji yenen yemege esitleniyordu —
        koloniyi cevre degil bu pompa besliyordu.
        """
        sim = make(steps=400, agents__initial_count=150, rules__share__need_bonus=3.0)
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim olmadi, test bos")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=6)

    def test_recipient_never_gains_more_than_the_giver_loses(self):
        """Tek transferde ham enerji korunumu, need_bonus acikken."""
        sim = make(agents__initial_count=2, rules__share__need_bonus=3.0)
        a, b = sim.agents
        a.x, a.y = 12.0, 12.0
        b.x, b.y = 12.4, 12.0
        a.energy, b.energy = 150.0, 10.0     # alici cok ac -> carpan azami
        a.nearest, b.nearest = b, None
        force_share(sim, 1.0)
        before_a, before_b = a.energy, b.energy
        sim._apply_social_rules()
        lost, gained = before_a - a.energy, b.energy - before_b
        self.assertGreater(gained, 0.0, "transfer olmadi")
        self.assertLessEqual(gained, lost + 1e-9, "alici vericinin kaybindan fazlasini aldi")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=9)

    def test_energy_mode_is_explicitly_non_conservative(self):
        """Eski mod hala uretilebilir — ama SESSIZ degil: kendi sayaciyla
        enerji yarattigini itiraf eder."""
        sim = make(
            steps=400, agents__initial_count=150,
            rules__share__need_bonus=3.0, rules__share__need_mode="energy",
        )
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim olmadi, test bos")
        self.assertGreater(sim.stats_total["energy_created"], 0.0)

    def test_unknown_need_mode_fails_loudly(self):
        with self.assertRaises(ValueError):
            make(steps=1, rules__share__need_mode="sihirli")

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
        a.attacks_made, a.damage_dealt, a.stolen = 99, 500.0, 500.0
        self.assertEqual(a.fitness(sim.fitness_weights), base)

    def test_fitness_has_no_attack_term(self):
        """KURAL 2 saldiri icin de gecerli: 'yabanciya saldirdin diye +puan' YOK."""
        cfg = load_config()
        weights = cfg.get("evolution.fitness").to_dict()
        for banned in ("attack", "attacks_made", "damage_dealt", "stolen", "hostility"):
            self.assertNotIn(banned, weights, f"fitness'a saldiri terimi sizmis: {banned}")

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

    def test_no_caste_is_hardcoded(self):
        """KURAL 1: kraliçe/isci gibi roller kodda gecmemeli."""
        import pathlib

        banned = ("queen", "worker", "drone", "caste", "kralice", "isci_ajan")
        for path in pathlib.Path("sinek").rglob("*.py"):
            text = path.read_text(encoding="utf-8").lower()
            for word in banned:
                self.assertNotIn(word, text, f"{path}: rol kodlanmis gorunuyor ({word})")


class TestAttackMechanics(unittest.TestCase):
    def _duel(self, target_energy, **over):
        sim = make(agents__initial_count=2, **over)
        a, b = sim.agents
        a.x, a.y = 30.0, 30.0
        b.x, b.y = 30.4, 30.0
        a.energy, b.energy = 120.0, target_energy
        a.nearest, b.nearest = b, None
        for agent in sim.agents:
            agent.last_motors = np.zeros(len(M), dtype=np.float32)
        a.last_motors[M["attack"]] = 1.0
        before = (a.energy, b.energy)
        sim._apply_social_rules()
        return sim, a, b, before

    def test_attack_transfers_and_damages(self):
        sim, a, b, (a0, b0) = self._duel(100.0, rules__attack__cost=2.0,
                                         rules__attack__damage=8.0,
                                         rules__attack__steal_ratio=0.5)
        self.assertEqual(sim.stats_step["attack_events"], 1)
        self.assertAlmostEqual(b0 - b.energy, 8.0, places=5, msg="hedef zarar gormedi")
        # saldirgan: -cost +calinan
        self.assertAlmostEqual(a.energy - a0, -2.0 + 4.0, places=5)

    def test_attacking_a_poor_target_is_a_net_loss(self):
        """Maliyet sabit, kazanc hedefin enerjisiyle sinirli -> fakire saldirmak zarar.

        'Herkes herkese saldirir' dejenere cozumunu engelleyen sey budur.
        """
        _sim, a, _b, (a0, _b0) = self._duel(1.0, rules__attack__cost=2.0,
                                            rules__attack__damage=8.0,
                                            rules__attack__steal_ratio=0.5)
        self.assertLess(a.energy, a0, "fakir hedefe saldiri saldirgana kar getirmis")

    def test_share_and_attack_are_mutually_exclusive(self):
        sim = make(agents__initial_count=2)
        a, b = sim.agents
        a.x, a.y = 10.0, 10.0
        b.x, b.y = 10.3, 10.0
        a.energy, b.energy = 140.0, 40.0
        a.nearest, b.nearest = b, None
        a.last_motors = np.zeros(len(M), dtype=np.float32)
        b.last_motors = np.zeros(len(M), dtype=np.float32)
        a.last_motors[M["share"]] = 1.0
        a.last_motors[M["attack"]] = 0.9          # ikisi de esigin ustunde
        sim._apply_social_rules()
        self.assertEqual(sim.stats_step["share_events"] + sim.stats_step["attack_events"], 1)
        self.assertEqual(sim.stats_step["share_events"], 1, "daha buyuk marj kazanmali")

    def test_lethal_attack_is_attributed(self):
        sim, a, b, _ = self._duel(3.0, rules__attack__damage=8.0)
        self.assertLessEqual(b.energy, 0.0)
        self.assertEqual(sim.stats_step["attack_kills"], 1)
        self.assertEqual(b.death_cause, "killed")
        # Kurban bir sonraki adimda yiyerek ya da bir paylasimla toparlanmasin:
        # burada olcumuz olum MUHASEBESI, kurbanin ekolojik sansi degil.
        sim.agents = [b]
        sim.world.food[:] = 0.0
        sim.step()  # olum muhasebesi bir sonraki adimda islenir
        self.assertNotIn(b, sim.agents)
        self.assertEqual(sim.stats_step["death_killed"], 1)

    def test_stratified_correction_applies_to_attack_too(self):
        stats = {f"opp_kin_{b}": 0 for b in range(5)}
        stats.update({f"opp_non_{b}": 0 for b in range(5)})
        stats.update(opp_kin_1=400, atk_kin_1=100, opp_non_1=400, atk_non_1=300)
        self.assertAlmostEqual(stratified_kin_bias(stats, action="atk"), -0.5, places=6)


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
