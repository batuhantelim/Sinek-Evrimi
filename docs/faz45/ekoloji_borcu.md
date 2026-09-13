# Faz 4.5 — ekoloji borcu: paylaşım enerji yaratıyordu

Tanı, popülasyonu çevrenin değil `agents.max_count`'un sınırladığını göstermişti.
Bu fazın amacı zinciri onarmaktı: **enerji → üreme → seçilim**. Onarırken borcun
tahmin ettiğimden derin olduğu çıktı.

---

## 0. Önce bir ölçüm hatamın düzeltmesi

Tanıda "yemek 16.7× kısıldığında popülasyon yine 700" demiştim. Yenilenme iki
terimden gelir ve ben yalnızca birini ölçeklemiştim:

```
food += regrowth_rate · food · (1 − food/cap)
food += seed_rate · cap            ← taban, koşulsuz, her adım
```

`seed_rate` yerinde kalınca gerçek girdi 62.1 → 15.0 birim/adım, yani
**16.7× değil 4.1×** düştü. Bulgunun yönü doğruydu, büyüklüğü yanlıştı.
Bu fazda iki terim birlikte ölçeklendi.

| `regrowth_rate` | `seed_rate` | girdi (birim/adım) | ≈ enerji/adım | çıplak metabolizmayla kaç sinek |
|---|---|---|---|---|
| 0.010 (varsayılan) | 0.0006 | 62.1 | 1367 | ~2136 |
| 0.0006 | 0.0006 | 15.0 | 331 | ~517 |
| 0.0006 | 0 | 3.0 | 66 | ~103 |

---

## 1. Asıl bulgu: paylaşım korunumlu değildi

Yemek arzını kısıp tavanı kaldırdığım ilk koşumda enerji defteri tutmadı:
5000 sineklik bir kolonide metabolizma 3000 enerji/adım isterken yenen yemek
53 enerji/adım idi — ama **ortalama enerji yükseliyordu**. 300 adımda ~900 bin
enerji yoktan var oluyordu.

Kaynak `need_bonus`:

```python
delivered = amount * (1.0 + need_bonus * need)   # 4×'e kadar
taken     = min(delivered, headroom)             # alıcıya GERÇEK enerji
other.energy += taken                            # veren yalnızca amount+overhead ödedi
```

"Alıcının dönüşüm verimi" diye belgelenen katsayı, alıcıya **vericinin
kaybettiğinden 4 kata kadar fazla enerji** veriyordu. Yani her paylaşım
koloniye net enerji **ekliyordu**.

### Pompanın büyüklüğü (son çeyrek, üretilen enerji / yenen yemek enerjisi)

| koşum | işbirliği | yenen (E/adım) | **üretilen (E/adım)** | oran |
|---|---|---|---|---|
| `tani_s42` | %4.4 | 618 | 44 | %7 |
| `taniD_s42` (tanının tabanı) | %10.1 | 616 | 74 | %12 |
| `tani_s777` | %90.0 | 438 | **422** | **%96** |
| `faz4_avci` | %97.2 | 178 | **569** | **%321** |

İşbirliği yükseldikçe pompa büyüyor; %90'ın üstünde koloni enerjisinin yarısı
ya da fazlası **yemekten değil paylaşımdan** geliyor. Tanının "kaçak havza"sı
(yumak) budur: paylaşım arttıkça yaratılan enerji artar, o da daha çok
paylaşımı besler. Ve sınırsız bir iç enerji kaynağı varken çevre bağlayıcı
olamaz — tavanın bağlaması da buradan.

### Düzeltme

`rules.share.need_mode` eklendi:

- **`fitness` (varsayılan, korunumlu)** — alıcı en fazla aktarılanın kendisini
  alır; çarpan yalnızca Hamilton muhasebesindeki `b`'ye girer. "Aynı kalori aç
  bir alıcıya daha değerlidir" bir **fitness** iddiasıdır, enerji yaratma izni
  değil.
- **`energy`** — eski davranış. Silinmedi: Faz 3 adım 1.5 – Faz 4 tanısı arası
  bütün sonuçlar bu modda üretildi ve tek komutla yeniden üretilebilmeli.
  Deney dosyalarına açıkça pinlendi.

`energy_created` sayacı eklendi; korunumlu modda tam olarak 0 olmalı ve
`tests/test_phase3.py` bunu bekliyor. Bilinmeyen bir `need_mode` `ValueError`
atar.

⚠ **Not:** `fitness` modunda `need_bonus` **dinamiği hiç değiştirmez**, yalnızca
ölçümü değiştirir. Yani Faz 3 adım 1.5'in `b/c ≤ 1` tavanından kaçış yolu
kapanmıştır. Kaçışın kendisi azalan verim değil, enerji üretimiymiş.

---

## 2. Bölüm 1 — çevresel sınırlama

Ölçüt koşumlardan **önce** yazıldı: [olcut_BOLUM1.md](olcut_BOLUM1.md).

Yemek arzı ölçeği `s` (iki terim birlikte), `max_count = 5000`, korunumlu
paylaşım, seed 42:

| yemek ölçeği | N (son yarı) | VK | doluluk | tavanda |
|---|---|---|---|---|
| ×0.25 | 215 | %84 | 0.214 | %0.0 |
| ×0.40 | 337 | %56 | 0.217 | %0.0 |
| ×0.60 | 450 | %14 | 0.213 | %0.0 |
| **×1.00 (değişmedi)** | **750** | %2.3 | 0.213 | **%0.0** |

**Yemek arzını hiç değiştirmeye gerek kalmadı.** Pompa kalkınca varsayılan
dünya kendiliğinden N ≈ 750'de dengeleniyor — eski tavan 700'e şaşırtıcı
biçimde yakın. N'in yemek arzına doğru orantılı yanıt vermesi (215/337/450/750)
çevresel sınırlamanın doz-yanıt kanıtı.

5 seed'de (1, 7, 42, 123, 777):

| seed | N (son yarı) | VK | tavanda | yanan üreme hakkı | ölçüt |
|---|---|---|---|---|---|
| 42 | 750 | %2.3 | %0.0 | 0.0 | geçti |
| 1 | 696 | %2.6 | %0.0 | 0.0 | geçti |
| 7 | 764 | %2.9 | %0.0 | 0.0 | geçti |
| 123 | 769 | %3.9 | %0.0 | 0.0 | geçti |
| 777 | 749 | %3.2 | %0.0 | 0.0 | geçti |

**5/5.** Eskiden adımların %99.4'ü tavanda ve adım başına ~456 üreme hakkı
yanıyordu; şimdi %0.0 ve 0. Ölümler açlık (%20–24) ve yaşlılık (%17–37)
arasında paylaşılıyor. Popülasyon sönümlenen bir boom–bust ile plato yapıyor
([populasyon_karsilastirma.png](populasyon_karsilastirma.png)).

---

## 3. Bölüm 2 — seçilim zinciri onarıldı mı?

`tools/selection_probe.py` **tamamlanmış yaşamları** (ölüm anındaki kayıt)
toplar ve sorar: çok toplayan gerçekten çok mu üredi? Yaş kontrol edilmeli —
yaşlı ajan hem çok yer hem çok ürer.

| ölçüm | eski (tavan + pompa) | yeni (çevresel + korunumlu) |
|---|---|---|
| adım başına yanan üreme hakkı | 421.9 | **0.0** |
| adım başına yaratılan enerji | 207.7 | **0.0** |
| hiç üremeyen yetişkin payı | %67.1 | %43.8 |
| yemek → yavru (ham) | +0.317 | +0.692 |
| **yemek → yavru (yaş kontrollü)** | **+0.047** | **+0.738** |
| eğim (yavru / yemek birimi) | 0.053 | 0.078 |
| VERMEK → yavru (yaş kontrollü) | +0.096 | +0.143 |
| **VERMEK → yavru (yaş + YEMEK kontrollü)** | **+0.114** | **−0.080** |
| ALMAK → yavru (yaş + yemek kontrollü) | +0.437 | +0.319 |

İki şey çıkıyor:

1. **Zincir gerçekten kırıkmış ve onarıldı.** Yaş kontrollü "yemek → yavru"
   bağı **+0.047 → +0.738**. Eski kurulumda çok toplamak üremeye neredeyse hiç
   dönüşmüyordu: yetişkinlerin üçte ikisi hiç üremiyordu, çünkü üreme bir slot
   kuyruğuydu. Ham korelasyon (+0.317) bunu gizliyordu; yaş kontrolü açığa
   çıkardı.
2. **Eski kurulumda VERMEK kârlıydı.** Yaş *ve* servet kontrol edildiğinde
   bile paylaşan daha çok üremişti (+0.114). "Paylaşım ödüllendirilmez"
   kuralı kodda ihlal edilmiyordu ama **sonuçta ihlal oluyordu**: pompa
   vericiyi de kârlı çıkarıyordu. Korunumlu kurulumda bu bağ **−0.080**'e
   dönüyor, yani paylaşmak artık gerçekten maliyetli. Almak ise hâlâ kârlı
   (+0.319) — beklenen.

⚠ Yalnızca yaş kontrol edilirse "VERMEK → yavru" iki kurulumda da pozitif
görünür (+0.096 / +0.143). Servet de kontrol edilmeden bu satır okunamaz:
çok toplayan hem çok paylaşır hem çok ürer.

---

## 4. Bölüm 3 — Faz 3'ün ana bulgusu temiz zeminde TEKRARLANMADI

Aynı rejim (r_azalan + `need_bonus=3` + attack), yeni ekoloji, 5 seed, her biri
kendi soyisim-karıştırma kontrolüyle. Ölçüt Faz 3'ten devralındı: **`kin_bias_adj`
kendi kontrolünden Welch t > 2 ile ve doğru yönde ayrışmalı.**

| seed | paylaş iç | paylaş dış | `kin_bias_adj` | kontrol | `share_t` | ayrıştı mı | `atk_t` |
|---|---|---|---|---|---|---|---|
| 1 | %1.09 | %1.07 | +0.43 | +1.69 | −5.93 | hayır | −6.09 |
| 7 | %2.40 | %0.56 | +1.87 | +2.22 | −2.28 | hayır | −1.52 |
| 42 | %1.27 | %0.29 | +1.07 | +2.57 | −12.27 | hayır | −10.75 |
| 123 | %1.67 | %0.34 | +1.44 | +1.83 | −3.20 | hayır | −7.98 |
| 777 | %1.67 | %0.36 | +1.54 | +1.40 | +0.77 | hayır | −5.20 |

**0/5 seed.** `kin_bias_adj` asıl kolda +1.27 ± 0.55 puan, kontrolde
+1.94 ± 0.46 — yani kontrol *daha yüksek*. Karşılaştırma:

| | eski zemin (Faz 3, 5 seed) | temiz ekoloji (5 seed) |
|---|---|---|
| ayrıştı | **5/5** | **0/5** |
| `kin_bias_adj` asıl | +28.02 ± 10.05 | +1.27 ± 0.55 |
| `kin_bias_adj` kontrol | +0.39 ± 0.15 | +1.94 ± 0.46 |
| Welch t | +10.75 ± 5.33 | −4.58 ± 4.92 |

Yani **sonuç (c)**: Faz 3'ün "akrabaya yönelik in-grup fedakârlık evrimleşti"
bulgusu, paylaşımın enerji ürettiği bir dünyanın özelliğiymiş. Paylaşım oranı
%1.1–2.4'e düşüyor — Faz 3 adım 1'in (need_bonus = 0) sonucuyla aynı yere.

Ham iç/dış oranı 4 seed'de hâlâ 1'in üstünde (ör. %2.40 / %0.56 = 4.3×). Ama
projenin kendi disiplini bunu kanıt saymıyor: enerji katmanlı ve kontrole
karşı okunan ölçü hayır diyor. Bu tam olarak `kin_bias`'in tek başına neden
kanıt olmadığının bir örneği.

**Yan bulgu:** saldırı bu zeminde yabancıya yöneliyor (`atk_t` 5 seed'in 4'ünde
−2'nin altında, en güçlüsü −10.75). Yani temiz ekolojide *düşmanlık* ayrım
gözetiyor, *fedakârlık* gözetmiyor. Bu bir gözlem; Faz 4 adım 1'in avcı
sorularıyla birlikte yeniden kurulmadan yorumlanmamalı.

---

## 5. Hangi eski sonuçlar etkilendi?

| sonuç | mod | durum |
|---|---|---|
| Faz 1, Faz 2 | paylaşım yok | **etkilenmedi** |
| Faz 3 adım 1 (fedakârlık evrimleşmedi) | `need_bonus = 0`, korunumlu | **etkilenmedi** — ve artık genel sonuç bu |
| Faz 3 adım 1.5 (`b/c` tavanı) | yapısal argüman | **geçerli**; ama "kaçış"ın azalan verim değil enerji üretimi olduğu anlaşıldı |
| Faz 3 adım 2, sağlamlık, eksen A, eksen B | `energy` modu | iç karşılaştırmaları (kol vs kendi kontrolü) kendi dünyalarında geçerli; **fedakârlık bulgusu temiz zeminde tekrarlanmadı** |
| Faz 4 adım 1 (avcı) | `energy` modu | aynı uyarı. Avcı sonuçları negatifti; temiz zeminde **yeniden kurulmalı** |
| Faz 4 tanı (rejim çatalı) | `energy` modu | çatalın **mekanizması** artık biliniyor: enerji pompası. Kaçak havza korunumlu modda görünmüyor (işbirliği %1–2'de kalıyor) |

---

## 6. Sınırlar — ne DEMİYORUZ

- **"Akrabaya fedakârlık bu simülasyonda imkânsız" demiyoruz.** Korunumlu bir
  dünyada `b/c ≤ 1` enerji biriminde yapısaldır; ama fitness biriminde ölmek
  üzere olan bir alıcının kazancı çok daha büyük olabilir. Sonda bunu
  destekliyor: ALMAK → yavru bağı korunumlu kurulumda bile +0.319. Fedakârlığın
  evrimleşmesi için gereken şey bu kanalın **seçilime görünür** olması; bunu
  test etmek ayrı bir iş.
- **"Yeni ekoloji her müdahale altında kararlı" demiyoruz.** 5 seed, müdahalesiz,
  12000 adım. Avcı ya da gruplar arası rekabet eklenince ölçüt yeniden
  denetlenmeli.
- **Bölüm 3 tek rejimdir.** Faz 3'ün dersi: tek rejim sonuç değildir. "Temiz
  zeminde fedakârlık evrimleşmiyor" iddiası çevre süpürülmeden genellenemez.
- Yaşam kayıtları tek seed'den (42). Bölüm 2'nin sayıları yön için güçlü ama
  çok seed'de tekrarlanmadı.
