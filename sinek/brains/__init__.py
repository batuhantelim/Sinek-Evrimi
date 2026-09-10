"""Beyin backend'leri.

Yeni bir backend eklemek icin: `Brain`'den turet, `@register("ad")` ile kaydet,
config'te `brain.type: ad` yaz. Simulasyonun geri kalanina dokunmak gerekmez.
"""

from .base import (  # noqa: F401
    Brain,
    brain_class,
    genome_size_for,
    make_brain,
    registered_brains,
)
from . import reflex, rnn  # noqa: F401  (kayit yan etkisi icin import edilir)
