"""Faz 2 beyni: kucuk, evrimlesebilir recurrent sinir agi.

Tum agirliklar `genome.weights`'ten gelir — kodda tek bir davranis katsayisi
yoktur. Ne yapacagini kimse soylemez; ne yapanin daha cok cocuk biraktigina
secilim karar verir.

    h_t = tanh(W_ih @ s + W_hh @ h_{t-1} + b_h)
    h_t = (1 - leak) * h_{t-1} + leak * h_t        (sizintili integratör)
    o   = W_ho @ h_t + b_o

Recurrent baglanti (W_hh) sinegin KISA SURELI BELLEGI: "az once yemek
kokusu daha guclu muydu?" gibi bir bilgi ancak boyle tutulabilir. Bu,
refleks beynin yapisal olarak yapamadigi seydir.
"""

from __future__ import annotations

import numpy as np

from ..agent import M, N_MOTORS, N_SENSORS
from .base import Brain, register


@register("rnn")
class TinyRNN(Brain):
    # Davranis tamamen agirliklarda; isimli parametrelerden yalnizca kesif
    # gurultusunun olcegi okunur. Geri kalanlar notr surukleme referansidir.
    uses_params = ("wander",)

    def __init__(self, genome, cfg):
        super().__init__(genome, cfg)
        h = self.hidden_size(cfg)
        need = self.genome_size(cfg)
        w = genome.weights
        if w.size != need:
            raise ValueError(
                f"genom agirlik sayisi uyusmuyor: {w.size} var, {need} gerekli "
                f"(brain.hidden={h}). Genom baska bir beyin icin uretilmis olabilir."
            )

        # Dilimler genomun uzerine GORUNUM (view) acar: kopya maliyeti yok.
        # Mutasyon her zaman yeni bir dizi baglar ve beyin cocuk genomundan
        # SONRA kurulur, dolayisiyla bayat gorunum olusmaz.
        i = 0
        self.W_ih = w[i : i + h * N_SENSORS].reshape(h, N_SENSORS); i += h * N_SENSORS
        self.W_hh = w[i : i + h * h].reshape(h, h); i += h * h
        self.b_h = w[i : i + h]; i += h
        self.W_ho = w[i : i + N_MOTORS * h].reshape(N_MOTORS, h); i += N_MOTORS * h
        self.b_o = w[i : i + N_MOTORS]

        self.leak = float(np.clip(cfg.get("brain.rnn_leak", 0.5), 0.0, 1.0))
        # Kesif gurultusu de evrimlesir: genomdaki 'wander' onu olcekler.
        self.noise = float(cfg.get("brain.noise", 0.15)) * float(genome.params.get("wander", 1.0))
        self.state = np.zeros(h, dtype=np.float32)

    # ------------------------------------------------------------------
    @staticmethod
    def hidden_size(cfg) -> int:
        return max(1, int(cfg.get("brain.hidden", 12)))

    @staticmethod
    def genome_size(cfg) -> int:
        h = TinyRNN.hidden_size(cfg)
        return h * N_SENSORS + h * h + h + N_MOTORS * h + N_MOTORS

    def reset(self) -> None:
        self.state[:] = 0.0

    # ------------------------------------------------------------------
    def act(self, sensors: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        pre = self.W_ih @ sensors + self.W_hh @ self.state + self.b_h
        self.state += self.leak * (np.tanh(pre) - self.state)
        out = self.W_ho @ self.state + self.b_o

        motors = np.empty(N_MOTORS, dtype=np.float32)
        turn = out[M["turn"]]
        if self.noise > 0.0:
            turn = turn + self.noise * float(rng.normal(0.0, 1.0))
        motors[M["turn"]] = np.tanh(turn)
        # thrust ve eat 0..1 araliginda olmali; tanh'i kaydirip olcekliyoruz
        motors[M["thrust"]] = 0.5 * (np.tanh(out[M["thrust"]]) + 1.0)
        motors[M["eat"]] = 0.5 * (np.tanh(out[M["eat"]]) + 1.0)
        motors[M["social"]] = np.tanh(out[M["social"]])  # Faz 3
        return motors
