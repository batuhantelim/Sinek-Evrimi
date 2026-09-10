"""Faz 2 testleri: mutasyon, evrimlesebilir sinir agi, secilim.

Kritik test `test_selection_beats_drift`: fitness'a gore secilim yapan koloni,
rastgele secilim yapan (surukleneN) kontrol grubunu gercekten geciyor mu?
Gecmiyorsa gordugumuz sey evrim degil, gurultudur.
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import N_MOTORS, N_SENSORS
from sinek.brains import genome_size_for, make_brain
from sinek.config import load_config
from sinek.genome import founder_genome
from sinek.metrics import behavior_diversity, weight_diversity
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]
DRIFT = [  # secilim baskisini tamamen kaldirir: turnuva rastgele ebeveyn secer
    "evolution.fitness.age=0.0",
    "evolution.fitness.children=0.0",
    "evolution.fitness.food_eaten=0.0",
    "evolution.fitness.energy=0.0",
    "evolution.fitness.distance=0.0",
    "evolution.elite_count=0",
]


def make(steps=0, extra=(), **over):
    ov = BASE + list(extra) + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


class TestRNNBrain(unittest.TestCase):
    def test_genome_size_matches_backend(self):
        cfg = load_config(overrides=["brain.type=rnn", "brain.hidden=9"])
        g = founder_genome(cfg, np.random.default_rng(0))
        self.assertEqual(g.weights.size, genome_size_for(cfg))
        brain = make_brain(cfg, g)  # uyusmazlik olsaydi patlardi
        out = brain.act(np.zeros(N_SENSORS, dtype=np.float32), np.random.default_rng(0))
        self.assertEqual(out.shape, (N_MOTORS,))

    def test_wrong_genome_size_is_rejected(self):
        """Sessizce yanlis calismaktansa yuksek sesle patlamali."""
        cfg = load_config(overrides=["brain.type=rnn", "brain.hidden=9"])
        g = founder_genome(cfg, np.random.default_rng(0))
        cfg.set("brain.hidden", 12)  # genom eski boyutta kaldi
        with self.assertRaises(ValueError):
            make_brain(cfg, g)

    def test_motor_ranges(self):
        cfg = load_config(overrides=["brain.type=rnn"])
        rng = np.random.default_rng(1)
        brain = make_brain(cfg, founder_genome(cfg, rng))
        for _ in range(50):
            out = brain.act(rng.normal(0, 1, N_SENSORS).astype(np.float32), rng)
            self.assertTrue(-1.0 <= out[0] <= 1.0)        # turn
            self.assertTrue(0.0 <= out[1] <= 1.0)         # thrust
            self.assertTrue(0.0 <= out[2] <= 1.0)         # eat
            self.assertTrue(-1.0 <= out[3] <= 1.0)        # social

    def test_declares_which_params_it_reads(self):
        """rnn davranisini agirliklardan alir; okunmayan parametreler notr.

        Bunu bildirmek zorunlu: aksi halde raporlar notr suruklenmeyi
        'evrimlesti' diye gosterir.
        """
        from sinek.brains import brain_class

        cfg = load_config(overrides=["brain.type=rnn"])
        self.assertEqual(brain_class(cfg).uses_params, ("wander",))
        cfg.set("brain.type", "reflex")
        self.assertIsNone(brain_class(cfg).uses_params, "reflex tum parametreleri okur")

    def test_unread_params_do_not_change_behaviour(self):
        """rnn beyninde okunmayan bir parametreyi degistirmek ciktiyi degistirmemeli."""
        cfg = load_config(overrides=["brain.type=rnn", "brain.noise=0.0"])
        rng = np.random.default_rng(7)
        g = founder_genome(cfg, rng)
        s = np.ones(N_SENSORS, dtype=np.float32) * 0.3

        base = make_brain(cfg, g).act(s, rng).copy()
        g2 = g.copy()
        g2.params["food_attraction"] = 99.0
        g2.params["crowd_bias"] = -5.0
        self.assertTrue(np.allclose(make_brain(cfg, g2).act(s, rng), base))

    def test_recurrent_state_is_memory(self):
        """Ayni girdi, farkli ic durum -> farkli cikti. reset() geri almali."""
        cfg = load_config(overrides=["brain.type=rnn", "brain.noise=0.0"])
        rng = np.random.default_rng(2)
        brain = make_brain(cfg, founder_genome(cfg, rng))
        s = np.ones(N_SENSORS, dtype=np.float32) * 0.5

        first = brain.act(s, rng).copy()
        for _ in range(5):
            brain.act(s, rng)
        later = brain.act(s, rng).copy()
        self.assertFalse(np.allclose(first, later), "recurrent durum bir sey tasimiyor")

        brain.reset()
        self.assertTrue(np.allclose(brain.act(s, rng), first))


class TestMutation(unittest.TestCase):
    def test_mutation_off_keeps_clones(self):
        sim = make(
            steps=400,
            extra=["evolution.enabled=false", "evolution.founder_spread=0.0"],
            evolution__generation_length=100,
        )
        self.assertEqual(behavior_diversity(sim.agents), 0.0)
        self.assertEqual(weight_diversity(sim.agents), 0.0)

    def test_mutation_on_creates_diversity(self):
        sim = make(steps=400, evolution__generation_length=100)
        self.assertGreater(weight_diversity(sim.agents), 0.0)
        self.assertGreater(behavior_diversity(sim.agents), 0.0)

    def test_mutation_respects_bounds(self):
        cfg = load_config(overrides=["evolution.mutation_rate=1.0", "evolution.mutation_sigma=5.0"])
        rng = np.random.default_rng(3)
        g = founder_genome(cfg, rng)
        for _ in range(60):
            g.mutate(cfg, rng)
        bounds = cfg.get("evolution.param_bounds").to_dict()
        for name, value in g.params.items():
            lo, hi = bounds[name]
            self.assertGreaterEqual(value, lo, name)
            self.assertLessEqual(value, hi, name)
        limit = float(cfg.get("evolution.weight_clip"))
        self.assertLessEqual(float(np.abs(g.weights).max()), limit + 1e-6)


class TestSelection(unittest.TestCase):
    def test_generation_loop_resets_population(self):
        gl = 60
        sim = make(steps=gl * 3, evolution__generation_length=gl, agents__initial_count=40)
        self.assertEqual(sim.generation, 3)
        self.assertEqual(len(sim.generation_rows), 3)
        self.assertEqual(sim.population, 40)
        self.assertEqual(sim.graveyard, [])
        # secilim havuzu yasayanlar + olenler olmali, yani nesildeki herkes
        self.assertEqual(sim.generation_rows[0]["pool"], 40)

    def test_reproduction_is_disabled_in_generational_mode(self):
        """Iki secilim mekanizmasi ayni anda calismamali."""
        sim = make(agents__reproduction__enabled=True)
        self.assertFalse(sim._repro_enabled)
        steady = make(extra=["evolution.mode=steady_state"], agents__reproduction__enabled=True)
        self.assertTrue(steady._repro_enabled)

    def _carried_genomes(self, elite_count: int) -> int:
        """Nesil sinirini asarken DEGISMEDEN gecen genom sayisi."""
        gl, n = 60, 40
        sim = make(
            evolution__generation_length=gl,
            evolution__elite_count=elite_count,
            agents__initial_count=n,
        )
        for _ in range(gl - 1):
            sim.step()
        before = [a.genome.weights.copy() for a in sim.agents + sim.graveyard]
        sim.step()  # nesil siniri: secilim burada calisir
        self.assertEqual(sim.generation, 1)
        return sum(
            1
            for a in sim.agents
            if any(np.array_equal(a.genome.weights, w) for w in before)
        )

    def test_elites_pass_unmutated(self):
        """Elitizm kazanimi korur: en iyi N genom mutasyona ugramadan gecer."""
        self.assertGreaterEqual(self._carried_genomes(elite_count=3), 3)

    def test_without_elitism_every_genome_mutates(self):
        self.assertEqual(self._carried_genomes(elite_count=0), 0)

    def test_fitness_weights_come_from_config(self):
        sim = make(
            extra=[
                "evolution.fitness.age=2.0",
                "evolution.fitness.food_eaten=0.0",
                "evolution.fitness.children=0.0",
                "evolution.fitness.energy=0.0",
                "evolution.fitness.distance=0.0",
            ]
        )
        a = sim.agents[0]
        a.age, a.food_eaten = 10, 100.0
        self.assertAlmostEqual(a.fitness(sim.fitness_weights), 20.0)

    def test_selection_improves_fitness(self):
        sim = make(steps=250 * 8)
        f = [g["mean_fitness"] for g in sim.generation_rows]
        self.assertGreaterEqual(len(f), 6)
        early = np.mean(f[:2])
        late = np.mean(f[-2:])
        self.assertGreater(late, early * 1.3, f"fitness artmadi: {early:.0f} -> {late:.0f}")

    def test_selection_beats_drift(self):
        """Asil sinav: secilim, rastgele suruklenmeden gercekten iyi mi?"""
        steps = 250 * 8
        evolved = make(steps=steps)
        drifted = make(steps=steps, extra=DRIFT)
        e = evolved.generation_rows[-1]["mean_food_eaten"]
        d = drifted.generation_rows[-1]["mean_food_eaten"]
        self.assertGreater(e, d * 1.5, f"secilim {e:.1f} vs suruklenme {d:.1f}")


class TestPersistence(unittest.TestCase):
    def test_save_load_roundtrip_and_seeding(self):
        import tempfile

        from sinek.persistence import load_population, save_population

        sim = make(steps=60, agents__initial_count=20)
        with tempfile.TemporaryDirectory() as d:
            path = save_population(os.path.join(d, "pop.npz"), sim, note="test")
            cfg = load_config(overrides=BASE + ["agents.initial_count=20"])
            genomes, meta = load_population(path, cfg)

            self.assertEqual(len(genomes), sim.population)
            self.assertEqual(meta["brain_type"], "rnn")
            # fitness'a gore sirali donmeli (en iyi basta)
            fits = sorted((a.fitness(sim.fitness_weights) for a in sim.agents), reverse=True)
            self.assertAlmostEqual(fits[0], max(fits))

            saved = {tuple(np.round(a.genome.weights, 6)) for a in sim.agents}
            self.assertEqual({tuple(np.round(g.weights, 6)) for g in genomes}, saved)

            # tohumlanan simulasyon genomlari aynen almali
            seeded = Simulation(cfg, initial_genomes=genomes)
            self.assertTrue(
                np.array_equal(seeded.agents[0].genome.weights, genomes[0].weights)
            )

    def test_load_rejects_mismatched_brain(self):
        import tempfile

        from sinek.persistence import load_population, save_population

        sim = make(steps=20, agents__initial_count=10)
        with tempfile.TemporaryDirectory() as d:
            path = save_population(os.path.join(d, "pop.npz"), sim)
            with self.assertRaises(ValueError):
                load_population(path, load_config(overrides=["brain.type=reflex"]))
            with self.assertRaises(ValueError):
                load_population(path, load_config(overrides=["brain.hidden=20"]))


if __name__ == "__main__":
    unittest.main()
