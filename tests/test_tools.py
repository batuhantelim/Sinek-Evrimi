"""Arac testleri.

En onemlisi `test_seed_sweep_regime_matches_step2`: cok-seed taramasinin
iddiasi "hicbir mekanik degismiyor, SADECE seed degisiyor". Bu ancak
taramadaki rejim, adim 2'nin deney dosyasiyla birebir ayniysa dogrudur —
biri elle degistirilip digeri unutulursa tekrarlanabilirlik iddiasi coker.
"""

import os
import sys
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from sinek.config import load_config  # noqa: E402

import basin_map  # noqa: E402
import env_sweep  # noqa: E402
import predator_sweep  # noqa: E402
import seed_sweep  # noqa: E402

# Taramanin bilerek farkli tuttugu, mekanigi etkilemeyen dallar.
IGNORED_BRANCHES = ("run", "viz", "metrics", "seed")


def _mechanics(cfg_dict: dict) -> dict:
    return {k: v for k, v in cfg_dict.items() if k not in IGNORED_BRANCHES}


class TestSeedSweepRegime(unittest.TestCase):
    def test_seed_sweep_regime_matches_step2(self):
        from_sweep = load_config(overrides=seed_sweep.FIXED + seed_sweep.REGIME).to_dict()
        from_file = load_config(
            os.path.join(ROOT, "experiments", "faz3b_saldiri.yaml")
        ).to_dict()
        self.assertEqual(
            _mechanics(from_sweep),
            _mechanics(from_file),
            "tarama rejimi ile adim 2 deney dosyasi ayrismis: "
            "'sadece seed degisiyor' iddiasi gecersiz",
        )

    def test_control_only_adds_shuffle(self):
        base = load_config(overrides=seed_sweep.FIXED + seed_sweep.REGIME).to_dict()
        ctrl = load_config(
            overrides=seed_sweep.FIXED
            + seed_sweep.REGIME
            + ["rules.kinship.control=shuffle_surnames"]
        ).to_dict()
        self.assertEqual(ctrl["rules"]["kinship"]["control"], "shuffle_surnames")
        base["rules"]["kinship"]["control"] = "shuffle_surnames"
        self.assertEqual(base, ctrl, "kontrol kosumu rejimde baska bir sey de degistirmis")


class TestEnvSweepStaysEnvironmental(unittest.TestCase):
    """Cevresel taramanin iddiasi: 'yeni davranis mekanigi yok, sadece dunya
    parametreleri degisiyor'. Bir kosula yanlislikla fitness ya da odeme
    parametresi sizarsa bu iddia coker ve sonuc yorumlanamaz hale gelir."""

    #: Kosullarin dokunmasina izin verilen tek dallar.
    ALLOWED_PREFIXES = (
        "world.food.",          # kaynak bollugu/kitligi
        "agents.motors.",       # karisma (hiz, donus)
        "agents.reproduction.spawn_radius",   # yavrunun ne kadar uzaga dogdugu
        "rules.kinship.split_rate",           # soy sayisi
    )
    #: Hicbir kosulun dokunmamasi gerekenler — bunlar DAVRANIS odemeleridir.
    FORBIDDEN_PREFIXES = (
        "evolution.fitness",
        "rules.share.",
        "rules.attack.",
        "rules.kinship.control",
        "brain.",
    )

    def test_conditions_only_touch_world_parameters(self):
        for name, overrides in env_sweep.CONDITIONS.items():
            for item in overrides:
                key = item.split("=", 1)[0]
                self.assertFalse(
                    key.startswith(self.FORBIDDEN_PREFIXES),
                    f"{name}: '{key}' bir davranis/odeme parametresi — cevresel tarama "
                    "bunu degistiremez",
                )
                self.assertTrue(
                    key.startswith(self.ALLOWED_PREFIXES),
                    f"{name}: '{key}' izinli cevresel dallarin disinda",
                )

    def test_base_regime_is_the_step2_regime(self):
        self.assertEqual(env_sweep.REGIME, seed_sweep.REGIME)
        self.assertEqual(env_sweep.FIXED, seed_sweep.FIXED)

    def test_axis_levers_are_distinct(self):
        """A1 mekansal yapiya, A2 soy bolunmesine dokunmamali; yoksa iki
        eksen ayni seyi olcer ve ayristirma imkansizlasir."""
        a1_keys = {i.split("=")[0] for name in env_sweep.A1 for i in env_sweep.A1[name]}
        a2_keys = {i.split("=")[0] for name in env_sweep.A2 for i in env_sweep.A2[name]}
        self.assertTrue(a1_keys <= {"rules.kinship.split_rate"}, a1_keys)
        self.assertTrue(
            a2_keys <= {"agents.motors.max_speed", "agents.reproduction.spawn_radius"}, a2_keys
        )
        self.assertEqual(a1_keys & a2_keys, set(), "iki alt-kaldirac ayni anahtari oynatiyor")


class TestHostilityClassifier(unittest.TestCase):
    """D (dusmanlik) / C (caresizlik) ayrimi.

    Bu ayrim yapilmadan "kitlik dusmanlik uretir" YAZILAMAZ: kitlikta artan
    saldiri, korlemesine bir aclik davranisi da olabilir. Siniflandirici
    yaniltici bir 'D' vermemeli.
    """

    def case(self, **kw):
        base = dict(
            hostility=0.10, q_attack_in_group=0.02, q_attack_out_group=0.06,
            attack_t=-8.0, pop_start=700.0, pop_end=690.0,
        )
        base.update(kw)
        return env_sweep.classify_hostility(base)

    def test_targeted_hostility_with_healthy_colony_is_D(self):
        kind, _why = self.case()
        self.assertEqual(kind, "D")

    def test_blind_attack_on_everyone_is_not_hostility(self):
        kind, _why = self.case(q_attack_in_group=0.28, q_attack_out_group=0.30, hostility=0.30)
        self.assertEqual(kind, "C", "in ve out birlikte yuksekken 'dusmanlik' denemez")

    def test_colony_collapse_is_desperation_even_if_targeted(self):
        """Cokusteki bir kolonide hedefli gorunen saldiri caresizliktir."""
        kind, why = self.case(pop_end=258.0, hostility=0.77, q_attack_out_group=0.80)
        self.assertEqual(kind, "C")
        self.assertIn("cokus", why)

    def test_no_elevation_means_question_does_not_arise(self):
        kind, _why = self.case(hostility=0.045, attack_t=+0.9)
        self.assertEqual(kind, "artmadi")

    def test_level_and_direction_are_reported_separately(self):
        """Saldiri artmamis olsa bile YON bilgisi gizlenmemeli.

        B_bol'da saldiri tabanin altinda (%2.0) ama dis/ic orani 3x ve
        atk_t -13.3 idi: seviye sorusu 'artmadi' der, yon sorusu 'yabanciya'.
        Gerekce metni ikisini de icermeli.
        """
        kind, why = self.case(
            hostility=0.0198, q_attack_in_group=0.0103, q_attack_out_group=0.0305,
            attack_t=-13.27,
        )
        self.assertEqual(kind, "artmadi")
        self.assertIn("YON", why)
        self.assertIn("2.96x", why)

    def test_collapse_check_precedes_targeting(self):
        """Sira onemli: cokus kontrolu hedeflilik kontrolunden ONCE gelmeli,
        yoksa cokmekte olan koloniler yanlislikla 'D' etiketlenir."""
        kind, _ = self.case(pop_end=100.0)   # hedefli gorunuyor ama cokmus
        self.assertEqual(kind, "C")


class TestPredatorArms(unittest.TestCase):
    """Faz 4 taramasinin iddiasi: 'kollar arasindaki TEK fark avcidir'.
    Rejim ile deney dosyalari ayrisirsa bu iddia coker."""

    ARMS = {"avci": "faz4_avci.yaml", "avcisiz": "faz4_avcisiz.yaml"}

    def _cfg(self, extra):
        return load_config(overrides=seed_sweep.FIXED + seed_sweep.REGIME + extra).to_dict()

    def test_arms_match_experiment_files(self):
        for arm, fname in self.ARMS.items():
            with self.subTest(arm=arm):
                from_sweep = self._cfg(predator_sweep.ARMS[arm])
                from_file = load_config(os.path.join(ROOT, "experiments", fname)).to_dict()
                self.assertEqual(
                    _mechanics(from_sweep),
                    _mechanics(from_file),
                    f"{arm} kolu ile {fname} ayrismis: 'tek fark avci' iddiasi gecersiz",
                )

    def test_arms_differ_only_in_the_predator_switch(self):
        a = self._cfg(predator_sweep.ARMS["avci"])
        b = self._cfg(predator_sweep.ARMS["avcisiz"])
        self.assertNotEqual(a["rules"]["predator"], b["rules"]["predator"])
        a["rules"]["predator"]["enabled"] = b["rules"]["predator"]["enabled"]
        self.assertEqual(a, b, "kollar avci disinda bir sey de degistirmis")

    def test_phase3_regime_keeps_the_predator_off(self):
        """config.yaml varsayilani Faz 4'e ilerledi; Faz 3 taramasi sessizce
        baska bir deneye donusmemeli."""
        self.assertFalse(self._cfg([])["rules"]["predator"]["enabled"])


class TestPredatorHostilityClassifier(unittest.TestCase):
    """Eksen B disiplini avci altinda da gecerli: saldiri SEVIYESI ile YONU
    ayri okunur, cokus hedeflilikten ONCE kontrol edilir."""

    def case(self, **over):
        pred = dict(
            hostility=0.12, q_attack_in_group=0.05, q_attack_out_group=0.15,
            attack_t=-6.0, population=600.0,
        )
        base = dict(hostility=0.0442, population=650.0)
        pred.update({k: v for k, v in over.items() if k in pred})
        base.update({k[5:]: v for k, v in over.items() if k.startswith("base_")})
        return predator_sweep.classify(pred, base)

    def test_healthy_and_targeted_is_hostility(self):
        kind, why = self.case()
        self.assertEqual(kind, "D")
        self.assertIn("YABANCIYA", why)

    def test_collapse_check_precedes_targeting(self):
        kind, why = self.case(population=300.0)   # hedefli ama koloni erimis
        self.assertEqual(kind, "C")
        self.assertIn("cokus", why)

    def test_blind_increase_is_not_hostility(self):
        kind, _ = self.case(attack_t=-0.3)
        self.assertEqual(kind, "C")

    def test_level_and_direction_are_reported_separately(self):
        """Saldiri artmadiysa D/C sorusu dusmez — ama YON yine de yazilir."""
        kind, why = self.case(hostility=0.03, q_attack_in_group=0.01,
                              q_attack_out_group=0.05, attack_t=-9.0)
        self.assertEqual(kind, "artmadi")
        self.assertIn("YON", why)
        self.assertIn("5.00x", why)


class TestBasinMap(unittest.TestCase):
    """Havza haritalamanin iddiasi: 'avci kapali, rejim Faz 3/4 ile ayni,
    yalnizca seed degisiyor'. Rejim deney dosyasindan ayrisirsa tani baska bir
    deneyi olcer."""

    def test_regime_matches_the_predator_free_arm(self):
        from_tool = load_config(
            overrides=seed_sweep.FIXED + seed_sweep.REGIME + [basin_map.PREDATOR_OFF]
        ).to_dict()
        from_file = load_config(
            os.path.join(ROOT, "experiments", "faz4_avcisiz.yaml")
        ).to_dict()
        self.assertEqual(_mechanics(from_tool), _mechanics(from_file))

    def test_new_base_changes_only_the_starting_population(self):
        """Faz 4 tabaninin iddiasi: 'hicbir odeme parametresi degismedi, yalnizca
        tohum populasyonu degisti'. Rejim avcisiz koldan ayrisirsa bu iddia coker
        ve taban gizlice yeni bir deney olur."""
        taban = load_config(os.path.join(ROOT, "experiments", "faz4_taban.yaml")).to_dict()
        avcisiz = load_config(os.path.join(ROOT, "experiments", "faz4_avcisiz.yaml")).to_dict()
        self.assertEqual(_mechanics(taban), _mechanics(avcisiz))

    def test_phase45_ecology_only_changes_cap_and_conservation(self):
        """Faz 4.5'in iddiasi: 'yemek arzi degismedi, yalnizca paylasim
        korunumlu oldu ve tavan baglayici olmaktan cikti'. Rejim baska bir
        yerden ayrisirsa bu iddia coker."""
        eko = load_config(os.path.join(ROOT, "experiments", "faz45_ekoloji.yaml")).to_dict()
        taban = load_config(os.path.join(ROOT, "experiments", "faz4_taban.yaml")).to_dict()
        self.assertEqual(eko["world"], taban["world"], "yemek arzi degismis")
        self.assertEqual(eko["rules"]["share"]["need_mode"], "fitness")
        self.assertEqual(taban["rules"]["share"]["need_mode"], "energy")
        self.assertGreater(eko["agents"]["max_count"], taban["agents"]["max_count"])
        # geri kalan her sey ayni olmali
        for d in (eko, taban):
            d["agents"]["max_count"] = 0
            d["rules"]["share"]["need_mode"] = "-"
        self.assertEqual(_mechanics(eko), _mechanics(taban))

    def test_predator_is_off(self):
        cfg = load_config(
            overrides=seed_sweep.FIXED + seed_sweep.REGIME + [basin_map.PREDATOR_OFF]
        )
        self.assertFalse(cfg.rules.predator.enabled)

    def test_threshold_comes_from_the_data_not_a_constant(self):
        """Esik en buyuk boslugun ORTASI olmali; veri kayinca esik de kaymali."""
        low = [0.10, 0.11, 0.12]
        high = [0.50, 0.51, 0.52]
        info = basin_map.largest_gap_threshold(np.array(low + high))
        self.assertAlmostEqual(info["threshold"], 0.31, places=6)
        info2 = basin_map.largest_gap_threshold(np.array(low + [h + 1.0 for h in high]))
        self.assertAlmostEqual(info2["threshold"], 0.81, places=6)

    def test_flat_spread_is_not_called_bimodal(self):
        """Duz bir yelpazede en buyuk bosluk ikincisine yakin olmali (oran ~1)."""
        flat = np.linspace(0.1, 0.5, 12)
        info = basin_map.largest_gap_threshold(flat)
        self.assertLess(info["gap_ratio"], 2.0)
        self.assertLess(info["spread_share"], 0.25)

    def test_clear_split_is_called_bimodal(self):
        info = basin_map.largest_gap_threshold(
            np.array([0.10, 0.11, 0.12, 0.13, 0.60, 0.61, 0.62, 0.63])
        )
        self.assertGreaterEqual(info["gap_ratio"], 2.0)
        self.assertGreaterEqual(info["spread_share"], 0.25)
        self.assertEqual((info["n_low"], info["n_high"]), (4, 4))

    def test_classify_labels_low_forage_as_huddle(self):
        rows = [{"forage": v} for v in (0.02, 0.03, 0.40, 0.41)]
        _info, labels = basin_map.classify(rows, "forage")
        self.assertEqual(labels, ["yumak", "yumak", "toplayici", "toplayici"])


class TestSweepStatistics(unittest.TestCase):
    def test_welch_t_sign_and_zero(self):
        a = np.array([5.0, 5.1, 4.9, 5.0])
        b = np.array([1.0, 1.1, 0.9, 1.0])
        self.assertGreater(seed_sweep.welch_t(a, b), 2.0)
        self.assertLess(seed_sweep.welch_t(b, a), -2.0)
        self.assertAlmostEqual(seed_sweep.welch_t(a, a), 0.0, places=9)

    def test_welch_t_handles_degenerate_input(self):
        z = np.zeros(4)
        self.assertEqual(seed_sweep.welch_t(z, z), 0.0)
        self.assertEqual(seed_sweep.welch_t(np.array([1.0]), np.array([2.0])), 0.0)

    def test_series_takes_the_tail(self):
        """Kesim noktasi tabana yuvarlanir: kisa dizilerde dilim biraz genis olur."""
        rows = [{"x": float(i)} for i in range(24)]           # gercek kosum uzunlugu
        np.testing.assert_allclose(seed_sweep.series(rows, "x", 0.5), np.arange(12, 24))
        np.testing.assert_allclose(seed_sweep.series(rows, "x", 0.25), np.arange(18, 24))
        # 10 eleman + ceyrek -> int(7.5)=7, yani 3 eleman (tam ceyrek degil)
        short = [{"x": float(i)} for i in range(10)]
        np.testing.assert_allclose(seed_sweep.series(short, "x", 0.25), np.arange(7, 10))
        self.assertEqual(seed_sweep.series([], "x").size, 0)


if __name__ == "__main__":
    unittest.main()
