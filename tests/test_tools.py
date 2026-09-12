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
