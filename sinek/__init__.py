"""Sinek Evrimi — ajan tabanli yapay yasam (ALife) simulasyonu.

Faz 1: tek tip (klon) ajan + ortam + hareket + yemek.
Faz 2: genom mutasyonu + secilim (evolution.enabled: true).
Faz 3: sosyal kurallar (rules.share / rules.attack).
"""

__version__ = "0.1.0"

from .config import Cfg, load_config          # noqa: F401
from .simulation import Simulation            # noqa: F401
