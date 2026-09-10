"""Sinek bedeni: konum, enerji, yas, sensorler ve motorlar.

Beden "ne hissettigini" ve "ne yapabildigini" tanimlar; NASIL karar verildigi
beynin isidir (sinek/brains/). Sensor ve motor isimleri sabittir — beyin
backend'leri bu sozlesmeye gore yazilir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# --- Sozlesme: sensor vektoru ------------------------------------------
SENSOR_NAMES: list[str] = [
    "bias",             # 0  sabit 1.0
    "energy",           # 1  enerji / max_enerji            (0..1)
    "age",              # 2  yas / omur                     (0..1)
    "food_here",        # 3  bulundugu hucredeki yemek      (0..1)
    "food_fwd",         # 4  yemek yonu, ileri bileseni     (-1..1)
    "food_left",        # 5  yemek yonu, sol bileseni       (-1..1)
    "food_strength",    # 6  yakindaki toplam yemek sinyali (0..1)
    "hazard_fwd",       # 7  tehlike yonu, ileri            (-1..1)
    "hazard_left",      # 8  tehlike yonu, sol              (-1..1)
    "hazard_near",      # 9  en yakin tehlikeye yakinlik    (0..1)
    "mate_fwd",         # 10 komsu yonu, ileri              (-1..1)
    "mate_left",        # 11 komsu yonu, sol                (-1..1)
    "crowd",            # 12 komsu yogunlugu                (0..1)
]
N_SENSORS = len(SENSOR_NAMES)

# --- Sozlesme: motor vektoru -------------------------------------------
MOTOR_NAMES: list[str] = [
    "turn",     # -1..1  yon degisimi (x max_turn radyan)
    "thrust",   #  0..1  ileri hiz    (x max_speed hucre)
    "eat",      #  0..1  yeme istegi
    "social",   # -1..1  Faz 3: >0 paylas, <0 saldir (Faz 1'de yok sayilir)
]
N_MOTORS = len(MOTOR_NAMES)

S = {name: i for i, name in enumerate(SENSOR_NAMES)}
M = {name: i for i, name in enumerate(MOTOR_NAMES)}


@dataclass
class Agent:
    """Tek bir sinek."""

    id: int
    x: float
    y: float
    heading: float
    energy: float
    genome: object
    brain: object
    lifespan: float
    birth_step: int = 0
    age: int = 0
    alive: bool = True
    parent_id: int = -1

    # yasam boyu istatistikler (metrikler ve secilim icin)
    food_eaten: float = 0.0
    distance: float = 0.0
    children: int = 0
    death_cause: str = ""
    last_motors: np.ndarray = field(
        default_factory=lambda: np.zeros(N_MOTORS, dtype=np.float32)
    )

    # ------------------------------------------------------------------
    def sense(self, world, cfg) -> np.ndarray:
        """Dunyayi bencil (egosentrik) bir sensor vektorune cevirir.

        Tum uzamsal bilgi dunyanin onceden hesaplanmis alanlarindan O(1)
        okunur; ardindan yon vektorleri sinegin bakis acisina dondurulur.
        """
        s = np.zeros(N_SENSORS, dtype=np.float32)
        cx, cy = world.cell(self.x, self.y)

        s[S["bias"]] = 1.0
        s[S["energy"]] = self.energy / float(cfg.agents.energy.max)
        s[S["age"]] = min(1.0, self.age / max(1.0, self.lifespan))
        s[S["food_here"]] = min(1.0, float(world.food[cy, cx]) / world.food_scale)

        ch, sh = math.cos(self.heading), math.sin(self.heading)

        # --- yemek koku gradyani (nereye gidersem daha cok yemek var) ---
        fx = float(world.food_dir_x[cy, cx])
        fy = float(world.food_dir_y[cy, cx])
        s[S["food_fwd"]] = fx * ch + fy * sh
        s[S["food_left"]] = -fx * sh + fy * ch
        s[S["food_strength"]] = float(world.food_grad_strength[cy, cx])

        # --- tehlike (sabit alan, kurulumda hesaplandi) ---
        hx = float(world.hazard_dir_x[cy, cx])
        hy = float(world.hazard_dir_y[cy, cx])
        s[S["hazard_fwd"]] = hx * ch + hy * sh
        s[S["hazard_left"]] = -hx * sh + hy * ch
        s[S["hazard_near"]] = float(world.hazard_near_field[cy, cx])

        # --- komsular (ajan yogunlugu alani) ---
        mx = float(world.crowd_dir_x[cy, cx])
        my = float(world.crowd_dir_y[cy, cx])
        s[S["mate_fwd"]] = mx * ch + my * sh
        s[S["mate_left"]] = -mx * sh + my * ch
        s[S["crowd"]] = float(world.crowd_density[cy, cx])

        return s

    # ------------------------------------------------------------------
    def apply_motors(self, motors: np.ndarray, world, cfg) -> float:
        """Motor vektorunu fizige cevirir. Yenen yemek miktarini dondurur."""
        mot = cfg.agents.motors
        en = cfg.agents.energy

        turn = float(np.clip(motors[M["turn"]], -1.0, 1.0))
        thrust = float(np.clip(motors[M["thrust"]], 0.0, 1.0))
        eat = float(np.clip(motors[M["eat"]], 0.0, 1.0))

        self.heading = (self.heading + turn * float(mot.max_turn)) % (2.0 * math.pi)
        speed = thrust * float(mot.max_speed)
        if speed > 0.0:
            self.x, self.y = world.move(
                self.x, self.y, math.cos(self.heading) * speed, math.sin(self.heading) * speed
            )
            self.distance += speed
            self.energy -= float(en.move_cost) * speed * speed

        gained = 0.0
        if eat > 0.0:
            taken = world.take_food(self.x, self.y, eat * float(en.eat_rate))
            if taken > 0.0:
                gained = taken * float(cfg.world.food.energy_per_unit)
                self.energy = min(float(en.max), self.energy + gained)
                self.food_eaten += taken

        self.last_motors = motors
        return gained

    # ------------------------------------------------------------------
    @property
    def fitness(self) -> float:
        """Faz 2'de secilim baskisi icin kullanilacak basit basari olcusu."""
        return self.age + 4.0 * self.children + 0.5 * self.food_eaten
