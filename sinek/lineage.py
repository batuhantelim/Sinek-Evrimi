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


#: `kin_ratio` icin gecerli formuller. Bilinmeyen deger sessizce varsayilana
#: dusmez; cagiran taraf kurulumda dogrular ve yuksek sesle patlar.
RATIO_MODES = ("jaccard", "mean")


def kin_ratio(s1: int, t1: int, s2: int, t2: int, mode: str = "jaccard") -> float:
    """SUREKLI AKRABALIK: paylasilan bilesen orani, 0.0–1.0.

    Iki formul (docs/faz9/olcut_surekli.md'de koşumlardan once ilan edildi):

    * ``jaccard`` : |kesisim| / |birlesim|
    * ``mean``    : |kesisim| / (ortalama etiket boyu)

    Tek bilesenli (saf) etiketlerde IKISI DE eski ikili degere indirgenir:
    ayni soy 1.0, farkli soy 0.0. Faz 1-8'in davranisi bu yuzden birebir
    korunur (test zorlar).

    ⚠ BU BIR OLCUDUR, DAVRANIS KURALI DEGIL. Deger sensore HAM girer; hicbir
    yerde "r > x ise paylas" diye bir esik yoktur. Analizde kullanilan
    dis-grup esigi (`rules.kinship.out_threshold`) yalnizca SINIFLANDIRMA
    icindir ve ajanin kararina girmez.
    """
    if t1 < 0 and t2 < 0:               # iki saf soy: eski ikili davranis
        return 1.0 if s1 == s2 else 0.0
    na = 1 if t1 < 0 else 2
    nb = 1 if t2 < 0 else 2
    inter = 0
    if s1 == s2 or (t2 >= 0 and s1 == t2):
        inter += 1
    if t1 >= 0 and (t1 == s2 or (t2 >= 0 and t1 == t2)):
        inter += 1
    if inter == 0:
        return 0.0
    if mode == "jaccard":
        return inter / (na + nb - inter)
    if mode == "mean":
        return 2.0 * inter / (na + nb)
    raise ValueError(
        f"bilinmeyen akrabalik formulu: {mode!r} ({' | '.join(RATIO_MODES)})"
    )
