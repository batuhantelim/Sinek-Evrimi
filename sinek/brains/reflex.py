"""Faz 1 beyni: genom parametreleriyle ayarlanan basit refleks devresi.

Sinir agi yok — sensorlerin agirlikli toplami dogrudan motorlari suruyor.
Onemli olan: agirliklar KOD'da degil GENOM'da. Faz 2'de mutasyon acilinca
bu ayni devre nesiller boyunca kendiliginden ayrisacak.
"""

from __future__ import annotations

import numpy as np

from ..agent import M, N_MOTORS, S
from .base import Brain, register


@register("reflex")
class ReflexBrain(Brain):
    """Durumsuz refleks devresi. Ayni sensor -> ayni motor (gurultu haric)."""

    def __init__(self, genome, cfg):
        super().__init__(genome, cfg)
        p = genome.params
        self.food_attraction = float(p.get("food_attraction", 1.0))
        self.hazard_avoidance = float(p.get("hazard_avoidance", 1.0))
        self.crowd_bias = float(p.get("crowd_bias", 0.0))
        self.wander = float(p.get("wander", 0.3))
        self.speed_pref = float(p.get("speed_pref", 0.6))
        self.eat_threshold = float(p.get("eat_threshold", 0.02))
        self.hunger_gain = float(p.get("hunger_gain", 1.0))
        self.graze_slowdown = float(p.get("graze_slowdown", 0.75))
        self.panic_speed = float(p.get("panic_speed", 0.6))
        self.hunger_speed = float(p.get("hunger_speed", 0.25))
        self.share_urge = float(np.clip(p.get("share_urge", 0.0), 0.0, 1.0))
        self.turn_gain = float(cfg.get("brain.turn_gain", 1.5))

    def act(self, sensors: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        motors = np.zeros(N_MOTORS, dtype=np.float32)

        hunger = 1.0 - float(sensors[S["energy"]])
        seek = self.food_attraction * (1.0 + self.hunger_gain * hunger)

        # Donus istegi: sol tarafta ne var? (+ sola, - saga)
        desire = (
            seek * sensors[S["food_left"]] * sensors[S["food_strength"]]
            - self.hazard_avoidance * sensors[S["hazard_left"]] * sensors[S["hazard_near"]]
            + self.crowd_bias * sensors[S["mate_left"]] * sensors[S["crowd"]]
        )
        desire += self.wander * float(rng.normal(0.0, 1.0))
        motors[M["turn"]] = np.tanh(self.turn_gain * desire)

        # Hiz: uzerinde yemek varsa yavasla (alan-kisitli arama), tehlikede hizlan.
        # Bu katsayilar da GENOMDAN gelir; Faz 2'de otlama stratejisi de evrimlesebilir.
        food_here = float(sensors[S["food_here"]])
        graze = min(1.0, food_here / max(1e-6, self.eat_threshold + 0.05))
        thrust = self.speed_pref * (1.0 - self.graze_slowdown * graze)
        thrust += self.panic_speed * self.hazard_avoidance * float(sensors[S["hazard_near"]])
        thrust += self.hunger_speed * hunger
        motors[M["thrust"]] = np.clip(thrust, 0.0, 1.0)

        motors[M["eat"]] = 1.0 if food_here > self.eat_threshold else 0.0
        # Refleks devre akrabalik gormez: paylasim egilimi tek bir genom
        # parametresi, akrabaliga gore kosullanamaz. Kosullu davranis icin
        # rnn beyni gerekir — karsilastirma noktasi tam olarak bu.
        motors[M["share"]] = self.share_urge
        return motors
