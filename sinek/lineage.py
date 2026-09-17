"""Soy etiketi mantigi: akrabalik ve etiket anahtari (Faz 9).

Ayri bir modul, cunku `agent`, `genome`, `metrics` ve `render` hepsi buna
ihtiyac duyuyor ve `genome` -> `brains` -> `agent` zinciri dairesel import
uretiyor. Burada hicbir proje modulu import edilmez.

MELEZLIK SALT ETIKETTIR: ureme aseksuel kalir, genom tek ebeveynden gelir.
Bu modul yalnizca "iki etiket akraba sayilir mi" ve "etiketin anahtari nedir"
sorularini tanimlar. Melezin nasil MUAMELE GORECEGI hicbir yerde yazmaz —
o evrimin isi, olcumun konusu.
"""

from __future__ import annotations


def label_key(surname: int, surname2: int) -> tuple[int, ...]:
    """Saf soyda `(X,)`, melezde sirali `(X, Y)`."""
    if surname2 < 0:
        return (surname,)
    return (surname, surname2) if surname <= surname2 else (surname2, surname)


def kin_labels(s1: int, t1: int, s2: int, t2: int) -> bool:
    """AKRABALIK: iki etiketin EN AZ BIR ortak bileseni var mi.

    Saf X ile melez {X,Y} akrabadir; {X,Y} ile {X,Z} akrabadir; {X,Y} ile saf Z
    yabancidir. Faz 3-8'de etiketler tek bilesenliydi (t = -1) ve bu tam
    esitlige indirgenir — eski davranis birebir korunur.
    """
    if t1 < 0 and t2 < 0:
        return s1 == s2
    if s1 == s2 or s1 == t2:
        return True
    return t1 >= 0 and (t1 == s2 or t1 == t2)
