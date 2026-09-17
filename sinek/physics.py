"""Sicak yol icin donmus fizik sabitleri.

`Agent.sense` ve `Agent.apply_motors` her ajan icin her adimda cagrilir.
Bu fonksiyonlar config agacini dolasirsa (cfg.agents.motors.max_turn gibi)
adim basina milyonlarca `Cfg.__getattr__` cagrisi olusuyor — profilde
toplam surenin ~%40'i oradaydi.

Cozum: config'i simulasyon kurulurken BIR KEZ duz alanlara acmak.
Deney yapilabilirlik bozulmaz — degerler yine config'ten gelir, sadece
bir kez okunur.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Physics:
    energy_max: float
    metabolism: float
    move_cost: float
    eat_rate: float
    energy_per_unit: float
    max_speed: float
    max_turn: float
    # --- Faz 5: tanima/hafiza kanali (sicak yolda config agaci dolasilmaz) ---
    memory_enabled: bool
    memory_scale: float
    # --- Faz 9 (revize): akrabalik SUREKLI mi ikili mi + hangi formul ---
    #  `binary` Faz 3-9/bilesen-1'in davranisi, `ratio` sureklidir. Saf
    #  soylarda ikisi ozdestir, o yuzden eski fazlar etkilenmez.
    kin_mode: str
    kin_ratio_mode: str

    @classmethod
    def from_config(cls, cfg) -> "Physics":
        en = cfg.agents.energy
        mot = cfg.agents.motors
        return cls(
            energy_max=float(en.max),
            metabolism=float(en.metabolism),
            move_cost=float(en.move_cost),
            eat_rate=float(en.eat_rate),
            energy_per_unit=float(cfg.world.food.energy_per_unit),
            max_speed=float(mot.max_speed),
            max_turn=float(mot.max_turn),
            memory_enabled=bool(cfg.get("rules.memory.enabled", False)),
            memory_scale=max(1e-6, float(cfg.get("rules.memory.scale", 8.0))),
            kin_mode=str(cfg.get("rules.kinship.kin_mode", "ratio")),
            kin_ratio_mode=str(cfg.get("rules.kinship.ratio", "jaccard")),
        )
