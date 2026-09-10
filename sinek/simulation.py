"""Simulasyon dongusu: dunya + ajanlar + beyinler + metrikler.

Adim sirasi (determinizm icin sabit):
  1. dunya yenilenir (yemek buyur)
  2. uzamsal hash kurulur
  3. her ajan (id sirasinda): algila -> karar ver -> hareket et / ye
  4. cevre etkileri: tehlike hasari, metabolizma, yaslanma
  5. olumler
  6. uremeler
  7. Faz 3 sosyal kurallar (rules.*) — Faz 1'de etkisiz
  8. metrikler

Tum rastgelelik tek bir np.random.Generator'dan gelir; ajanlar hep ayni
sirayla cizim yapar. Ayni seed -> ayni sonuc.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from .agent import Agent, M
from .brains import make_brain
from .genome import Genome, founder_genome
from .spatial import SpatialHash
from .world import World

DEATH_KEYS = {"starved": "death_starved", "hazard": "death_hazard", "old_age": "death_old_age"}


class Simulation:
    def __init__(self, cfg, seed: int | None = None):
        self.cfg = cfg
        self.seed = int(cfg.seed if seed is None else seed)
        self.rng = np.random.default_rng(self.seed)

        self.world = World(cfg, self.rng)
        self.hash = SpatialHash(
            self.world.width,
            self.world.height,
            float(cfg.agents.senses.neighbor_radius),
            self.world.toroidal,
        )

        self.step_index = 0
        self._next_id = 0
        self.founder = founder_genome(cfg)
        self.agents: list[Agent] = [
            self._spawn(self.founder.copy()) for _ in range(int(cfg.agents.initial_count))
        ]
        self.stats_step = _empty_stats()
        self.stats_total = _empty_stats()
        self.extinct_at: int | None = None
        self.last_metrics: dict | None = None  # HUD ve loglama icin son metrik satiri
        self._social_enabled = bool(cfg.get("rules.share.enabled", False)) or bool(
            cfg.get("rules.attack.enabled", False)
        )

    # ------------------------------------------------------------- kurulum
    def _spawn(self, genome: Genome, x=None, y=None, energy=None) -> Agent:
        cfg = self.cfg
        if x is None or y is None:
            if str(cfg.agents.get("spawn", "scatter")) == "center":
                x = self.world.width * 0.5 + float(self.rng.normal(0, 3))
                y = self.world.height * 0.5 + float(self.rng.normal(0, 3))
                x, y = self.world.move(x, y, 0.0, 0.0)
            else:
                x, y = self.world.random_position(self.rng)
        jitter = float(cfg.agents.get("lifespan_jitter", 0.0))
        lifespan = float(cfg.agents.lifespan) + (
            float(self.rng.uniform(-jitter, jitter)) if jitter > 0 else 0.0
        )
        agent = Agent(
            id=self._next_id,
            x=float(x),
            y=float(y),
            heading=float(self.rng.uniform(0, 2 * math.pi)),
            energy=float(cfg.agents.energy.initial if energy is None else energy),
            genome=genome,
            brain=make_brain(cfg, genome),
            lifespan=max(1.0, lifespan),
            birth_step=self.step_index,
        )
        self._next_id += 1
        return agent

    # ---------------------------------------------------------------- adim
    def step(self) -> None:
        cfg = self.cfg
        self.step_index += 1
        self.stats_step = _empty_stats()

        # 1) dunya
        self.world.step()

        # 2) algi alanlarini tazele (yemek kokusu + ajan yogunlugu)
        self.world.update_food_perception()
        self.world.update_crowd_perception(
            np.fromiter((a.x for a in self.agents), dtype=np.float32, count=len(self.agents)),
            np.fromiter((a.y for a in self.agents), dtype=np.float32, count=len(self.agents)),
        )
        if self._social_enabled:
            self.hash.build(self.agents)  # Faz 3 ikili etkilesimler icin

        # 3) algi -> karar -> eylem
        for a in self.agents:
            sensors = a.sense(self.world, cfg)
            motors = a.brain.act(sensors, self.rng)
            gained = a.apply_motors(motors, self.world, cfg)
            self.stats_step["food_eaten"] += gained / float(cfg.world.food.energy_per_unit)

        # 4) cevre etkileri
        metabolism = float(cfg.agents.energy.metabolism)
        for a in self.agents:
            dmg = self.world.hazard_damage_at(a.x, a.y)
            if dmg > 0.0:
                a.energy -= dmg
                a.death_cause = "hazard"  # olurse sebebi bu adimdaki hasardir
            a.energy -= metabolism
            a.age += 1

        # 5) olumler
        survivors = []
        for a in self.agents:
            if a.energy <= 0.0:
                cause = a.death_cause if a.death_cause == "hazard" else "starved"
                self._kill(a, cause)
            elif a.age >= a.lifespan:
                self._kill(a, "old_age")
            else:
                a.death_cause = ""
                survivors.append(a)
        self.agents = survivors

        # 6) ureme
        if bool(cfg.agents.reproduction.enabled):
            self._reproduce()

        # 7) sosyal kurallar (Faz 3 kancasi)
        self._apply_social_rules()

        for k, v in self.stats_step.items():
            self.stats_total[k] += v

        if not self.agents and self.extinct_at is None:
            self.extinct_at = self.step_index

    def _kill(self, a: Agent, cause: str) -> None:
        a.alive = False
        a.death_cause = cause
        self.stats_step["deaths"] += 1
        self.stats_step[DEATH_KEYS[cause]] += 1

    def _reproduce(self) -> None:
        cfg = self.cfg
        rep = cfg.agents.reproduction
        threshold = float(rep.energy_threshold)
        min_age = int(rep.min_age)
        cost = float(rep.cost)
        share = float(rep.child_share)
        radius = float(rep.spawn_radius)
        cap = int(cfg.agents.max_count)

        newborns: list[Agent] = []
        for a in self.agents:
            if len(self.agents) + len(newborns) >= cap:
                break
            if a.energy < threshold or a.age < min_age:
                continue
            child_energy = a.energy * share
            a.energy -= child_energy + cost
            if a.energy <= 0.0:
                a.energy += child_energy + cost  # bolunme bedelini kaldiramaz
                continue
            ang = float(self.rng.uniform(0, 2 * math.pi))
            cx, cy = self.world.move(a.x, a.y, math.cos(ang) * radius, math.sin(ang) * radius)
            child = self._spawn(a.genome.child(cfg, self.rng), cx, cy, child_energy)
            child.parent_id = a.id
            a.children += 1
            newborns.append(child)
            self.stats_step["births"] += 1
        self.agents.extend(newborns)

    def _apply_social_rules(self) -> None:
        """Faz 3: paylasma / saldiri. Config'te kapaliysa hicbir sey yapmaz."""
        cfg = self.cfg
        if not self._social_enabled:
            return
        # Faz 3'te doldurulacak: motors["social"] isaretine gore enerji transferi.
        # Iskelet burada duruyor ki kural motoru simulasyon dongusune bagli kalsin.
        raise NotImplementedError(
            "Sosyal kurallar Faz 3'te uygulanacak (rules.share / rules.attack)."
        )

    # ---------------------------------------------------------------- kosum
    def run(self, steps: int, on_step=None) -> None:
        for _ in range(steps):
            self.step()
            if on_step is not None:
                on_step(self)
            if not self.agents and bool(self.cfg.get("run.stop_if_extinct", True)):
                break

    # ------------------------------------------------------------ yardimci
    def state_hash(self) -> str:
        """Determinizm testi icin durumun kisa parmak izi."""
        h = hashlib.sha256()
        h.update(np.round(self.world.food, 5).tobytes())
        for a in self.agents:
            h.update(
                np.array(
                    [a.id, round(a.x, 6), round(a.y, 6), round(a.heading, 6), round(a.energy, 6), a.age],
                    dtype=np.float64,
                ).tobytes()
            )
        return h.hexdigest()[:16]

    @property
    def population(self) -> int:
        return len(self.agents)


def _empty_stats() -> dict:
    return {
        "births": 0,
        "deaths": 0,
        "death_starved": 0,
        "death_hazard": 0,
        "death_old_age": 0,
        "food_eaten": 0.0,
        "cooperation_rate": 0.0,
    }
