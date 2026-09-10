"""Popülasyon kaydetme/yukleme (npz).

32 nesillik hesabin kosum bitince buharlasmamasi icin. Ayrica:
* evrimlesmis koloniyi acemi (rastgele) koloniyle ayni dunyada kiyaslamak,
* Faz 3'u Faz 2'nin kazananlariyla tohumlamak
icin gerekli.

Format sade tutuldu: agirlik matrisi + parametre isimleri/degerleri + meta.
"""

from __future__ import annotations

import json
import os

import numpy as np

from .genome import Genome

FORMAT_VERSION = 1


def save_population(path: str, sim, note: str = "") -> str:
    """Simulasyonun mevcut populasyonunun genomlarini yazar."""
    agents = sim.agents
    if not agents:
        raise ValueError("kaydedilecek ajan yok (koloni tukenmis olabilir)")

    names = sorted(agents[0].genome.params)
    params = np.array([[a.genome.params[n] for n in names] for a in agents], dtype=np.float64)
    weights = np.array([a.genome.weights for a in agents], dtype=np.float32)
    lineage = np.array([a.genome.lineage for a in agents], dtype=np.int64)
    fitness = np.array([a.fitness(sim.fitness_weights) for a in agents], dtype=np.float64)

    meta = {
        "format_version": FORMAT_VERSION,
        "brain_type": str(sim.cfg.get("brain.type", "reflex")),
        "brain_hidden": int(sim.cfg.get("brain.hidden", 0)),
        "seed": sim.seed,
        "step": sim.step_index,
        "generation": sim.generation,
        "param_names": names,
        "note": note,
    }

    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    np.savez_compressed(
        path,
        params=params,
        weights=weights,
        lineage=lineage,
        fitness=fitness,
        meta=json.dumps(meta),
    )
    return path


def load_population(path: str, cfg=None, top: int | None = None) -> tuple[list[Genome], dict]:
    """Genomlari geri yukler. `top` verilirse en iyi N genomu dondurur.

    cfg verilirse beyin tipi/boyutu uyusmazligi ERKEN yakalanir; yoksa hata
    ilk `make_brain` cagrisina kadar gizlenir.
    """
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(str(data["meta"]))
        params = data["params"]
        weights = data["weights"]
        lineage = data["lineage"]
        fitness = data["fitness"]

    if cfg is not None:
        want = str(cfg.get("brain.type", "reflex"))
        if meta["brain_type"] != want:
            raise ValueError(
                f"kayit '{meta['brain_type']}' beyni icin uretilmis, config '{want}' istiyor"
            )
        from .brains import genome_size_for

        need = genome_size_for(cfg)
        have = int(weights.shape[1]) if weights.ndim == 2 else 0
        if need != have:
            raise ValueError(
                f"agirlik sayisi uyusmuyor: kayitta {have}, config {need} istiyor "
                f"(brain.hidden={cfg.get('brain.hidden')})"
            )

    order = np.argsort(-fitness, kind="stable")
    if top is not None:
        order = order[: max(1, top)]

    names = list(meta["param_names"])
    genomes = [
        Genome(
            params={n: float(v) for n, v in zip(names, params[i])},
            weights=np.asarray(weights[i], dtype=np.float32).copy(),
            lineage=int(lineage[i]),
        )
        for i in (int(k) for k in order)
    ]
    return genomes, meta
