"""Faz 7 testleri: cesitlilik altyapisi.

En onemlisi `test_immigration_zero_is_byte_identical` ve
`test_immigration_does_not_create_energy`: birincisi Faz 1-6'nin butun taban
cizgilerinin degismedigini (varsayilan 0.0'da hicbir rastgele cekim yok),
ikincisi gocmenin bir DOGUMUN yerine gectigini — koloniye enerji EKLEMEDIGINI
— dogrular. Faz 4.5'in dersi: enerji aktaran/yaratan her yeni kural once
enerji defterinde sinanir.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config
from sinek.metrics import lineage_stats, social_rates
from sinek.simulation import Simulation

BASE = ["viz.mode=none", "metrics.enabled=false"]


def make(steps=0, **over):
    ov = BASE + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


class TestImmigrationIsOptIn(unittest.TestCase):
    def test_default_is_off(self):
        self.assertEqual(load_config().get("evolution.immigration_rate", None), 0.0)

    def test_immigration_zero_is_byte_identical(self):
        """0.0'da hicbir rng cekimi yapilmamali: eski fazlar birebir korunur."""
        a = make(steps=250, agents__initial_count=80, seed=5)
        b = make(steps=250, agents__initial_count=80, seed=5,
                 evolution__immigration_rate=0.0)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertEqual(a.stats_total["immigrants"], 0)

    def test_immigration_changes_the_run(self):
        a = make(steps=250, agents__initial_count=80, seed=5)
        c = make(steps=250, agents__initial_count=80, seed=5,
                 evolution__immigration_rate=0.05)
        self.assertNotEqual(a.state_hash(), c.state_hash())
        self.assertGreater(c.stats_total["immigrants"], 0)

    def test_same_seed_same_result(self):
        ov = dict(agents__initial_count=80, seed=11, evolution__immigration_rate=0.05)
        self.assertEqual(make(steps=200, **ov).state_hash(),
                         make(steps=200, **ov).state_hash())


class TestImmigrationEnergyLedger(unittest.TestCase):
    def test_immigration_does_not_create_energy(self):
        """Gocmen bir DOGUMUN yerine gecer: ebeveyn ayni maliyeti oder, yavru
        ayni enerjiyle baslar. Iki kolun ureme oncesi/sonrasi enerji farki
        BIREBIR ayni olmali — aksi halde Faz 4.5'in pompasi geri gelir."""
        deltas = []
        for rate in (0.0, 1.0):
            sim = make(agents__initial_count=40, seed=9,
                       evolution__immigration_rate=rate)
            for a in sim.agents:
                a.energy = float(sim.cfg.agents.energy.max)
                a.age = int(sim.cfg.agents.reproduction.min_age) + 1
            before = sum(a.energy for a in sim.agents)
            n_before = len(sim.agents)
            sim._reproduce()
            after = sum(a.energy for a in sim.agents)
            self.assertGreater(len(sim.agents), n_before, "hic dogum yok, test bos")
            deltas.append(round(after - before, 6))
        self.assertEqual(deltas[0], deltas[1],
                         f"gocmen enerji dengesini degistirdi: {deltas}")

    def test_sharing_still_conserves_with_immigration(self):
        sim = make(steps=300, agents__initial_count=150,
                   evolution__immigration_rate=0.05,
                   rules__share__need_bonus=3.0)
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim yok")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=6)


class TestImmigrationProducesRealDiversity(unittest.TestCase):
    def test_immigrant_gets_a_brand_new_surname(self):
        sim = make(agents__initial_count=30, seed=2, evolution__immigration_rate=1.0)
        founders = {a.genome.surname for a in sim.agents}
        for a in sim.agents:
            a.energy = float(sim.cfg.agents.energy.max)
            a.age = int(sim.cfg.agents.reproduction.min_age) + 1
        sim._reproduce()
        newborns = [a for a in sim.agents if a.genome.surname not in founders]
        self.assertTrue(newborns, "gocmen yeni soyisim almamis")

    def test_immigrant_genome_is_not_the_parents_child(self):
        """Gocmenin agirliklari ebeveynden gelmemeli — etiket degil GENOM
        cesitliligi uretmesi gereken sey bu."""
        sim = make(agents__initial_count=20, seed=4, evolution__immigration_rate=1.0)
        for a in sim.agents:
            a.energy = float(sim.cfg.agents.energy.max)
            a.age = int(sim.cfg.agents.reproduction.min_age) + 1
        parents = {a.id: a for a in sim.agents}
        sim._reproduce()
        checked = 0
        for child in sim.agents:
            parent = parents.get(child.parent_id)
            if parent is None or child.id in parents:
                continue
            checked += 1
            self.assertGreater(
                float(abs(child.genome.weights - parent.genome.weights).mean()),
                1e-3, "gocmen genomu ebeveyninkiyle ayni"
            )
        self.assertGreater(checked, 0, "hic yavru incelenmedi, test bos")

    def test_immigration_raises_effective_lineages(self):
        base = make(steps=400, agents__initial_count=60, seed=8)
        imm = make(steps=400, agents__initial_count=60, seed=8,
                   evolution__immigration_rate=0.05)
        self.assertGreater(lineage_stats(imm.agents)["lineage_effective"],
                           lineage_stats(base.agents)["lineage_effective"])

    def test_immigrants_are_reported_as_a_metric(self):
        self.assertEqual(social_rates({"immigrants": 7})["immigrants"], 7)


class TestControlDeletesInformationNotMigration(unittest.TestCase):
    def test_control_keeps_immigrants_but_hides_the_label(self):
        """Karistirma kontrolu BILGIYI siler, GOCU degil: gocmen sayisi ayni
        kalmali ama etiketi yasayan populasyondan gelmeli (yeni soy acmamali).
        Aksi halde iki kol farkli sayida soyla kosar ve kiyaslanamaz."""
        sim = make(agents__initial_count=30, seed=6,
                   evolution__immigration_rate=1.0,
                   rules__kinship__control="random_surname_at_birth")
        founders = {a.genome.surname for a in sim.agents}
        for a in sim.agents:
            a.energy = float(sim.cfg.agents.energy.max)
            a.age = int(sim.cfg.agents.reproduction.min_age) + 1
        sim._reproduce()
        self.assertGreater(sim.stats_step["immigrants"], 0, "kontrolde goc durmus")
        self.assertTrue(
            {a.genome.surname for a in sim.agents} <= founders,
            "kontrol kolunda gocmen yeni soy acti — etiket bilgi tasiyor",
        )


class TestSeedIsAConfigKey(unittest.TestCase):
    def test_default_is_fresh(self):
        cfg = load_config()
        self.assertIsNone(cfg.get("run.load_genomes", None))

    def test_cli_overrides_config(self):
        import argparse
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import run as runner
        cfg = load_config(overrides=["run.load_genomes=config/yol.npz", "run.load_top=5"])
        args = argparse.Namespace(load_genomes=None, load_top=None)
        self.assertEqual(runner.resolve_seed(args, cfg), ("config/yol.npz", 5))
        args = argparse.Namespace(load_genomes="cli/yol.npz", load_top=9)
        self.assertEqual(runner.resolve_seed(args, cfg), ("cli/yol.npz", 9))

    def test_old_experiments_declare_their_own_seed(self):
        """Varsayilan TAZE'ye donunce, tohumla kurulmus eski deneyler kendi
        tohumunu dosyasinda yazmali; yoksa sessizce baska bir deneye donusur."""
        root = os.path.join(os.path.dirname(__file__), "..", "experiments")
        for name in ("faz4_taban.yaml", "faz45_ekoloji.yaml", "faz5_hafiza.yaml",
                     "faz6_secim.yaml"):
            cfg = load_config(os.path.join(root, name))
            self.assertTrue(
                cfg.get("run.load_genomes", None),
                f"{name} tohumunu ilan etmiyor (TAZE'ye duser, rejim degisir)",
            )


if __name__ == "__main__":
    unittest.main()
