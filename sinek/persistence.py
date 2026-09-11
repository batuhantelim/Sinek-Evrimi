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

from .agent import N_MOTORS, N_SENSORS
from .genome import Genome

FORMAT_VERSION = 2


def save_population(path: str, sim, note: str = "") -> str:
    """Simulasyonun mevcut populasyonunun genomlarini yazar."""
    agents = sim.agents
    if not agents:
        raise ValueError("kaydedilecek ajan yok (koloni tukenmis olabilir)")

    names = sorted(agents[0].genome.params)
    params = np.array([[a.genome.params[n] for n in names] for a in agents], dtype=np.float64)
    weights = np.array([a.genome.weights for a in agents], dtype=np.float32)
    lineage = np.array([a.genome.lineage for a in agents], dtype=np.int64)
    surname = np.array([a.genome.surname for a in agents], dtype=np.int64)
    fitness = np.array([a.fitness(sim.fitness_weights) for a in agents], dtype=np.float64)

    meta = {
        "format_version": FORMAT_VERSION,
        "brain_type": str(sim.cfg.get("brain.type", "reflex")),
        "brain_hidden": int(sim.cfg.get("brain.hidden", 0)),
        # Sensor/motor sayilari kayda yazilir: sozlesme buyudugunde eski
        # genomlar tasinabilsin diye (bkz. migrate_weights).
        "n_sensors": N_SENSORS,
        "n_motors": N_MOTORS,
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
        surname=surname,
        fitness=fitness,
        meta=json.dumps(meta),
    )
    return path


def migrate_weights(
    weights: np.ndarray, old_n: int, old_m: int, hidden: int, new_n: int, new_m: int
) -> np.ndarray:
    """Sensor/motor sozlesmesi buyudugunde eski rnn agirliklarini tasir.

    Yeni sensor sutunlari ve yeni motor satirlari SIFIR baslar: ag baslangicta
    yeni girdiyi gormez, yeni ciktiyi surmez -> davranis birebir korunur.
    Mutasyon zamanla bu baglantilari acar. Faz 2'nin kazananlari boylece
    Faz 3'e kaybolmadan gecer.
    """
    if new_n < old_n or new_m < old_m:
        raise ValueError(
            f"sozlesme kucultulmus ({old_n}->{new_n} sensor, {old_m}->{new_m} motor); "
            "kucultme tasimasi desteklenmiyor"
        )
    out = np.zeros((weights.shape[0], hidden * new_n + hidden * hidden + hidden + new_m * hidden + new_m), dtype=np.float32)
    for row, w in enumerate(weights):
        i = 0
        W_ih = w[i : i + hidden * old_n].reshape(hidden, old_n); i += hidden * old_n
        W_hh = w[i : i + hidden * hidden]; i += hidden * hidden
        b_h = w[i : i + hidden]; i += hidden
        W_ho = w[i : i + old_m * hidden].reshape(old_m, hidden); i += old_m * hidden
        b_o = w[i : i + old_m]

        new_ih = np.zeros((hidden, new_n), dtype=np.float32)
        new_ih[:, :old_n] = W_ih
        new_ho = np.zeros((new_m, hidden), dtype=np.float32)
        new_ho[:old_m] = W_ho
        new_bo = np.zeros(new_m, dtype=np.float32)
        new_bo[:old_m] = b_o
        out[row] = np.concatenate(
            [new_ih.ravel(), W_hh, b_h, new_ho.ravel(), new_bo]
        )
    return out


def _infer_shape(meta: dict, total: int) -> tuple[int, int, int]:
    """Kayittaki (n_sensors, n_motors, hidden). v1 kayitlarda cikarim yapilir."""
    hidden = int(meta.get("brain_hidden", 0))
    if "n_sensors" in meta and "n_motors" in meta:
        return int(meta["n_sensors"]), int(meta["n_motors"]), hidden
    # format_version 1: sensor/motor sayisi yazilmamis. O donemde motor sayisi
    # 4'tu; sensor sayisi genom boyutundan geri cozulur.
    m = 4
    rest = total - hidden * hidden - hidden - m * hidden - m
    if hidden <= 0 or rest <= 0 or rest % hidden:
        raise ValueError(f"eski kaydin sensor sayisi cozulemedi (toplam {total}, hidden {hidden})")
    return rest // hidden, m, hidden


def load_population(
    path: str, cfg=None, top: int | None = None, migrate: bool = True
) -> tuple[list[Genome], dict]:
    """Genomlari geri yukler. `top` verilirse en iyi N genomu dondurur.

    cfg verilirse beyin tipi/boyutu uyusmazligi ERKEN yakalanir. Sensor/motor
    sozlesmesi buyumusse (Faz 2 -> Faz 3) agirliklar otomatik tasinir; ne
    yapildigi meta['migrated'] icinde raporlanir — sessizce genom degistirmek
    tam olarak gizlenmemesi gereken seydir.
    """
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(str(data["meta"]))
        params = data["params"]
        weights = data["weights"]
        lineage = data["lineage"]
        fitness = data["fitness"]
        surname = data["surname"] if "surname" in data.files else np.zeros(len(lineage), np.int64)

    meta["migrated"] = None
    if cfg is not None:
        want = str(cfg.get("brain.type", "reflex"))
        if meta["brain_type"] != want:
            raise ValueError(
                f"kayit '{meta['brain_type']}' beyni icin uretilmis, config '{want}' istiyor"
            )
        from .brains import genome_size_for

        need = genome_size_for(cfg)
        have = int(weights.shape[1]) if weights.ndim == 2 else 0
        if need != have and have > 0:
            old_n, old_m, hidden = _infer_shape(meta, have)
            if hidden != int(cfg.get("brain.hidden", hidden)):
                raise ValueError(
                    f"gizli noron sayisi uyusmuyor: kayitta {hidden}, config "
                    f"{cfg.get('brain.hidden')} istiyor — tasima desteklemiyor"
                )
            if not migrate:
                raise ValueError(f"agirlik sayisi uyusmuyor: kayitta {have}, config {need} istiyor")
            weights = migrate_weights(weights, old_n, old_m, hidden, N_SENSORS, N_MOTORS)
            if weights.shape[1] != need:
                raise ValueError(f"tasima sonrasi boyut tutmadi: {weights.shape[1]} != {need}")
            meta["migrated"] = {
                "sensors": [old_n, N_SENSORS],
                "motors": [old_m, N_MOTORS],
                "new_weights_zeroed": need - have,
            }

    order = np.argsort(-fitness, kind="stable")
    if top is not None:
        order = order[: max(1, top)]

    names = list(meta["param_names"])
    genomes = [
        Genome(
            params={n: float(v) for n, v in zip(names, params[i])},
            weights=np.asarray(weights[i], dtype=np.float32).copy(),
            lineage=int(lineage[i]),
            surname=int(surname[i]),
        )
        for i in (int(k) for k in order)
    ]
    return genomes, meta
