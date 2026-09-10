"""Simulasyon dongusu: dunya + ajanlar + beyinler + metrikler.

Adim sirasi (determinizm icin sabit):
  1. dunya yenilenir (yemek buyur)
  2. uzamsal hash kurulur
  3. her ajan (id sirasinda): algila -> karar ver -> hareket et / ye
  4. cevre etkileri: tehlike hasari, metabolizma, yaslanma
  5. olumler
  6. uremeler
  7. Faz 3 sosyal kurallar (rules.*) — Faz 1'de etkisiz
  8. nesil siniri geldiyse secilim + yeni nesil (yalnizca generational modda)

Tum rastgelelik tek bir np.random.Generator'dan gelir; ajanlar hep ayni
sirayla cizim yapar. Ayni seed -> ayni sonuc.

IKI EVRIM MODU (evolution.mode)
-------------------------------
steady_state : Faz 1'in ekolojisi. Ureme surekli ve aseksuel; enerji esigini
               asan bolunur. Secilim ortuk: cok yemek bulan cok cocuk birakir.
               Boom-bust salinimi ve populasyon dinamigi korunur.
generational : Klasik GA. Sabit uzunlukta nesiller; nesil sonunda TUM birey
               havuzu (yasayanlar + o nesilde olenler) fitness'a gore
               siralanir, turnuva secilimi + elitizm ile yeni nesil kurulur,
               dunya sifirlanir. "Nesiller boyunca ortalama basari artiyor mu"
               sorusu en temiz burada olculur.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from .agent import Agent
from .brains import make_brain
from .genome import Genome, founder_genome
from .metrics import behavior_diversity, genome_param_means, weight_diversity
from .spatial import SpatialHash
from .world import World

DEATH_KEYS = {"starved": "death_starved", "hazard": "death_hazard", "old_age": "death_old_age"}


class Simulation:
    def __init__(self, cfg, seed: int | None = None, initial_genomes=None):
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

        # --- evrim ayarlari ---
        self.mode = str(cfg.get("evolution.mode", "steady_state"))
        if self.mode not in ("steady_state", "generational"):
            raise ValueError(
                f"bilinmeyen evolution.mode={self.mode!r} (steady_state | generational)"
            )
        self.generation_length = max(1, int(cfg.get("evolution.generation_length", 250)))
        self.fitness_weights = _as_dict(cfg.get("evolution.fitness", {}))
        # Nesilli modda ureme kapatilir: secilim nesil sonunda toplu yapilir,
        # yoksa iki secilim mekanizmasi birbirine karisir.
        self._repro_enabled = bool(cfg.agents.reproduction.enabled) and self.mode != "generational"

        self.founder = founder_genome(cfg, self.rng)
        n0 = int(cfg.agents.initial_count)
        if initial_genomes:
            # Kayitli koloniyle tohumla; havuz kucukse basa donerek tekrarla.
            seeds = [initial_genomes[i % len(initial_genomes)].copy() for i in range(n0)]
            self.agents: list[Agent] = [self._spawn(g) for g in seeds]
        else:
            spread = float(cfg.get("evolution.founder_spread", 0.0))
            self.agents = [
                self._spawn(self.founder.diversified(cfg, self.rng, spread)) for _ in range(n0)
            ]

        self.generation = 0
        self.graveyard: list[Agent] = []  # bu neslin oluleri (secilim havuzunda kalirlar)
        self.generation_rows: list[dict] = []
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
        if self._repro_enabled:
            self._reproduce()

        # 7) sosyal kurallar (Faz 3 kancasi)
        self._apply_social_rules()

        for k, v in self.stats_step.items():
            self.stats_total[k] += v

        if not self.agents and self.extinct_at is None:
            self.extinct_at = self.step_index

        # 8) nesil siniri
        if self.mode == "generational" and self.step_index % self.generation_length == 0:
            self._next_generation()

    def _kill(self, a: Agent, cause: str) -> None:
        a.alive = False
        a.death_cause = cause
        self.stats_step["deaths"] += 1
        self.stats_step[DEATH_KEYS[cause]] += 1
        if self.mode == "generational":
            # Erken olenler de secilim havuzunda kalir; yoksa "hicbir sey
            # yapmayip hayatta kalmak" yapay bir avantaja donusur.
            self.graveyard.append(a)

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

    # ------------------------------------------------------------- secilim
    def _next_generation(self) -> None:
        """Nesil sonu: fitness'a gore secilim + yeni neslin kurulmasi.

        Secilim havuzu = hayatta kalanlar + bu nesilde olenler. Olenleri
        disarida birakmak, "erken olen hic yarismamis" sayilmasina yol acar
        ve secilimi carpitir.
        """
        cfg = self.cfg
        pool = self.agents + self.graveyard
        if not pool:
            return  # koloni tukendi; run() dongusu zaten durduracak

        fits = np.array([a.fitness(self.fitness_weights) for a in pool], dtype=np.float64)
        order = np.argsort(-fits, kind="stable")  # stable => determinizm
        self.generation_rows.append(self._generation_row(pool, fits, order))

        n_new = int(cfg.agents.initial_count)
        elite = max(0, min(int(cfg.get("evolution.elite_count", 2)), len(pool), n_new))
        tournament = max(2, int(cfg.get("evolution.tournament_size", 4)))

        # elitler: en iyi genomlar mutasyonsuz gecer (kazanimi kaybetmemek icin)
        parents = [pool[int(order[i])] for i in range(elite)]
        # geri kalan: turnuva secilimi — k rastgele aday, en iyisi ebeveyn olur
        while len(parents) < n_new:
            idx = self.rng.integers(0, len(pool), size=tournament)
            parents.append(pool[int(idx[int(np.argmax(fits[idx]))])])

        self.generation += 1
        if bool(cfg.get("evolution.reset_world", True)):
            self.world.reset_food()

        newborn: list[Agent] = []
        for i, parent in enumerate(parents[:n_new]):
            if i < elite:
                genome = parent.genome.copy()
                genome.lineage = parent.genome.lineage + 1
            else:
                genome = parent.genome.child(cfg, self.rng)
            child = self._spawn(genome)
            child.parent_id = parent.id
            newborn.append(child)

        self.agents = newborn
        self.graveyard = []

    def _generation_row(self, pool, fits: np.ndarray, order: np.ndarray) -> dict:
        survivors = sum(1 for a in pool if a.alive)
        row = {
            "generation": self.generation,
            "step": self.step_index,
            "pool": len(pool),
            "survivors": survivors,
            "mean_fitness": round(float(fits.mean()), 3),
            "median_fitness": round(float(np.median(fits)), 3),
            "max_fitness": round(float(fits.max()), 3),
            "mean_age": round(float(np.mean([a.age for a in pool])), 2),
            "mean_food_eaten": round(float(np.mean([a.food_eaten for a in pool])), 3),
            "best_food_eaten": round(float(pool[int(order[0])].food_eaten), 3),
            "behavior_diversity": round(behavior_diversity(pool), 5),
            "weight_diversity": round(weight_diversity(pool), 5),
        }
        for name, value in genome_param_means(pool).items():
            row[f"gp_{name}"] = round(value, 4)
        return row

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
            # genom da duruma dahil: mutasyon akisi bozulursa test yakalasin
            h.update(np.round(a.genome.vector(), 6).tobytes())
            if a.genome.weights.size:
                h.update(np.round(a.genome.weights.astype(np.float64), 5).tobytes())
        return h.hexdigest()[:16]

    @property
    def population(self) -> int:
        return len(self.agents)


def _as_dict(node) -> dict:
    return node.to_dict() if hasattr(node, "to_dict") else dict(node or {})


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
