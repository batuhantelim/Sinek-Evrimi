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

    def test_pool_multi_counts_real_choices(self):
        """ONKOSUL olcusu: havuzda >=2 aday olan kararlarin payi.

        Ortalama havuz buyuklugu yeterli degil — 1 ve 4 adayli kararlarin
        karisimi da 2.5 ortalama verir. Ilk partide havuz 1.35'ti ve "secim"
        diye bir sey yoktu; bu sutun onu sessiz kalmadan gosterir.
        """
        from sinek.metrics import social_rates
        stats = {"pick_events": 10, "pick_pool": 25, "pick_multi": 6}
        r = social_rates(stats)
        self.assertAlmostEqual(r["pool_size"], 2.5)
        self.assertAlmostEqual(r["pool_multi"], 0.6)

    def test_pool_multi_is_zero_when_every_pool_is_a_single_candidate(self):
        """Ajanlar birbirinden uzakken hicbir kararda ikinci aday olmamali."""
        sim = make(agents__initial_count=4, rules__partner__enabled=True)
        for i, a in enumerate(sim.agents):
            a.x, a.y = 10.0 + i * 40.0, 10.0
        sim.run(1)
        self.assertEqual(sim.stats_total["pick_multi"], 0)

    def test_fitness_has_no_choice_term(self):
        path = os.path.join(os.path.dirname(__file__), "..", "sinek", "agent.py")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        body = src.split("def fitness(")[1].split("def ")[0]
        for banned in ("pick_", "ledger", "given", "received"):
            self.assertNotIn(banned, body, f"fitness '{banned}' okuyor")


class TestParamMigration(unittest.TestCase):
    """Sozlesme buyudugunde YENI PARAMETRELER de tasinmali.

    Bu test Faz 6'da eklendi cunku tam tersi oldu: kayitli genomlarda
    `pick_*` yoktu, `mutate` mevcut anahtarlar uzerinde gezdigi icin onlar
    asla mutasyona ugramadi ve partner secimi SESSIZCE olu kaldi — secim
    kolu, secimsiz kolla birebir ayni sonuc verdi.
    """

    def test_missing_params_are_added_with_config_defaults(self):
        import tempfile

        from sinek.persistence import load_population, save_population

        sim = make(agents__initial_count=8)
        for a in sim.agents:                      # eski kayit: pick_* yok
            for name in [k for k in a.genome.params if k.startswith("pick")]:
                del a.genome.params[name]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pop.npz")
            save_population(path, sim)
            genomes, meta = load_population(path, sim.cfg)
        self.assertIn("pick_kin", genomes[0].params, "yeni parametre tasinmadi")
        self.assertEqual(genomes[0].params["pick_kin"], 0.0, "config varsayilaniyla baslamali")
        self.assertIn("new_params", meta["migrated"], "tasima SESSIZ olmamali")
        self.assertIn("pick_kin", meta["migrated"]["new_params"])

    def test_migrated_params_actually_mutate(self):
        """Tasinan parametre mutasyona girmeli; yoksa mekanik olu kalir."""
        sim = make(agents__initial_count=4)
        g = sim.agents[0].genome
        before = g.params["pick_kin"]
        moved = False
        for _ in range(400):
            child = g.child(sim.cfg, sim.rng)
            if child.params["pick_kin"] != before:
                moved = True
                break
            g = child
        self.assertTrue(moved, "pick_kin hic mutasyona ugramadi")


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_state(self):
        a = make(steps=200, rules__partner__enabled=True)
        b = make(steps=200, rules__partner__enabled=True)
        self.assertEqual(a.state_hash(), b.state_hash())


if __name__ == "__main__":
    unittest.main()


class TestExclusionProbe(unittest.TestCase):
    """Sonda OLCMELI, DEGISTIRMEMELI: `_note_pick` sarilmis haliyle koşum
    birebir ayni state_hash vermeli. Faz 3'te sonda ile simulasyon ici olcu
    ayrismisti; sonda karari etkiliyorsa o ayrisma yorumlanamaz."""

    def probe_mod(self):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "..", "tools",
                            "exclusion_probe.py")
        spec = importlib.util.spec_from_file_location("exclusion_probe", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_probe_does_not_change_the_run(self):
        mod = self.probe_mod()
        ov = list(mod.REGIME) + BASE + ["agents.initial_count=60", "seed=42"]
        plain = Simulation(load_config(overrides=ov))
        plain.run(120)

        wrapped = Simulation(load_config(overrides=ov))
        tally = mod.Tally()
        original = wrapped._note_pick
        emax = float(wrapped.physics.energy_max) if hasattr(
            wrapped.physics, "energy_max") else 100.0
        wrapped._note_pick = lambda a, pool, idx: (
            tally.note(a, pool, idx, emax), original(a, pool, idx))[1]
        wrapped.run(120)

        self.assertEqual(plain.state_hash(), wrapped.state_hash())
        self.assertGreater(tally.events, 0, "hic karar kaydedilmedi, test bos")

    def test_structural_and_individual_exclusion_are_separate(self):
        """Yapisal dislama havuz buyuklugunun zorunlu sonucudur; bireysel
        dislama davranistir. Ikisi ayni sayi degildir."""
        mod = self.probe_mod()
        tally = mod.Tally()

        class G:
            surname = 1

        class A:
            def __init__(self, i):
                self.id = i
                self.genome = G()
                self.mem_id = i
                self.energy = 50.0
                self.ledger = {}

        a = A(0)
        others = [A(1), A(2), A(3)]
        for _ in range(10):                      # her seferinde ayni adayi sec
            tally.note(a, [(o, 1.0) for o in others], 0, 100.0)
        r = tally.summary()
        self.assertAlmostEqual(r["structural"], 2.0 / 3.0, places=3)
        self.assertAlmostEqual(r["individual"], 2.0 / 3.0, places=3)
        tally2 = mod.Tally()
        for i in range(3):                       # sirayla hepsini sec
            tally2.note(a, [(o, 1.0) for o in others], i, 100.0)
        r2 = tally2.summary()
        self.assertAlmostEqual(r2["structural"], 2.0 / 3.0, places=3)
        self.assertAlmostEqual(r2["individual"], 0.0, places=3,
                               msg="hepsi bir kez secildi, bireysel dislama 0")
