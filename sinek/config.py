"""Konfigurasyon yukleme.

`config.yaml` tek dogru kaynaktir. Kullanici kismi bir YAML verirse eksik
anahtarlar varsayilandan derin-birlestirme (deep merge) ile tamamlanir, boylece
kod degistirmeden deney yapilabilir.
"""

from __future__ import annotations

import copy
import os
from typing import Any, Iterator

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(REPO_ROOT, "config.yaml")


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _coerce(text: str) -> Any:
    """'0.01' -> 0.01, 'true' -> True, 'abc' -> 'abc', '[1, 2]' -> [1, 2]."""
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return text


class Cfg:
    """Nokta ve koseli parantez ile erisilebilen ic ice sozluk sarmalayicisi."""

    __slots__ = ("_d",)

    def __init__(self, data: dict | None = None):
        object.__setattr__(self, "_d", data if data is not None else {})

    # --- okuma ---------------------------------------------------------
    def __getattr__(self, key: str) -> Any:
        d = object.__getattribute__(self, "_d")
        if key not in d:
            raise AttributeError(f"config anahtari yok: {key!r}")
        v = d[key]
        return Cfg(v) if isinstance(v, dict) else v

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return key in self._d

    def __iter__(self) -> Iterator[str]:
        return iter(self._d)

    def keys(self):
        return self._d.keys()

    def items(self):
        return ((k, Cfg(v) if isinstance(v, dict) else v) for k, v in self._d.items())

    def get(self, dotted: str, default: Any = None) -> Any:
        """cfg.get('world.food.regrowth_rate', 0.0) seklinde noktali erisim."""
        node: Any = self._d
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return Cfg(node) if isinstance(node, dict) else node

    # --- yazma ---------------------------------------------------------
    def __setattr__(self, key: str, value: Any) -> None:
        self._d[key] = value

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node = self._d
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                raise KeyError(f"{dotted}: {part} bir sozluk degil")
        node[parts[-1]] = value

    # --- yardimcilar ---------------------------------------------------
    def to_dict(self) -> dict:
        return copy.deepcopy(self._d)

    def dump(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(self._d, fh, allow_unicode=True, sort_keys=False)

    def __repr__(self) -> str:
        return f"Cfg({sorted(self._d)})"


def load_config(path: str | None = None, overrides: list[str] | None = None) -> Cfg:
    """Varsayilan config.yaml uzerine kullanici dosyasini ve CLI override'lari bindirir.

    overrides: ["world.food.regrowth_rate=0.02", "agents.initial_count=300"]
    """
    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    if path and os.path.abspath(path) != os.path.abspath(DEFAULT_CONFIG_PATH):
        with open(path, "r", encoding="utf-8") as fh:
            user = yaml.safe_load(fh) or {}
        data = _deep_merge(data, user)

    cfg = Cfg(data)
    for item in overrides or []:
        if "=" not in item:
            raise ValueError(f"--set bicimi 'anahtar.yol=deger' olmali, alinan: {item!r}")
        key, _, raw = item.partition("=")
        cfg.set(key.strip(), _coerce(raw.strip()))
    return cfg
