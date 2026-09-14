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

from .agent import M, Agent
from .brains import make_brain
from .genome import Genome, founder_genome
from .physics import Physics
from .predator import PredatorPack
from .metrics import (
    behavior_diversity,
    clustering_index,
    genetic_relatedness,
    genome_param_means,
    kin_assortment,
    lineage_stats,
    social_rates,
    weight_diversity,
)
from .spatial import SpatialHash
from .world import World

DEATH_KEYS = {
    "starved": "death_starved",
    "hazard": "death_hazard",
    "old_age": "death_old_age",
    "killed": "death_killed",
    "predator": "death_predator",
}

#: Paylasim istatistiklerinin ayrildigi verici-enerjisi katmani sayisi.
ENERGY_BUCKETS = 5


class Simulation:
    def __init__(self, cfg, seed: int | None = None, initial_genomes=None):
        self.cfg = cfg
        self.seed = int(cfg.seed if seed is None else seed)
        self.rng = np.random.default_rng(self.seed)

        self.physics = Physics.from_config(cfg)
        self.world = World(cfg, self.rng)
        # Hash hucresi SORGU yaricapina gore boyutlandirilir. Faz 3'te sorgu
        # yaricapi akrabalik menzili (~2.5); komsuluk yaricapiyla (~8)
        # boyutlandirmak her sorguyu 15x pahali hale getiriyordu.
        social_on = bool(cfg.get("rules.share.enabled", False)) or bool(
            cfg.get("rules.attack.enabled", False)
        )
        hash_cell = (
            float(cfg.get("rules.kinship.radius", 2.5))
            if social_on
            else float(cfg.agents.senses.neighbor_radius)
        )
        self.hash = SpatialHash(
            self.world.width, self.world.height, max(0.5, hash_cell), self.world.toroidal
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

        # --- Faz 3: sosyal kurallar ---
        self._share_on = bool(cfg.get("rules.share.enabled", False))
        self._attack_on = bool(cfg.get("rules.attack.enabled", False))
        self._social_enabled = self._share_on or self._attack_on
        self.kin_radius = float(cfg.get("rules.kinship.radius", 2.5))
        self.kin_control = str(cfg.get("rules.kinship.control", "none"))
        self.split_rate = float(cfg.get("rules.kinship.split_rate", 0.0))
        # Faz 7: dogumlarin bu oraninda yavru TAZE bir kurucu genomla dogar.
        # 0.0 = Faz 1-6 davranisi (hicbir rng cekimi yapilmaz, hash birebir ayni).
        self.immigration_rate = float(cfg.get("evolution.immigration_rate", 0.0))
        # --- Faz 8: yogunluga bagli secilim (negatif frekans bagimliligi) ---
        # Yerel olarak KALABALIKLASAN soy adim basina ek enerji oder. Hicbir soy
        # adiyla hedeflenmez; ceza yalnizca YEREL FREKANSA bakar. Bir GIDERdir,
        # kaynak degil (paylasimin korunumuna dokunmaz).
        self.crowding_on = bool(cfg.get("rules.crowding.enabled", False))
        self.crowding_radius = float(cfg.get("rules.crowding.radius", 5.0))
        self.crowding_cost = float(cfg.get("rules.crowding.cost", 0.0))
        self.crowding_control = str(cfg.get("rules.crowding.control", "none"))
        if self.crowding_control not in ("none", "shuffled"):
            raise ValueError(
                f"bilinmeyen rules.crowding.control={self.crowding_control!r}"
            )
        if self.kin_control not in ("none", "shuffle_surnames", "random_surname_at_birth", "scatter_offspring"):
            raise ValueError(f"bilinmeyen rules.kinship.control={self.kin_control!r}")
        # --- Faz 5: tanima + hafiza ---
        self.memory_on = bool(cfg.get("rules.memory.enabled", False))
        self.memory_capacity = max(1, int(cfg.get("rules.memory.capacity", 16)))
        self.memory_decay = float(cfg.get("rules.memory.decay", 0.0))
        self.memory_control = str(cfg.get("rules.memory.control", "none"))
        if self.memory_control not in ("none", "shuffle_ledger", "shuffle_identity"):
            raise ValueError(f"bilinmeyen rules.memory.control={self.memory_control!r}")
        # --- Faz 6: partner secimi ---
        self.partner_on = bool(cfg.get("rules.partner.enabled", False)) and self._social_enabled
        self.partner_k = max(1, int(cfg.get("rules.partner.candidates", 4)))
        self.partner_control = str(cfg.get("rules.partner.control", "none"))
        if self.partner_control not in ("none", "random"):
            raise ValueError(f"bilinmeyen rules.partner.control={self.partner_control!r}")

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
        # Her kurucuya benzersiz soyisim; yavrular miras alir (genome.copy).
        # Tohumlanmis genomlar da yeniden isimlendirilir: kayittaki soyisimler
        # baska bir kosumun soyagacina aitti.
        self._next_surname = len(self.agents)
        for i, a in enumerate(self.agents):
            a.genome.surname = i
            # Faz 8: kalabalik cezasinin etiketi soyisimle birlikte yenilenmeli.
            # `_spawn` onu genomdan okuyor ama kurucular BURADA yeniden
            # adlandiriliyor; atlanirsa butun kurucular ayni etiketi tasir ve
            # ceza "herkes ayni soydan" diye hesaplanir (test yakaladi).
            a.crowd_label = i

        self.predators = PredatorPack(cfg, self.world, self.rng)

        self.generation = 0
        self.epoch_length = max(1, int(cfg.get("evolution.epoch_length", 500)))
        self.graveyard: list[Agent] = []  # bu neslin oluleri (secilim havuzunda kalirlar)
        self.generation_rows: list[dict] = []
        self._epoch_acc: dict = {}
        self.share_events: list[tuple] = []   # gorsellestirme icin (x1,y1,x2,y2,kin)
        self.attack_events: list[tuple] = []
        self.stats_step = _empty_stats()
        self.stats_total = _empty_stats()
        self.extinct_at: int | None = None
        self._record_lifetimes = bool(cfg.get("metrics.record_lifetimes", False))
        #: (food_eaten, children, age, given, received) — olum aninda
        self.life_records: list[tuple] = []
        self.last_metrics: dict | None = None  # HUD ve loglama icin son metrik satiri

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
        agent.mem_id = agent.id          # Faz 5: tanima kimligi (kontrol permute eder)
        agent.crowd_label = genome.surname   # Faz 8: kalabalik cezasinin baktigi etiket
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
        if self.predators.enabled:
            for a in self.agents:
                a.predator_signal = self.predators.signal(a.x, a.y)

        if self._social_enabled or self.crowding_on:
            # Faz 3: akrabalik sensoru ve paylasim ayni "en yakin komsu"yu
            # kullanir; bir kez hesaplanip onbellege alinir. Faz 8'in kalabalik
            # cezasi da ayni izgarayi kullanir, sosyal kurallar kapaliyken bile.
            self.hash.build(self.agents)
            if self.crowding_control == "shuffled":
                self._shuffle_crowd_labels()
        if self._social_enabled:
            if self.kin_control == "shuffle_surnames":
                self._shuffle_surnames()
            if self.memory_control == "shuffle_ledger":
                self._shuffle_ledgers()
            elif self.memory_control == "shuffle_identity":
                self._shuffle_identities()
            if self.partner_on:
                # Faz 6: hedef artik dayatilmiyor, SECILIYOR.
                for a in self.agents:
                    a.nearest = self._choose_partner(a)
            else:
                for a in self.agents:
                    a.nearest = self.hash.nearest(a, self.kin_radius, self.world)

        # 3) algi -> karar -> eylem
        phys = self.physics
        rng = self.rng
        inv_energy_per_unit = 1.0 / phys.energy_per_unit
        for a in self.agents:
            gained = a.apply_motors(a.brain.act(a.sense(self.world, phys), rng), self.world, phys)
            self.stats_step["food_eaten"] += gained * inv_energy_per_unit

        # 3.5) sosyal kurallar — olumlerden ONCE: bir paylasim olmak uzere
        #      olan bir sinegi gercekten kurtarabilmeli.
        self._apply_social_rules()

        # 3.6) avci: ajanlar hareket ettikten SONRA vurur, yani kacma sansi
        #      gercekten ise yarayabilir.
        strikes, kills = self.predators.step(self.agents)
        self.stats_step["predator_strikes"] += strikes
        self.stats_step["predator_kills"] += kills

        # 3.7) Faz 8: yogunluga bagli secilim. Yerel olarak ayni etiketten kac
        #      komsusu varsa o kadar ek metabolik gider. Nadir olan ucuz yasar.
        #      Bu bir CEVRE kurali; davranis degil, rol degil, odul degil.
        if self.crowding_on and self.crowding_cost > 0.0:
            self._apply_crowding_cost()

        # 4) cevre etkileri
        metabolism = phys.metabolism
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
                cause = (
                    a.death_cause
                    if a.death_cause in ("hazard", "killed", "predator")
                    else "starved"
                )
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

        for k, v in self.stats_step.items():
            self.stats_total[k] += v

        if not self.agents and self.extinct_at is None:
            self.extinct_at = self.step_index

        for k, v in self.stats_step.items():
            self._epoch_acc[k] = self._epoch_acc.get(k, 0) + v

        # 8) periyodik evrim raporu
        if self.mode == "generational":
            if self.step_index % self.generation_length == 0:
                self._next_generation()
        elif self.step_index % self.epoch_length == 0:
            self._record_epoch()

    def _kill(self, a: Agent, cause: str) -> None:
        a.alive = False
        a.death_cause = cause
        if self._record_lifetimes:
            # Tam yasam kaydi: enerji -> ureme -> secilim zincirinin saglikli
            # olup olmadigi ancak TAMAMLANMIS yasamlarda olculebilir
            # (bkz. tools/selection_probe.py).
            self.life_records.append(
                (a.food_eaten, a.children, a.age, a.given, a.received)
            )
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
        for i, a in enumerate(self.agents):
            if len(self.agents) + len(newborns) >= cap:
                # TAVAN BASKISI. `agents.max_count` bir "bellek/hiz emniyeti"
                # olarak konmustu; bagladiginda ureme bir SLOT KUYRUGUNA doner
                # ve enerji fitness'a donusmez. Kac ureme hakkinin tavan
                # yuzunden yandigini SAYIYORUZ: bu sayac 0'a yakin degilse
                # populasyonu cevre degil sabit sinirliyordur.
                self.stats_step["repro_blocked"] += sum(
                    1 for b in self.agents[i:]
                    if b.energy >= threshold and b.age >= min_age
                )
                break
            if a.energy < threshold or a.age < min_age:
                continue
            child_energy = a.energy * share
            a.energy -= child_energy + cost
            if a.energy <= 0.0:
                a.energy += child_energy + cost  # bolunme bedelini kaldiramaz
                continue
            ang = float(self.rng.uniform(0, 2 * math.pi))
            if self.kin_control == "scatter_offspring":
                # KONTROL: yavru ebeveynin yaninda degil, haritada rastgele
                # dogar -> akrabalarin uzamsal kumelenmesi bozulur.
                cx, cy = self.world.random_position(self.rng)
            else:
                cx, cy = self.world.move(
                    a.x, a.y, math.cos(ang) * radius, math.sin(ang) * radius
                )
            genome = a.genome.child(cfg, self.rng)
            # FAZ 7 — GOCMEN: yavrunun genomu ebeveynden degil TAZE bir
            # kurucudan gelir ve yeni bir soyisim alir. Soylar yalnizca
            # tukenebildigi icin (yeni kurucu yoktu) etkin soy sayisi Faz 6'da
            # ~1'e inmisti; bu, "grup-ici vs grup-disi" olcmeyi imkansiz
            # kiliyor. `split_rate` yalnizca ETIKET uretir (bolunen soy
            # bolundugu anda ebeveyniyle genetik olarak AYNIDIR); gocmen
            # GENETIK cesitlilik uretir.
            #
            # ENERJI DEFTERI: gocmen bir DOGUMUN yerine gecer — ebeveyn ayni
            # maliyeti oder, yavru ayni `child_energy` ile baslar. Yani
            # koloniye enerji EKLEMEZ (disaridan birey enjekte etmek eklerdi).
            # Bedeli seçilimdedir, enerjide degil: uygun bir ebeveynin yavrusu
            # `immigration_rate` olasilikla acemi cikar. Bu bedel olculur.
            immigrant = (
                self.immigration_rate > 0.0
                and self.rng.random() < self.immigration_rate
            )
            if immigrant:
                genome = self.founder.diversified(cfg, self.rng, 1.0)
                self.stats_step["immigrants"] += 1
            if self.kin_control == "random_surname_at_birth":
                # KONTROL: etiket birey icin sabit ama KALITSAL DEGIL.
                # Etiket YASAYAN populasyondan cekilir (0..N araligindan degil):
                # boylece soy buyukluklerinin dagilimi ve dolayisiyla akrabayla
                # karsilasma SIKLIGI asil kosumdakine benzer kalir. Duz rastgele
                # cekim herkesi yabanci yapar, opp_kin ornegi cok kucuk kalir ve
                # in-group orani olculemeyecek kadar gurultulu olur.
                donor = self.agents[int(self.rng.integers(0, len(self.agents)))]
                genome.surname = donor.genome.surname
            elif immigrant:
                # Gocmen tanim geregi yeni bir soydur. Kontrol kolunda ise
                # etiketi yine yasayan populasyondan gelir (yukaridaki dal):
                # kontrol BILGIYI siler, GOCU degil — iki kolda gocmen sayisi
                # ve genetik etkisi ayni kalir.
                genome.surname = self._next_surname
                self._next_surname += 1
            elif self.split_rate > 0.0 and self.rng.random() < self.split_rate:
                # Soy bolunmesi: nadiren yeni bir soyisim dogar.
                # Soylar suruklenmeyle tukendigi icin (kurucu sayisi sadece
                # azalabilir) etiket cesitliligi bu olmadan sifira gider ve
                # in-group/out-group ayrimi anlamsizlasir. Genomu degistirmez,
                # yalnizca soyagaci etiketini yeniler; kontrol grubuna da
                # BIREBIR ayni oranda uygulanir.
                genome.surname = self._next_surname
                self._next_surname += 1
            child = self._spawn(genome, cx, cy, child_energy)
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
            # Cevresel baglam: kitlik taramalarinda rejimin gercekten
            # degistigini dogrulamak icin nesil satirinda da dursun.
            "food_fill": round(
                self.world.food_total / max(1e-9, self.world.food_capacity_total), 5
            ),
            "population": len(self.agents),
            # Faz 4: surulesme (dilution'in davranissal izi) donem satirinda
            # da dursun — avcinin YAN ETKILERINI olcmeden "avci dusmanlik
            # uretti" denemez.
            "clustering": round(clustering_index(self), 5),
        }
        lin = lineage_stats(self.agents)
        row.update(lin)
        # Hamilton'un r'si ETIKETTEN degil GENOMDAN okunur (bkz. Faz 4.6).
        row.update(genetic_relatedness(self.agents))
        acc = self._epoch_acc if self.mode != "generational" else self.stats_total
        row.update(social_rates(acc))
        # Faz 4 avlanma muhasebesi + koloni sagligi (D/C ayrimi bunlara bakar).
        for key in ("deaths", "births", "death_starved", "death_old_age",
                    "death_predator", "predator_strikes", "predator_kills",
                    "repro_blocked", "immigrants"):
            row[key] = int(acc.get(key, 0))
        # KISI BASI hizlar. `food_fill` bir ORANDIR ve kapasiteye bagimlidir;
        # kosullar arasi kiyaslanamaz (eksen B dersi). Bunlar ajan-adim basina
        # mutlak buyukluklerdir: "koloni topluyor mu, yoksa enerjiyi yalnizca
        # aralarinda mi dolastiriyor" sorusu ancak bu ikisiyle sorulabilir.
        window = self.step_index if self.mode == "generational" else self.epoch_length
        denom = max(1, len(self.agents)) * max(1, window)
        row["forage_per_capita"] = round(acc.get("food_eaten", 0.0) / denom, 6)
        row["share_per_capita"] = round(acc.get("share_energy", 0.0) / denom, 6)
        row["predation_risk"] = round(
            acc.get("predator_kills", 0) / max(1, len(self.agents)), 5
        )
        # NOT: firsat sayimlari donem boyunca birikir, soy dagilimi ise donem
        # SONUNDAKI anlik durumdur. Yavas degisen bir buyukluk oldugu icin
        # kabul edilebilir bir yaklasiklik.
        row.update(
            kin_assortment(acc.get("opp_kin", 0), acc.get("opp_nonkin", 0), lin["kin_expected"])
        )
        # Ornek buyuklukleri satirda dursun: kucuk opp_kin ile hesaplanan bir
        # in-group orani gurultudur, okuyan bunu gorebilmeli.
        for key in ("opp_kin", "opp_nonkin", "share_kin", "share_nonkin"):
            row[key] = int(acc.get(key, 0))
        for name, value in genome_param_means(pool).items():
            row[f"gp_{name}"] = round(value, 4)
        return row

    # --------------------------------------------------------------- Faz 3
    def _apply_social_rules(self) -> None:
        """Paylasma (ve ileride saldiri). Config'te kapaliysa hicbir sey yapmaz.

        PAYLASIM ASLA DOGRUDAN ODULLENDIRILMEZ. `evolution.fitness` icinde
        "paylastin diye +puan" YOKTUR ve olmamalidir. Verenin NET kaybi vardir
        (aktarilan enerji + islem maliyeti). Paylasmanin kârli olmasinin tek
        yolu DOLAYLIdir: akrabaya yardim = ortak genin hayatta kalmasi.

        Alici her zaman EN YAKIN komsudur — yani "kime" degil "verecek miyim"
        karari evrimlesir. Akrabalik sensoru de ayni komsuyu bildirdigi icin
        ayrimcilik dogrudan olculebilir:
            P(paylas | en yakin akraba)  vs  P(paylas | en yakin yabanci)

        Transferler id sirasinda ve ardisik uygulanir (simulasyonun geri
        kalaniyla ayni konvansiyon) — deterministik.
        """
        self.share_events.clear()
        self.attack_events.clear()
        if not self._social_enabled:
            return

        cfg = self.cfg
        sh = cfg.rules.share
        at = cfg.rules.attack
        atk_threshold = float(at.threshold)
        atk_damage = float(at.damage)
        atk_steal = float(at.steal_ratio)
        atk_cost = float(at.cost)
        atk_floor = float(at.min_attacker_energy)
        threshold = float(sh.threshold)
        amount_max = float(sh.amount)
        overhead = float(sh.overhead)
        floor = float(sh.min_donor_energy)
        radius2 = self.kin_radius * self.kin_radius
        e_max = self.physics.energy_max
        # "Kurtarma" esigi: bu enerjinin altindaki bir sinek ~20 adim icinde
        # aclıktan olur. Dogrusal olmayan faydanin gerceklestigi yer burasi.
        rescue_level = 20.0 * self.physics.metabolism
        need_bonus = float(sh.get("need_bonus", 0.0))
        need_mode = str(sh.get("need_mode", "fitness"))
        if need_mode not in ("fitness", "energy"):
            raise ValueError(
                f"bilinmeyen rules.share.need_mode: {need_mode!r} "
                "(fitness | energy) — sessizce varsayilana dusulmez"
            )
        stats = self.stats_step

        for a in self.agents:
            other = a.nearest
            if other is None or not other.alive:
                continue
            dx, dy = self.world.delta(a.x, a.y, other.x, other.y)
            if dx * dx + dy * dy > radius2:
                continue  # hareket ettiler, artik menzilde degil

            kin = other.genome.surname == a.genome.surname
            stats["opp_kin" if kin else "opp_nonkin"] += 1
            # Enerji katmani: akrabalar uzamsal kumelendigi icin "en yakini
            # akraba" olmak, zengin bir yamada olmakla — yani paylasacak
            # BUTCEYE sahip olmakla — karisir. Katman icinde karsilastirma
            # bu konfoundu notrler (bkz. metrics.social_rates).
            bucket = min(ENERGY_BUCKETS - 1, int(a.energy / e_max * ENERGY_BUCKETS))
            stats[f"{'opp_kin' if kin else 'opp_non'}_{bucket}"] += 1

            # Faz 5: ayni firsat, DEFTERE gore de siniflanir. "Bu birey bana
            # daha once verdi mi?" Ayni enerji konfoundu burada da var —
            # defteri pozitif olan ajan ENERJI ALMISTIR, yani zengindir ve
            # zaten daha cok paylasir — o yuzden katman ayni sekilde tutulur.
            owes = self.memory_on and a.ledger.get(other.mem_id, 0.0) > 0.0
            grudge = self.memory_on and a.ledger.get(other.mem_id, 0.0) < 0.0
            stats["oppr_pos" if owes else "oppr_nonpos"] += 1
            stats[f"{'oppr_pos' if owes else 'oppr_non'}_{bucket}"] += 1
            stats["oppg_neg" if grudge else "oppg_nonneg"] += 1
            stats[f"{'oppg_neg' if grudge else 'oppg_non'}_{bucket}"] += 1

            share_urge = float(a.last_motors[M["share"]]) if self._share_on else 0.0
            atk_urge = float(a.last_motors[M["attack"]]) if self._attack_on else 0.0
            # Iki eylem birbirini disliyor: esigini daha cok asan kazanir.
            share_margin = share_urge - threshold
            atk_margin = atk_urge - atk_threshold
            if atk_margin > share_margin and atk_margin >= 0.0:
                self._do_attack(
                    a, other, kin, bucket, atk_urge, atk_damage, atk_steal, atk_cost,
                    atk_floor, grudge
                )
                continue
            if share_margin < 0.0:
                continue
            urge = share_urge

            # Verenin net maliyeti: aktarilan + islem. Kendini oldurecek
            # kadarini veremez; taban enerjinin altina inmez.
            budget = a.energy - floor - overhead
            if budget <= 0.0:
                continue
            amount = min(urge * amount_max, budget)
            if amount <= 0.0:
                continue

            a.energy -= amount + overhead
            a.given += amount  # aktarilan enerji (islem maliyeti kimseye gitmez)
            a.shares_made += 1
            # Alici tavanini asamaz; asan kisim BOSA GIDER (azalan verim —
            # tok bir sinege vermek israf, ac olana vermek hayat kurtarir)
            recipient_energy = other.energy
            # AZALAN VERIM. Ham enerji aktariminda b <= c YAPISALDIR (veren
            # amount+overhead oder, alici en fazla amount alir), dolayisiyla
            # r <= 1 ile Hamilton kurali r*b > c ASLA saglanamaz. Bu katsayi
            # ayni kalorinin ac bir aliciya daha degerli olmasini modeller.
            # Verene hicbir sey kazandirmaz — odul degil, alicinin donusum
            # verimidir. 0.0 = dogrusal (varsayilan, onceki davranis).
            need = max(0.0, 1.0 - recipient_energy / e_max)
            multiplier = 1.0 + need_bonus * need if need_bonus > 0.0 else 1.0
            headroom = e_max - other.energy
            if need_mode == "energy":
                # ESKI DAVRANIS (Faz 3 adim 1.5 – Faz 4 tanisi). Alici carpanla
                # birlikte GERCEK enerji alir, yani transfer KORUNUMLU DEGILDIR:
                # her paylasim koloniye net enerji EKLER. Olculdu: %90 isbirligi
                # olan bir kosumda uretilen enerji, yenen yemege esit hale
                # geliyordu (bkz. docs/faz45/). Yalnizca eski sonuclari
                # yeniden uretmek icin korunuyor.
                taken = min(amount * multiplier, headroom)
            else:
                # KORUNUMLU (varsayilan). Alici en fazla aktarilanin kendisini
                # alir; carpan yalnizca MUHASEBEYE girer. "Ayni kalori ac bir
                # aliciya daha degerlidir" iddiasi bir FITNESS iddiasidir,
                # enerji yaratma izni degil.
                taken = min(amount, headroom)
            if taken > 0.0:
                other.energy += taken
                other.received += taken
                # Faz 5: ALICI defterine yazar — "a bana verdi".
                self._remember(other, a, taken)
            # Yaratilan/yok edilen enerji ACIKCA sayilir: korunumlu modda 0
            # olmalidir (`test_sharing_conserves_energy` bunu bekler).
            stats["energy_created"] += taken - min(amount, headroom)

            stats["share_events"] += 1
            stats["share_energy"] += amount
            # Gerceklesen fayda/maliyet muhasebesi (Hamilton'un b ve c'si):
            #   c = verenin kaybi  = amount + overhead
            #   b = alicinin kazanci = taken  (tavani asan kisim bosa gider)
            # Ham enerjide b <= c HER ZAMAN dogrudur; b > c ancak enerjinin
            # fitness'a donusumu DOGRUSAL OLMADIGI yerde olabilir: olmek uzere
            # olan bir aliciya verilen enerji cok daha degerlidir.
            # IKI AYRI MUHASEBE, karistirilmamali:
            #   share_benefit  = ENERJI birimi. Korunumlu modda <= maliyet
            #                    (b/c <= 1 YAPISALDIR — Faz 3 adim 1.5).
            #   share_benefit_fit = FITNESS birimi TAHMINI: alinan enerji x
            #                    alicinin varsayilan donusum verimi. Bu bir
            #                    VARSAYIMDIR; "r*b/c > 1" diye okunursa kendi
            #                    varsayimimizi olcmus oluruz (Faz 4.6 notu).
            stats["share_cost"] += amount + overhead
            stats["share_benefit"] += taken
            stats["share_benefit_fit"] += taken * (multiplier if need_mode != "energy" else 1.0)
            if recipient_energy < rescue_level:
                stats["share_rescue"] += 1
            stats["share_kin" if kin else "share_nonkin"] += 1
            stats[f"{'shr_kin' if kin else 'shr_non'}_{bucket}"] += 1
            # Faz 5 karsiliklilik sayaci
            stats[f"{'rcp_pos' if owes else 'rcp_non'}_{bucket}"] += 1
            self.share_events.append((a.x, a.y, other.x, other.y, kin))

    def _do_attack(self, a, other, kin, bucket, urge, damage, steal, cost, floor,
                   grudge: bool = False) -> None:
        """Saldiri: hedeften enerji alir, hedefe zarar verir, saldirgana MALIYET.

        SALDIRI DA ODULLENDIRILMEZ. `evolution.fitness` icinde saldiri terimi
        yoktur; `attacks_made`/`damage_dealt` yalnizca olcum icindir.

        Maliyet sabit, kazanc ise hedefin enerjisiyle SINIRLI: fakir bir hedefe
        saldirmak net ZARARDIR. Boylece "herkes herkese saldirir" dejenere
        cozumu olusmaz, ayrimcilik icin gercek bir secilim baskisi kalir.
        """
        stats = self.stats_step
        if a.energy - cost <= floor:
            return  # saldiracak gucu yok

        inflicted = min(urge * damage, other.energy)
        a.energy -= cost
        if inflicted > 0.0:
            other.energy -= inflicted
            other.damage_taken += inflicted
            # Faz 5: SALDIRIYA UGRAYAN defterine yazar — "a bana saldirdi".
            self._remember(other, a, -inflicted)
            gained = inflicted * steal
            a.energy = min(self.physics.energy_max, a.energy + gained)
            a.stolen += gained
            a.damage_dealt += inflicted
        a.attacks_made += 1

        stats["attack_events"] += 1
        stats["attack_damage"] += inflicted
        stats["attack_kin" if kin else "attack_nonkin"] += 1
        stats[f"{'atk_kin' if kin else 'atk_non'}_{bucket}"] += 1
        # Faz 5: MISILLEME sayaci — "bana saldirana saldirdim mi?"
        stats[f"{'rtl_neg' if grudge else 'rtl_non'}_{bucket}"] += 1
        if other.energy <= 0.0:
            other.death_cause = "killed"
            stats["attack_kills"] += 1
        self.attack_events.append((a.x, a.y, other.x, other.y, kin))

    def _apply_crowding_cost(self) -> None:
        """Negatif frekans bagimliligi: yerel olarak kalabalik olan soy oder.

        Ceza HICBIR SOYU ADIYLA hedeflemez — yalnizca "menzilimde benimle ayni
        etiketten kac kisi var" sayisina bakar. Butun soyisimler tutarli
        bicimde yeniden adlandirilsa ceza dagilimi birebir ayni kalir
        (`test_crowding_is_lineage_blind` bunu zorlar).

        Bir GIDERdir: enerji yok edilir, yaratilmaz. `crowding_drain` sayaci
        defteri denetlenebilir tutar (Faz 4.5 dersi).
        """
        radius = self.crowding_radius
        cost = self.crowding_cost
        world = self.world
        hash_ = self.hash
        drain = 0.0
        for a in self.agents:
            n = hash_.count_label(a, radius, world, a.crowd_label)
            if n:
                pay = cost * n
                a.energy -= pay
                drain += pay
        self.stats_step["crowding_drain"] += drain

    def _shuffle_crowd_labels(self) -> None:
        """KONTROL: ceza ayni buyuklukte kalir ama ETIKET BILGISIZ olur.

        `crowd_label` yasayanlar arasinda permute edilir; `genome.surname`'e
        DOKUNULMAZ, cunku butun olcumler (soy cesitliligi, in/out) onu okur.
        Boylece iki kol ayni sayida ajan, ayni soy dagilimi ve benzer toplam
        gider ile kosar; yalnizca "kim kiminle ayni sayiliyor" bilgisi gider.
        """
        n = len(self.agents)
        if n < 2:
            return
        labels = [a.crowd_label for a in self.agents]
        perm = self.rng.permutation(n)
        for a, idx in zip(self.agents, perm):
            a.crowd_label = labels[int(idx)]

    def _shuffle_surnames(self) -> None:
        """KONTROL: soyisimleri yasayanlar arasinda karistirir.

        Etiket ile gercek akrabalik arasindaki bagi koparir; akrabalik
        sensoru saf gurultuye doner. Bu kontrolde isbirligi evrimlesmemeli.
        """
        if len(self.agents) < 2:
            return
        names = [a.genome.surname for a in self.agents]
        order = self.rng.permutation(len(names))
        for a, idx in zip(self.agents, order):
            a.genome.surname = names[int(idx)]

    def _choose_partner(self, a: Agent):
        """Faz 6: aday havuzundan hedefi SECER.

        Skor GENOMDAN gelir — kodda tek bir tercih katsayisi yoktur:

            skor = pick_kin*kin + pick_ledger*defter + pick_need*ihtiyac
                   + pick_energy*enerji + pick_dist*(-mesafe)

        Tum agirliklar 0 baslar; o zaman skor herkeste 0'dir ve beraberligi
        MESAFE bozar (aday listesi mesafeye gore sirali), yani davranis
        secimsiz kolla OZDESTIR. "Iyi partner sec" diye bir kural yoktur.
        """
        pool = self.hash.candidates(a, self.kin_radius, self.world, self.partner_k)
        if not pool:
            self._pick_pool_reset()
            return None
        if len(pool) == 1:
            self._note_pick(a, pool, 0)
            return pool[0][0]
        if self.partner_control == "random":
            # KONTROL: secme yetenegi var, politika yok.
            idx = int(self.rng.integers(0, len(pool)))
            self._note_pick(a, pool, idx)
            return pool[idx][0]

        p = a.genome.params
        w_kin = p.get("pick_kin", 0.0)
        w_led = p.get("pick_ledger", 0.0)
        w_need = p.get("pick_need", 0.0)
        w_en = p.get("pick_energy", 0.0)
        w_dist = p.get("pick_dist", 0.0)
        e_max = self.physics.energy_max
        best_i, best_score = 0, None
        for i, (other, d2) in enumerate(pool):
            kin = 1.0 if other.genome.surname == a.genome.surname else -1.0
            led = 0.0
            if self.memory_on:
                bal = a.ledger.get(other.mem_id)
                if bal is not None:
                    led = math.tanh(bal / self.physics.memory_scale)
            frac = other.energy / e_max
            score = (
                w_kin * kin + w_led * led + w_need * (1.0 - frac)
                + w_en * frac + w_dist * (-math.sqrt(d2))
            )
            # Beraberlikte once gelen (daha yakin, sonra kucuk id) kazanir.
            if best_score is None or score > best_score:
                best_i, best_score = i, score
        self._note_pick(a, pool, best_i)
        return pool[best_i][0]

    def _pick_pool_reset(self) -> None:
        pass

    def _note_pick(self, a: Agent, pool, idx: int) -> None:
        """KIMI sectigini olcer: secilenin profili vs ADAY HAVUZUNUN profili.

        Politika evrimlesmediyse ikisi ayni cikar. Bu yuzden "secim akrabaya
        yoneldi" iddiasi havuz ortalamasina karsi okunur, sifira karsi degil.
        """
        stats = self.stats_step
        stats["pick_events"] += 1
        stats["pick_pool"] += len(pool)
        if len(pool) >= 2:
            stats["pick_multi"] += 1
        if idx != 0:
            stats["pick_not_nearest"] += 1
        chosen = pool[idx][0]
        near = pool[0][0]          # politika olmasaydi secilecek olan
        if chosen.genome.surname == a.genome.surname:
            stats["pick_kin"] += 1
        # ⚠ ASIL REFERANS EN YAKIN, havuz ortalamasi DEGIL. Akrabalar uzamsal
        # kumelendigi icin en yakin zaten havuz ortalamasindan daha sik
        # akrabadir; havuza karsi okunan secicilik, politika hic yokken bile
        # +0.05 cikiyor (olculdu). Politikanin KENDI katkisi ancak "secilen vs
        # en yakin" farkiyla izole edilir.
        if near.genome.surname == a.genome.surname:
            stats["near_kin"] += 1
        stats["pool_kin"] += sum(
            1 for o, _ in pool if o.genome.surname == a.genome.surname
        )
        if self.memory_on:
            if a.ledger.get(chosen.mem_id, 0.0) > 0.0:
                stats["pick_ledger_pos"] += 1
            if a.ledger.get(near.mem_id, 0.0) > 0.0:
                stats["near_ledger_pos"] += 1
            stats["pool_ledger_pos"] += sum(
                1 for o, _ in pool if a.ledger.get(o.mem_id, 0.0) > 0.0
            )

    def _shuffle_ledgers(self) -> None:
        """KONTROL (ASIL): her ajanin defterindeki DEGERLERI kendi partnerleri
        arasinda karistirir.

        Neden bu, `shuffle_identity`'den daha iyi bir kontrol: kimlikleri
        karistirmak, defterde kayitli bir bireye rastlama olasiligini da yok
        eder (olculdu: defteri pozitif firsat 17751 -> 417, 43x kucuk ornek).
        O zaman "bilgi yok oldugu icin mi, ornek kalmadigi icin mi" ayirt
        edilemez — Faz 3'te `random_surname_at_birth`'un ilk surumunde yapilan
        hatanin aynisi.

        Buradaki karistirma ORNEKLEMI AYNEN KORUR: ajan yine ayni sayida
        partneri taniyor, defterinde yine ayni degerler var; yalnizca HANGI
        partnerin hangi degere sahip oldugu bilgisizlesir. `partner_known`
        degismez, yalnizca `partner_ledger` anlamsizlasir.
        """
        for a in self.agents:
            led = a.ledger
            if len(led) < 2:
                continue
            keys = list(led)
            vals = [led[k] for k in keys]
            order = self.rng.permutation(len(vals))
            for k, idx in zip(keys, order):
                led[k] = vals[int(idx)]

    def _shuffle_identities(self) -> None:
        """KONTROL: TANIMA kimliklerini yasayanlar arasinda karistirir.

        Defter artik yanlis bireyi gosterir — "bu bana yardim etmisti" bilgisi
        tanimi geregi bilgisiz olur. Karsiliklilik bu kontrolde COKMELI.

        `id` DOKUNULMAZ: ajan sirasi ve determinizm ona baglidir; yalnizca
        `mem_id` permute edilir.
        """
        if len(self.agents) < 2:
            return
        ids = [a.mem_id for a in self.agents]
        order = self.rng.permutation(len(ids))
        for a, idx in zip(self.agents, order):
            a.mem_id = ids[int(idx)]

    def _remember(self, owner: Agent, partner: Agent, delta: float) -> None:
        """Defterine yaz: ALICI kaydeder, veren degil.

        Kapasite dolunca EN ZAYIF kayit (|deger| en kucuk, esitlikte en kucuk
        kimlik) atilir — deterministik, sozluk sirasina bagimli degil.
        """
        if not self.memory_on:
            return
        led = owner.ledger
        key = partner.mem_id
        led[key] = led.get(key, 0.0) + delta
        if len(led) > self.memory_capacity:
            victim = min(led.items(), key=lambda kv: (abs(kv[1]), kv[0]))[0]
            del led[victim]

    def _record_epoch(self) -> None:
        """steady_state modunda periyodik evrim raporu.

        Nesil siniri olmadigi icin "nesil" yerine sabit uzunlukta ZAMAN DILIMI
        raporlanir; generations.csv semasi ayni kalir, grafik araclari bozulmaz.
        """
        if not self.agents:
            return
        fits = np.array([a.fitness(self.fitness_weights) for a in self.agents], dtype=np.float64)
        order = np.argsort(-fits, kind="stable")
        row = self._generation_row(self.agents, fits, order)
        self.generation += 1
        self._epoch_acc = {}
        self.generation_rows.append(row)

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
        "immigrants": 0,        # Faz 7: taze kurucu genomla dogan yavru sayisi
        "crowding_drain": 0.0,  # Faz 8: yogunluk cezasinin yaktigi enerji (GIDER)
        "deaths": 0,
        "repro_blocked": 0,   # tavan yuzunden yanan ureme hakki (Faz 4.5)
        "death_starved": 0,
        "death_hazard": 0,
        "death_old_age": 0,
        "death_killed": 0,
        "death_predator": 0,
        "food_eaten": 0.0,
        # --- Faz 4 ---
        "predator_strikes": 0,
        "predator_kills": 0,
        # --- Faz 3 ---
        "share_events": 0,      # gerceklesen paylasim sayisi
        "share_energy": 0.0,    # aktarilan toplam enerji
        "opp_kin": 0,           # en yakin komsusu AKRABA olan ajan-adim sayisi
        "opp_nonkin": 0,        # en yakin komsusu YABANCI olan ajan-adim sayisi
        "share_kin": 0,         # bunlarin kacinda paylasildi
        "share_nonkin": 0,
        "share_cost": 0.0,      # verenlerin toplam kaybi   (Hamilton c)
        "share_benefit": 0.0,   # alicilarin toplam ENERJI kazanci (Hamilton b)
        "share_benefit_fit": 0.0,  # ayni sey FITNESS birimi TAHMINIYLE (varsayim!)
        "share_rescue": 0,      # olmek uzere olan bir aliciya yapilan paylasim
        "energy_created": 0.0,  # paylasimin yarattigi/yok ettigi net enerji (Faz 4.5)
        # --- Faz 6: partner secimi ---
        "pick_events": 0,       # kac kez aday havuzundan secim yapildi
        "pick_pool": 0,         # toplam aday (ortalama havuz buyuklugu icin)
        "pick_not_nearest": 0,  # secim EN YAKIN olmayani sectiyse
        "pick_multi": 0,        # havuzda >=2 aday oldugu karar sayisi (onkosul)
        "pick_kin": 0,          # secilen akraba miydi
        "near_kin": 0,          # EN YAKIN akraba miydi (ASIL referans)
        "pool_kin": 0,          # havuzdaki akraba sayisi (konfoundlu referans)
        "pick_ledger_pos": 0,   # secilenin defteri pozitif miydi
        "near_ledger_pos": 0,
        "pool_ledger_pos": 0,
        # --- Faz 5: karsiliklilik (defter isaretine kosullu) ---
        "oppr_pos": 0,          # defteri POZITIF olan partnerle firsat
        "oppr_nonpos": 0,
        "oppg_neg": 0,          # defteri NEGATIF olan partnerle firsat
        "oppg_nonneg": 0,
        **{f"oppr_pos_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"oppr_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"rcp_pos_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"rcp_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"oppg_neg_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"oppg_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"rtl_neg_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"rtl_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
        # --- Faz 3 adim 2: saldiri ---
        "attack_events": 0,
        "attack_damage": 0.0,
        "attack_kills": 0,
        "attack_kin": 0,
        "attack_nonkin": 0,
        # Enerji katmanli sayimlar (konfound duzeltmesi icin)
        **{f"opp_kin_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"opp_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"shr_kin_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"shr_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"atk_kin_{b}": 0 for b in range(ENERGY_BUCKETS)},
        **{f"atk_non_{b}": 0 for b in range(ENERGY_BUCKETS)},
    }
