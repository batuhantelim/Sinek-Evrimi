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

import env_sweep  # noqa: E402
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
