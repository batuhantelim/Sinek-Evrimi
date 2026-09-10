"""Beyin backend'leri.

Yeni bir backend eklemek icin: `Brain`'den turet, `@register("ad")` ile kaydet,
config'te `brain.type: ad` yaz. Simulasyonun geri kalanina dokunmak gerekmez.
"""

from .base import Brain, make_brain, registered_brains  # noqa: F401
from . import reflex  # noqa: F401  (kayit yan etkisi icin import edilir)
