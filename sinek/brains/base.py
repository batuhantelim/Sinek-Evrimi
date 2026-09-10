"""Beyin arayuzu ve kayit defteri (registry).

Sinek bedeni (`sinek/agent.py`) sensor vektorunu uretir, beyin motor vektorunu
dondurur. Beyin ile beden arasindaki tek sozlesme bu iki vektordur.

    sensors (float32, N_SENSORS)  ->  Brain.act()  ->  motors (float32, N_MOTORS)

Bu sozlesme sayesinde ileride tamamen farkli bir "beyin" takilabilir:
kucuk bir recurrent sinir agi (Faz 2), ya da opsiyonel bir connectome
backend'i (orn. FlyWire) — beden, dunya ve metrikler degismeden kalir.
Yeni backend `genome_size()` ile genomdan kac agirlik istedigini bildirir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np

_REGISTRY: dict[str, type["Brain"]] = {}


def register(name: str) -> Callable[[type["Brain"]], type["Brain"]]:
    def deco(cls: type["Brain"]) -> type["Brain"]:
        _REGISTRY[name] = cls
        cls.backend_name = name
        return cls

    return deco


def registered_brains() -> list[str]:
    return sorted(_REGISTRY)


class Brain(ABC):
    """Tum beyin backend'lerinin ortak arayuzu."""

    backend_name: str = "?"

    #: Bu backend'in genom parametrelerinden HANGILERINI okudugu.
    #: None = hepsi. Okunmayan parametreler davranisa etki etmez; genomda
    #: tasinmaya devam ederler ve secilim baskisi altinda olmadiklari icin
    #: yerlesik bir NOTR SURUKLENME (genetic drift) referansi olustururlar.
    uses_params: tuple[str, ...] | None = None

    def __init__(self, genome, cfg):
        self.genome = genome
        self.cfg = cfg

    @staticmethod
    def genome_size(cfg) -> int:
        """Bu backend'in genomdan bekledigi serbest agirlik sayisi."""
        return 0

    @abstractmethod
    def act(self, sensors: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """Sensor vektorunden motor vektoru uretir. Uzunluk = len(MOTOR_NAMES)."""

    def reset(self) -> None:
        """Ic durumu (recurrent state) sifirlar. Durumsuz beyinler icin no-op."""


def brain_class(cfg) -> type["Brain"]:
    name = cfg.get("brain.type", "reflex")
    if name not in _REGISTRY:
        raise KeyError(
            f"bilinmeyen brain.type={name!r}. Kayitli olanlar: {registered_brains()}"
        )
    return _REGISTRY[name]


def genome_size_for(cfg) -> int:
    """Secili backend'in genomdan bekledigi serbest agirlik sayisi.

    Genom uretimi (sinek/genome.py) bunu okur; beyin degistiginde genom
    boyutu kendiliginden dogru olur.
    """
    return int(brain_class(cfg).genome_size(cfg))


def make_brain(cfg, genome) -> Brain:
    return brain_class(cfg)(genome, cfg)
