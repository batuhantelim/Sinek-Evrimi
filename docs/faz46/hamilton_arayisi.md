# Faz 4.6 — korunumlu zeminde `r·b > c` aranması

Faz 4.5: Faz 3'ün "fedakârlık evrimleşti" sonucu, `need_bonus`'un alıcıya
verenin kaybından 4 kata kadar fazla **gerçek enerji** vermesinden doğan bir
artefakttı. Korunumlu zeminde fedakârlık 0/5 seed'de evrimleşti.

Bu faz sorar: **korunumu bozmadan** `r·b > c` sağlanabilir mi?

Ölçüt koşumlardan önce yazıldı: [olcut.md](olcut.md).
Zemin: Faz 4.5 ekolojisi (`need_mode: fitness`, çevre-sınırlı popülasyon,
bağlayıcı tavan yok). 15 sonda koşumu + 16 kontrollü evrim koşumu.

---

## 0. İki ölçüm tuzağı, ikisi de kapatıldı

### `r` etiketten okunamaz

`kin_assortment` **soyisim eşitliğini** ölçer. Ama aynı soyisim mutasyonla
ayrışır ve `split_rate` ile ayrılan iki soy, ayrılma anında genetik olarak
**aynıdır**. Hamilton eşitsizliği etiketle değil genomla çalışır. Yeni metrik:

```
genetic_r = Σ_k Cov(x_k^aktör, x_k^en yakın komşu) / Σ_k Var(x_k^aktör)
```

k genom **ağırlık** boyutları üzerinde. Rastgele eşleşmede 0, klonlarda 1
(birim testiyle doğrulandı).

### `b/c` varsayılamaz

`need_bonus` çarpanını muhasebeye koyup "bak, `b/c` = 2.3" demek **kendi
varsayımını ölçmektir**. Bu yüzden iki sütun ayrıldı:

| sütun | ne |
|---|---|
| `bc_ratio` | **ENERJİ** birimi. Korunumlu aktarımda yapısal olarak ≤ 1 |
| `bc_ratio_fit` | `need_bonus` çarpanlı **TAHMİN** — bir varsayım |

Ve asıl ölçüm `tools/hamilton_probe.py`: tamamlanmış yaşamlar üzerinde

```
yavru ~ 1 + yaş + yemek + VERİLEN + ALINAN
```

`b̂` = ALINAN katsayısı (birim enerji almak kaç yavru getirdi),
`ĉ` = −VERİLEN katsayısı. Yaş **ve** yemek kontrol edilir (Faz 4.5 dersi:
yaşlı ajan hem çok yer hem çok ürer; çok toplayan hem çok paylaşır hem çok ürer).

**Ölçüm, varsayımı çürüttü:** `bc_ratio_fit` 2.0–2.9 diyor, ölçülen `b/c`
0.64–1.48. Yani `need_bonus` varsayımı gerçek fitness faydasını **2–3 kat
fazla** tahmin ediyor.

---

## 1. Harita: 15 dürüst koşul, hiçbiri eşiği geçmiyor

Her koşumda enerji korunumu denetlendi: **15/15 TAMAM** (yaratılan enerji = 0).

| koşul | `r` | b/c enerji | b/c fit* | `b̂` | `ĉ` | **b/c ÖLÇÜLEN** | **`r·b/c`** |
|---|---|---|---|---|---|---|---|
| `BC2_taban100` | 0.745 | 0.787 | 2.046 | 0.0083 | 0.0131 | 0.638 | 0.475 |
| `BC4_taban100_R1` | 0.618 | 1.000 | 2.547 | 0.0086 | 0.0096 | 0.895 | 0.553 |
| `BC3_ikisi` | 0.750 | 1.000 | 2.592 | 0.0093 | 0.0114 | 0.818 | 0.614 |
| `R0` (taban) | 0.427 | 0.833 | 2.289 | 0.0161 | 0.0108 | **1.484** | 0.634 |
| `R1` | 0.553 | 0.832 | 2.308 | 0.0129 | 0.0104 | 1.249 | 0.691 |
| `R0_ovh0` | 0.552 | 0.998 | 2.713 | 0.0119 | 0.0091 | 1.315 | 0.726 |
| `R1_ovh0` | 0.586 | 0.999 | 2.718 | 0.0118 | 0.0092 | 1.273 | 0.746 |
| `R2` | 0.767 | 0.833 | 2.327 | 0.0126 | 0.0129 | 0.976 | 0.748 |
| `BC1_ovh0` | 0.751 | 1.000 | 2.786 | 0.0114 | 0.0104 | 1.091 | 0.819 |
| `BC7_pay15` | 0.748 | 1.000 | 2.873 | 0.0111 | 0.0098 | 1.130 | 0.845 |
| `BC5_kitlik` | 0.838 | 1.000 | 2.808 | 0.0115 | 0.0109 | 1.058 | 0.886 |
| `BC6_kucuk_pay` | 0.762 | 1.000 | 2.794 | 0.0101 | 0.0085 | 1.182 | 0.901 |
| `BC9_pay3_kit` | 0.836 | 1.000 | 2.807 | 0.0107 | 0.0098 | 1.096 | 0.917 |
| `BC8_pay15_kit` | 0.866 | 1.000 | 2.762 | 0.0107 | 0.0098 | 1.099 | 0.952 |
| **`BC10_pay1_kit`** | **0.892** | 1.000 | 2.839 | 0.0121 | 0.0110 | 1.109 | **0.989** |

\* varsayım, kanıt değil.

**`r·b/c` aralığı 0.475 – 0.989. 1'i geçen: 0/15.**

`b̂` ve `ĉ` her koşulda sıfırdan açıkça farklı (|t| = 10–70): almak gerçekten
yavru getiriyor, vermek gerçekten yavruya mal oluyor. Ölçüm zayıf değil;
**oran yetmiyor.**

## 2. Neden: `r` ile `b/c` birbirini yiyor

15 koşul üzerinde **korelasyon(r, b/c) = −0.514**
([hamilton_takas.png](hamilton_takas.png)).

Akrabaları uzamsal sıkıştırmak (`max_speed` ↓, `spawn_radius` ↓) `r`'yi
0.43 → 0.89'a çıkarıyor — **ama** aynı hamle komşuları birbirine benzer *ve*
benzer doygunlukta yapıyor, dolayısıyla bir transferin marjinal faydası
düşüyor: `b/c` 1.48 → 0.98. Net kazanç ×1.18, oysa `r` ×2.09 arttı.

Yapısal sınır de net: korunumlu aktarımda

```
c = amount + overhead ,  b = min(amount, alıcının boşluğu) ≤ amount
⇒ enerji b/c ≤ 1   (overhead = 0'da tam 1)
```

Ölçülen fitness `b/c`'nin 1'i biraz aşabilmesinin tek sebebi **azalan verimin
gerçek payı**: aynı enerji daha aç bir alıcıda biraz daha çok yavruya
dönüşüyor. Ama bu pay ölçüldüğünde yalnızca %10–48; `need_bonus` varsayımının
iddia ettiği %130–190 değil. `r ≤ 1` olduğu için `r·b/c > 1` ancak
`b/c > 1/r ≥ 1.12` (en iyi `r`'de) ile mümkün — ve yüksek `r`'de ölçülen
`b/c` tam olarak oraya, 1.10 civarına sıkışıyor.

## 3. Kaldıraçlar ne yaptı (biri beklentinin tersine)

| kaldıraç | niyet | ölçülen |
|---|---|---|
| `max_speed`/`spawn_radius` ↓ | `r` ↑ | ✅ `r` 0.43 → 0.89; ama `b/c` düştü |
| `overhead` 1.2 → 0 | `c` ↓ | ✅ enerji `b/c` 0.833 → 1.000 (yapısal tavan) |
| `amount` 8 → 1 | küçük transfer, boşluk israfı ↓ | ✅ ölçülen `b/c` 0.98 → 1.11–1.18 |
| kıtlık (yemek ×0.5) | aç alıcıda `b` ↑ | ✅ `r` da yükseldi (0.77 → 0.84) |
| **`min_donor_energy` 10 → 100** | yalnız zengin versin ⇒ `c` ↓ | ❌ **TERSİ**: `ĉ` 0.0129 → 0.0131, `b̂` 0.0126 → 0.0083, `b/c` 0.98 → **0.64** |

Son satır önemli: "yalnız tok olan versin" kuralı fedakârlığı ucuzlatmadı,
**faydayı** düşürdü — çünkü paylaşım fırsatları o eşiğin üstünde kalan, zaten
iyi durumdaki çiftlere daraldı. Kaldıracın ne yaptığını ölçmeseydim bunu ters
raporlayacaktım.

## 4. Asıl test: eşiğe en yakın noktalarda fedakârlık evrimleşiyor mu?

`r·b/c` bir **tahmindir**; karar kontrollü koşumda verilir.

### `BC10` (`r·b/c` = 0.989) — ölçülebilirlik şartını düşürdü

3 seed: dış-grup fırsat payı %3.0 / %8.3 / %8.9 — ölçüt %10 istiyordu.
Popülasyon 214–262'ye indi (kıtlık + sıkı mekân). Ayrışma 1/3.
**Bu koşul okunmaz**: eşiğe yaklaşmanın bedeli ölçülebilirliği kaybetmek oldu.

### `BC6` (`r·b/c` = 0.901) — ölçülebilir ama sinyal zayıf ve tutarsız

5 seed, her biri kendi soyisim-karıştırma kontrolüyle:

| seed | N | `r` | işbirliği | dış pay | `kin_bias_adj` | kontrol | `share_t` | ayrıştı | `atk_t` |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 643 | 0.759 | %1.36 | %19.9 | +0.65 | +0.07 | **+4.26** | EVET | −14.04 |
| 7 | 595 | 0.777 | %0.77 | %18.7 | +0.64 | +0.23 | **+6.98** | EVET | −10.35 |
| 42 | 659 | 0.789 | %0.89 | %14.5 | +0.13 | +0.33 | −2.66 | hayır | −10.21 |
| 123 | 581 | 0.760 | %1.43 | %20.5 | +0.63 | +0.26 | **+4.24** | EVET | −14.65 |
| 777 | 625 | 0.724 | %0.99 | %20.1 | +0.32 | +0.71 | −4.37 | hayır | −6.74 |

**Ayrışma 3/5** — ölçüt en az 2/3 (yani 4/5) istiyordu: **kaldı.**
İşbirliği ≥%1 şartını 2/5 seed sağlıyor: **kaldı.**
`share_t` +1.69 ± 4.92, iki seed'de belirgin **negatif**.

Etki büyüklüğü: `kin_bias_adj` asıl +0.48 puan, kontrol +0.32 — fark
**0.16 puan**. Faz 3'ün pompalı zemininde bu fark **+28 puandı**.

Korunum 5/5 koşumda tam (yaratılan enerji = 0).

---

## 5. Sonuç

**Bu minimal korunumlu sistemde akraba fedakârlığı için gereken `r·b > c`
ulaşılamıyor.** 15 dürüst koşulun hiçbiri eşiği geçmedi (en iyi 0.989) ve
eşiğe en çok yaklaşan koşul koloniyi ölçülemez hale getirdi. Ölçülebilir en iyi
noktada sinyal 5 seed'in 3'ünde ve 0.16 puan büyüklüğünde — önceden ilan edilen
ölçütü geçmiyor.

Hangi kolun tıkandığı da belli:

- **`b/c` kolu yapısal olarak tıkalı.** Korunumlu aktarımda enerji `b/c ≤ 1`;
  azalan verimin ölçülen gerçek payı yalnızca %10–48.
- **`r` kolu ekolojik olarak tıkalı.** 0.89'un üstüne çıkmak için hareketi daha
  da kısmak gerekiyor, o da koloniyi çökertiyor (`max_speed` 0.02'de N = 17).
- **İkisi aynı anda büyümüyor** (korelasyon −0.51).

## 6. Yan bulgu: düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor

`atk_t` 5/5 seed'de −6.7 ile −14.7 arasında: saldırı **yabancıya** yöneliyor,
güçlü ve tutarlı biçimde. Aynı koşumlarda fedakârlık ayrımı yok. Faz 4.5'in
yan bulgusu farklı bir koşulda tekrarlandı.

Bu, saldırının fedakârlıktan farklı bir muhasebesi olmasıyla tutarlı: saldırı
**alan** için net kazançtır (hedefin enerjisini alır), dolayısıyla `b/c`
tavanına çarpmaz. Ama bu bir hipotez; ölçülmedi.

## 7. Sınırlar — ne DEMİYORUZ

- **"Akraba fedakârlığı imkânsız" demiyoruz.** *Bu* mekanik repertuvarda —
  tek yönlü enerji aktarımı, en yakın komşu hedefi, hafızasız beyin —
  ulaşılamıyor. Misilleme, itibar, tekrarlı etkileşim, kısmi akrabalık
  (melez soyisim) veya grup seçilimi denenmedi.
- **15 koşul bir tarama, kapsamlı bir arama değil.** Taranmayan kaldıraçlar
  var (`kinship.radius`, `threshold`, dünya boyutu, `energy.max`).
- **Sonda tek seed'lidir (42).** `r·b/c` haritası yön için güçlü ama çok
  seed'de tekrarlanmadı; kontrollü evrim testi 3–5 seed'de yapıldı.
- **`b̂`/`ĉ` doğrusal bir yaklaşımdır.** Yavru sayısı sayımdır ve sıfır
  ağırlıklıdır; OLS eğimi yorumlanabilir ama tam model değildir.
