"""Faz 1 davranis testleri: klonluk, algi-motor dongusu, kaynak muhasebesi."""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.agent import MOTOR_NAMES, SENSOR_NAMES
from sinek.config import load_config
from sinek.metrics import behavior_diversity
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]


def make(steps=0, **over):
    ov = BASE + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


class TestPhase1(unittest.TestCase):
    def test_clones_are_identical(self):
        """Faz 1: mutasyon kapali -> davranis cesitliligi tam olarak 0."""
        sim = make(steps=150, agents__initial_count=60)
        self.assertGreater(sim.population, 0)
        self.assertEqual(behavior_diversity(sim.agents), 0.0)
        first = sim.agents[0].genome.params
        for a in sim.agents:
            self.assertEqual(a.genome.params, first)

    def test_identical_sensors_give_identical_motors(self):
        """Klon beyinler ayni girdide ayni cikti verir (gurultu disinda)."""
        sim = make(agents__initial_count=4, genome__params__wander=0.0)
        sensors = np.zeros(len(SENSOR_NAMES), dtype=np.float32)
        sensors[SENSOR_NAMES.index("bias")] = 1.0
        sensors[SENSOR_NAMES.index("food_left")] = 0.8
        sensors[SENSOR_NAMES.index("food_strength")] = 1.0
        outs = [
            a.brain.act(sensors, np.random.default_rng(0)) for a in sim.agents
        ]
        for o in outs[1:]:
            np.testing.assert_allclose(o, outs[0])
        self.assertEqual(len(outs[0]), len(MOTOR_NAMES))

    def test_agents_beat_random_walkers(self):
        """Algi-motor dongusu ise yariyor mu?

        Tam kor kontrol grubuyla ayni dunyada karsilastir: yemek kokusuna gore
        yon bulma VE yemek uzerinde yavaslama kapali. Koklayan sinekler
        belirgin sekilde daha cok beslenmeli.
        """
        common = dict(
            agents__initial_count=100,
            agents__reproduction__enabled=False,
            agents__energy__max=1e9,
            agents__lifespan=100000,
        )
        blind_params = dict(
            genome__params__food_attraction=0.0,
            genome__params__hunger_gain=0.0,
            genome__params__graze_slowdown=0.0,
            genome__params__hunger_speed=0.0,
        )
        smart = make(steps=300, **common)
        blind = make(steps=300, **common, **blind_params)
        smart_food = float(np.mean([a.food_eaten for a in smart.agents]))
        blind_food = float(np.mean([a.food_eaten for a in blind.agents]))
        self.assertGreater(
            smart_food, blind_food * 1.10, f"koklayan {smart_food:.2f} vs kor {blind_food:.2f}"
        )

    def test_gradient_sensor_is_informative(self):
        """food_strength sensoru olu olmamali ve sinekler gradyanla hizalanmali."""
        sim = make(steps=120, agents__initial_count=100)
        sensors = np.array([a.sense(sim.world, sim.cfg) for a in sim.agents])
        strength = sensors[:, SENSOR_NAMES.index("food_strength")]
        fwd = sensors[:, SENSOR_NAMES.index("food_fwd")]
        self.assertGreater(strength.mean(), 0.05, "koku sinyali fiilen sifir")
        # +1 = tam gradyan yonunde, 0 = rastgele yonelim
        self.assertGreater(fwd.mean(), 0.3, f"gradyanla hizalanma zayif: {fwd.mean():.2f}")

    def test_hazard_avoidance_reduces_exposure(self):
        """Tehlikeden kacinma parametresi gercekten hasari azaltiyor mu?"""
        def exposure(avoid):
            sim = make(
                agents__initial_count=120,
                agents__reproduction__enabled=False,
                world__hazard__count=10,
                world__hazard__damage=0.0,   # olmesinler, sadece maruziyeti say
                genome__params__hazard_avoidance=avoid,
            )
            hits = 0
            for _ in range(200):
                sim.step()
                hits += sum(
                    1 for a in sim.agents if sim.world.hazard_near_field[sim.world.cell(a.x, a.y)[1], sim.world.cell(a.x, a.y)[0]] > 0.9
                )
            return hits

        self.assertLess(exposure(2.5), exposure(0.0))

    def test_food_is_conserved(self):
        """Yemek muhasebesi: yenen + kalan <= baslangic + yenilenen."""
        sim = make(agents__initial_count=50)
        start = sim.world.food_total
        regrown = 0.0
        for _ in range(100):
            before = sim.world.food_total
            sim.world.step()
            regrown += sim.world.food_total - before
            sim.world.update_food_perception()
            sim.world.update_crowd_perception(
                np.array([a.x for a in sim.agents], dtype=np.float32),
                np.array([a.y for a in sim.agents], dtype=np.float32),
            )
            for a in sim.agents:
                a.apply_motors(a.brain.act(a.sense(sim.world, sim.cfg), sim.rng), sim.world, sim.cfg)
        eaten = sim.world.food_consumed_total
        self.assertGreater(eaten, 0.0)
        self.assertAlmostEqual(sim.world.food_total, start + regrown - eaten, delta=1e-2)
        self.assertTrue(np.all(sim.world.food >= -1e-6))
        self.assertTrue(np.all(sim.world.food <= sim.world.food_capacity + 1e-4))

    def test_toroidal_wrapping(self):
        sim = make(world__toroidal=True)
        w = sim.world
        x, y = w.move(w.width - 0.5, 0.5, 1.0, -1.0)
        self.assertAlmostEqual(x, 0.5)
        self.assertAlmostEqual(y, w.height - 0.5)
        dx, dy = w.delta(1.0, 1.0, w.width - 1.0, 1.0)
        self.assertAlmostEqual(dx, -2.0)

    def test_phase3_rules_are_explicitly_unimplemented(self):
        """Faz 3 kurallari acilirsa sessizce yok sayilmamali, hata vermeli."""
        sim = make(rules__share__enabled=True)
        with self.assertRaises(NotImplementedError):
            sim.step()


class TestRendering(unittest.TestCase):
    def test_frame_shape_and_png_roundtrip(self):
        import tempfile
        from sinek.pngwrite import write_png
        from sinek.render import frame_size, render

        sim = make(steps=5, agents__initial_count=20, viz__scale=3)
        img = render(sim)
        w, h = frame_size(sim.cfg)
        self.assertEqual(img.shape, (h, w, 3))
        self.assertEqual(img.dtype, np.uint8)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.png")
            write_png(p, img)
            with open(p, "rb") as fh:
                self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")
            self.assertGreater(os.path.getsize(p), 100)


if __name__ == "__main__":
    unittest.main()
