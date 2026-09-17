"""Faz 8 testleri: yogunluga bagli secilim (negatif frekans bagimliligi).

En onemlisi `test_crowding_is_lineage_blind` ve
`test_crowding_only_destroys_energy`: birincisi hicbir soyun ADIYLA
hedeflenmedigini (butun etiketler yeniden adlandirilsa ceza birebir ayni),
ikincisi cezanin bir GIDER oldugunu — enerji yaratmadigini — dogrular.
Faz 4.5'in dersi: enerji dengesine dokunan her yeni kural once defterde
sinanir.
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


class TestCrowdingIsOptIn(unittest.TestCase):
    def test_default_is_off(self):
        cfg = load_config()
        self.assertFalse(cfg.get("rules.crowding.enabled", None))
        self.assertEqual(cfg.get("rules.crowding.cost", None), 0.0)

    def test_zero_cost_is_byte_identical(self):
        """cost = 0'da hicbir enerji hareketi olmamali: eski fazlar korunur."""
        a = make(steps=250, agents__initial_count=100, seed=5)
        b = make(steps=250, agents__initial_count=100, seed=5,
                 rules__crowding__enabled=True, rules__crowding__cost=0.0)
        self.assertEqual(a.state_hash(), b.state_hash())

    def test_unknown_control_fails_loudly(self):
        with self.assertRaises(ValueError):
            make(rules__crowding__control="sihirli")

    def test_same_seed_same_result(self):
        ov = dict(agents__initial_count=100, seed=11,
                  rules__crowding__enabled=True, rules__crowding__cost=0.05)
        self.assertEqual(make(steps=200, **ov).state_hash(),
                         make(steps=200, **ov).state_hash())


class TestCrowdingIsAnEnvironmentRule(unittest.TestCase):
    def cluster(self, labels):
        """Hepsi ayni noktada duran ajanlar; etiketleri disaridan verilir."""
        sim = make(agents__initial_count=len(labels), seed=2,
                   rules__crowding__enabled=True, rules__crowding__cost=1.0)
        for a, lab in zip(sim.agents, labels):
            a.x, a.y = 40.0, 40.0
            a.energy = 100.0
            a.crowd_label = lab
        sim.hash.build(sim.agents)
        return sim

    def test_crowding_is_lineage_blind(self):
        """Butun etiketler tutarli bicimde YENIDEN ADLANDIRILSA ceza dagilimi
        birebir ayni kalmali. Aksi halde belirli bir soyu hedeflemis oluruz —
        Faz 3'un 1. kurali (rol/kast kodlanmaz) ihlal edilir."""
        labels = [7, 7, 7, 3, 3, 91]
        renamed = [100 + x for x in labels]      # bijeksiyon: 7->107, 3->103...
        a = self.cluster(labels)
        b = self.cluster(renamed)
        a._apply_crowding_cost()
        b._apply_crowding_cost()
        self.assertEqual([round(x.energy, 9) for x in a.agents],
                         [round(x.energy, 9) for x in b.agents])
        self.assertGreater(a.stats_step["crowding_drain"], 0.0, "hic ceza yok, test bos")

    def test_rare_label_pays_less(self):
        """Nadir olan ucuz yasar — mekanizmanin tanimi bu."""
        sim = self.cluster([7, 7, 7, 7, 91])
        sim._apply_crowding_cost()
        cok, nadir = sim.agents[0], sim.agents[4]
        self.assertAlmostEqual(100.0 - cok.energy, 3.0)    # 3 ayni etiketli komsu
        self.assertAlmostEqual(100.0 - nadir.energy, 0.0)  # tek basina

    def test_crowding_only_destroys_energy(self):
        """GIDER: toplam enerji tam olarak `crowding_drain` kadar DUSMELI."""
        sim = self.cluster([7, 7, 7, 3, 3, 91])
        before = sum(a.energy for a in sim.agents)
        sim._apply_crowding_cost()
        after = sum(a.energy for a in sim.agents)
        self.assertAlmostEqual(before - after, sim.stats_step["crowding_drain"], places=9)
        self.assertGreater(sim.stats_step["crowding_drain"], 0.0)

    def test_sharing_conservation_is_untouched(self):
        """Kalabalik cezasi bir GIDER; paylasimin korunum sayacina dokunmamali."""
        sim = make(steps=300, agents__initial_count=150,
                   rules__crowding__enabled=True, rules__crowding__cost=0.05,
                   rules__share__need_bonus=3.0)
        self.assertGreater(sim.stats_total["share_events"], 0, "hic paylasim yok")
        self.assertAlmostEqual(sim.stats_total["energy_created"], 0.0, places=6)
        self.assertGreater(sim.stats_total["crowding_drain"], 0.0)

    def test_drain_is_reported_as_a_metric(self):
        self.assertAlmostEqual(
            social_rates({"crowding_drain": 12.5})["crowding_drain"], 12.5
        )


class TestShuffledControl(unittest.TestCase):
    def test_control_shuffles_the_penalty_label_not_the_surname(self):
        """KONTROL bilgiyi siler, OLCUMU degil: `genome.surname` degismemeli —
        soy cesitliligi ve in/out oranlari onu okuyor."""
        sim = make(agents__initial_count=60, seed=4,
                   rules__crowding__enabled=True, rules__crowding__cost=0.05,
                   rules__crowding__control="shuffled")
        soyisimler = [a.genome.surname for a in sim.agents]
        sim._shuffle_crowd_labels()
        self.assertEqual([a.genome.surname for a in sim.agents], soyisimler,
                         "kontrol soyisimleri bozdu — olcum okunamaz hale gelir")
        # Faz 9'dan beri `crowd_label` bir ETIKET DEMETI (melez iki bilesenli).
        self.assertEqual(sorted(a.crowd_label for a in sim.agents),
                         sorted((x,) for x in soyisimler),
                         "etiket cokluk dagilimi korunmali (ornek degil bilgi silinir)")

    def test_control_still_pays_the_same_kind_of_cost(self):
        """Kontrol kolu da ceza odemeli; yoksa iki kol 'bilgi' degil 'gider'
        bakimindan ayrisir ve kiyaslanamaz."""
        sim = make(steps=250, agents__initial_count=150, seed=6,
                   rules__crowding__enabled=True, rules__crowding__cost=0.05,
                   rules__crowding__control="shuffled")
        self.assertGreater(sim.stats_total["crowding_drain"], 0.0)


class TestCrowdingActuallyProtectsLabels(unittest.TestCase):
    def test_short_run_raises_effective_lineages(self):
        """Mekanigin YONU dogru mu (kanit degil — asil olcum 12000 adimda)."""
        base = make(steps=400, agents__initial_count=120, seed=8)
        lev = make(steps=400, agents__initial_count=120, seed=8,
                   rules__crowding__enabled=True, rules__crowding__cost=0.05)
        self.assertGreater(lineage_stats(lev.agents)["lineage_effective"],
                           lineage_stats(base.agents)["lineage_effective"])


if __name__ == "__main__":
    unittest.main()
