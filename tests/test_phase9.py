"""Faz 9 testleri: melez soyisim (SALT ETIKET).

En onemlisi `test_hybrid_is_not_a_hardcoded_class` ve
`test_hybrid_touches_no_energy`: birincisi melezin bir sinif/kast olarak
kodlanmadigini (kaynakta melez icin ozel bir paylasim/saldiri dali yok),
ikincisi melezligin enerji defterine dokunmadigini dogrular. Uculeyin:
`test_disabled_is_byte_identical` Faz 1-8'in butun taban cizgilerinin
degismedigini sabitler.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sinek.config import load_config
from sinek.genome import Genome, kin_of
from sinek.lineage import kin_labels, label_key
from sinek.metrics import lineage_stats, social_rates, stratified_kin_bias
from sinek.simulation import Simulation

import numpy as np

BASE = ["viz.mode=none", "metrics.enabled=false"]


def make(steps=0, **over):
    ov = BASE + [f"{k.replace('__', '.')}={v}" for k, v in over.items()]
    sim = Simulation(load_config(overrides=ov))
    if steps:
        sim.run(steps)
    return sim


def g(a, b=-1):
    return Genome({}, np.zeros(0, np.float32), 0, a, b)


class TestLabelAlgebra(unittest.TestCase):
    def test_pure_labels_reduce_to_equality(self):
        """Faz 3-8 davranisi: tek bilesenli etiketlerde tam esitlik."""
        self.assertTrue(kin_labels(3, -1, 3, -1))
        self.assertFalse(kin_labels(3, -1, 4, -1))

    def test_hybrid_is_kin_to_both_parents(self):
        self.assertTrue(kin_of(g(3), g(3, 7)))
        self.assertTrue(kin_of(g(7), g(3, 7)))
        self.assertFalse(kin_of(g(9), g(3, 7)))

    def test_hybrids_sharing_a_component_are_kin(self):
        self.assertTrue(kin_of(g(3, 7), g(3, 9)))
        self.assertFalse(kin_of(g(3, 7), g(8, 9)))

    def test_kinship_is_symmetric(self):
        for x, y in [(g(3), g(3, 7)), (g(3, 7), g(9)), (g(3, 7), g(7, 3))]:
            self.assertEqual(kin_of(x, y), kin_of(y, x))

    def test_label_key_is_order_free(self):
        self.assertEqual(label_key(7, 3), label_key(3, 7))
        self.assertEqual(label_key(5, -1), (5,))


class TestHybridIsOptIn(unittest.TestCase):
    def test_default_is_off(self):
        cfg = load_config()
        self.assertFalse(cfg.get("rules.hybrid.enabled", None))
        self.assertEqual(cfg.get("rules.hybrid.rate", None), 0.0)

    def test_disabled_is_byte_identical(self):
        """rate = 0'da hicbir rng cekimi yapilmamali: Faz 1-8 korunur."""
        a = make(steps=250, agents__initial_count=120, seed=5)
        b = make(steps=250, agents__initial_count=120, seed=5,
                 rules__hybrid__enabled=True, rules__hybrid__rate=0.0)
        self.assertEqual(a.state_hash(), b.state_hash())
        self.assertEqual(a.stats_total["hybrid_births"], 0)

    def test_same_seed_same_result(self):
        ov = dict(agents__initial_count=120, seed=11,
                  rules__hybrid__enabled=True, rules__hybrid__rate=0.3)
        self.assertEqual(make(steps=200, **ov).state_hash(),
                         make(steps=200, **ov).state_hash())


class TestHybridMechanic(unittest.TestCase):
    def test_hybrids_actually_form(self):
        sim = make(steps=400, agents__initial_count=150, seed=3,
                   rules__hybrid__enabled=True, rules__hybrid__rate=0.3)
        self.assertGreater(sim.stats_total["hybrid_births"], 0)
        self.assertGreater(lineage_stats(sim.agents)["hybrid_share"], 0.0)

    def test_only_two_pure_lineages_hybridise(self):
        """Melez saf doller: etiket ASLA ikiden fazla bilesen tasimaz."""
        sim = make(steps=500, agents__initial_count=150, seed=4,
                   rules__hybrid__enabled=True, rules__hybrid__rate=0.9)
        self.assertGreater(sum(1 for a in sim.agents if a.genome.is_hybrid), 0)
        for a in sim.agents:
            self.assertLessEqual(len(a.genome.label()), 2)

    def test_hybrid_child_keeps_the_parent_genome(self):
        """MELEZLIK SALT ETIKETTIR: ikinci ebeveynin genomu cocuga GECMEZ."""
        sim = make(agents__initial_count=40, seed=9,
                   rules__hybrid__enabled=True, rules__hybrid__rate=1.0,
                   evolution__enabled=False)
        for i, a in enumerate(sim.agents):
            a.x, a.y = 30.0 + (i % 5) * 0.4, 30.0 + (i // 5) * 0.4
            a.energy = float(sim.cfg.agents.energy.max)
            a.age = int(sim.cfg.agents.reproduction.min_age) + 1
        sim.hash.build(sim.agents)
        parents = {a.id: a for a in sim.agents}
        sim._reproduce()
        checked = 0
        for child in sim.agents:
            parent = parents.get(child.parent_id)
            if parent is None or child.id in parents:
                continue
            checked += 1
            np.testing.assert_allclose(child.genome.weights, parent.genome.weights)
        self.assertGreater(checked, 0, "hic yavru incelenmedi, test bos")
        self.assertGreater(sim.stats_step["hybrid_births"], 0, "hic melez olusmadi")

    def test_hybrid_touches_no_energy(self):
        """Ikinci ebeveyn hicbir sey odemez: ureme oncesi/sonrasi enerji farki
        melezli ve melezsiz kolda BIREBIR ayni olmali (Faz 4.5 dersi)."""
        deltas = []
        for rate in (0.0, 1.0):
            sim = make(agents__initial_count=40, seed=9,
                       rules__hybrid__enabled=True, rules__hybrid__rate=rate,
                       evolution__enabled=False)
            for i, a in enumerate(sim.agents):
                a.x, a.y = 30.0 + (i % 5) * 0.4, 30.0 + (i // 5) * 0.4
                a.energy = float(sim.cfg.agents.energy.max)
                a.age = int(sim.cfg.agents.reproduction.min_age) + 1
            sim.hash.build(sim.agents)
            before = sum(x.energy for x in sim.agents)
            sim._reproduce()
            deltas.append(round(sum(x.energy for x in sim.agents) - before, 9))
        self.assertEqual(deltas[0], deltas[1], f"melez enerji dengesini oynatti: {deltas}")

    def test_sharing_still_conserves_energy(self):
        sim = make(steps=300, agents__initial_count=150,
                   rules__hybrid__enabled=True, rules__hybrid__rate=0.3,
                   rules__share__need_bonus=3.0)
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim yok")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=6)


class TestHybridIsMeasuredNotCoded(unittest.TestCase):
    def test_hybrid_is_not_a_hardcoded_class(self):
        """KURAL: melez bir sinif/kast degildir. `is_hybrid` yalnizca OLCUM
        sayaclarina girmeli — hicbir karar dalinda (paylasim esigi, saldiri
        esigi, hedef secimi) kullanilmamali."""
        path = os.path.join(os.path.dirname(__file__), "..", "sinek", "simulation.py")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        body = src.split("def _apply_social_rules(")[1].split("\n    def ")[0]
        hits = [l.strip() for l in body.splitlines() if "is_hybrid" in l]
        # Tek mesru kullanim: melezligi bir OLCUM degiskenine okumak.
        # Birden fazla okuma ya da bir `if`/`while` dali, melezi sinif haline
        # getirir — yasak olan tam olarak budur.
        self.assertEqual(len(hits), 1, f"melezlik birden fazla yerde okunmus: {hits}")
        self.assertIn("=", hits[0])
        self.assertFalse(hits[0].startswith(("if ", "elif ", "while ")),
                         f"melez bir karar dalinda kullanilmis: {hits[0]}")
        # Ve okundugu degisken yalnizca sayac/etiket besler.
        var = hits[0].split("=")[0].strip()
        for line in body.splitlines():
            if var in line and "is_hybrid" not in line:
                self.assertTrue("stats[" in line or "hcell" in line,
                                f"olcum degiskeni karara sizmis: {line.strip()}")

    def test_three_cells_are_measured(self):
        sim = make(steps=400, agents__initial_count=150, seed=3,
                   rules__hybrid__enabled=True, rules__hybrid__rate=0.3,
                   rules__share__need_bonus=3.0)
        r = social_rates(sim.stats_total)
        self.assertGreater(r["opph_pk"], 0)
        self.assertGreater(r["opph_hyb"], 0)
        self.assertGreater(r["opph_nn"], 0)
        # firsatlarin toplami, akrabalik firsatlarinin toplamiyla tutarli
        self.assertEqual(r["opph_pk"] + r["opph_hyb"],
                         int(sim.stats_total["opp_kin"]))
        self.assertEqual(r["opph_nn"], int(sim.stats_total["opp_nonkin"]))

    def test_reference_is_pure_kin_not_stranger(self):
        """`hyb_share_adj` SAF AKRABAYA karsi okunur; referansi degistirmek
        sorunun kendisini degistirir (Faz 6 dersi: secicilik referansi)."""
        stats = {f"opph_hyb_{b}": 100 for b in range(5)}
        stats.update({f"opph_pk_{b}": 100 for b in range(5)})
        stats.update({f"opph_nn_{b}": 100 for b in range(5)})
        stats.update({f"shr_hyb_{b}": 10 for b in range(5)})
        stats.update({f"shr_pk_{b}": 30 for b in range(5)})
        stats.update({f"shr_nn_{b}": 5 for b in range(5)})
        vs_pure = stratified_kin_bias(stats, "shr", group="hyb", ref="pk", opp="opph")
        vs_out = stratified_kin_bias(stats, "shr", group="hyb", ref="nn", opp="opph")
        self.assertAlmostEqual(vs_pure, -0.20, places=6)   # saf akrabadan DUSUK
        self.assertAlmostEqual(vs_out, +0.05, places=6)    # yabancidan YUKSEK


class TestShuffleControlCarriesBothComponents(unittest.TestCase):
    def test_shuffle_keeps_the_hybrid_label_intact(self):
        """Karistirma kontrolu BILGIYI siler, melezligi degil: melez sayisi
        ayni kalmali, yalnizca kimin hangi etikete sahip oldugu bozulmali."""
        sim = make(agents__initial_count=60, seed=6,
                   rules__hybrid__enabled=True, rules__hybrid__rate=0.5,
                   rules__kinship__control="shuffle_surnames")
        for a in sim.agents[:20]:
            a.genome.surname2 = (a.genome.surname + 1) % 60
        before = sorted((a.genome.surname, a.genome.surname2) for a in sim.agents)
        sim._shuffle_surnames()
        after = sorted((a.genome.surname, a.genome.surname2) for a in sim.agents)
        self.assertEqual(before, after, "karistirma etiket dagilimini degistirdi")
        self.assertEqual(sum(1 for a in sim.agents if a.genome.is_hybrid), 20)


if __name__ == "__main__":
    unittest.main()
