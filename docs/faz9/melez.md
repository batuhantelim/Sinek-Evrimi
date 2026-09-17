# Faz 9 bileşen 1 — melez soyisim: mekanik çalıştı, ölçüm zeminini yedi

Ölçüt koşumlardan önce yazıldı: **[olcut.md](olcut.md)**.

Faz 8 ölçülebilir bir çeşitlilik zemini kurmuştu (etkin soy 4.4–15.1, dış-grup
fırsat payı %11.9–49.8). Faz 9'un ilk bileşeni o zemine **melez soyisim**
ekliyor: iki saf soydan doğan çocuk birleşik `{X,Y}` etiketi alır.

**Sonuç iki parçalı:**

1. **Melez dışlanmıyor da, köprü de olmuyor — FARK YOK, 3/3 seed.**
2. **⚠ Ama mekanik kendi ölçüm zeminini yiyor**: melez payı doyuma kadar
   tırmanıyor (%0 → %53–78) ve "yabancı" kategorisi eriyor (dış-grup payı
   %49.7 → %31.0, %11.9 → %1.8, %16.2 → %6.6). Zemin ölçütü **1/3 seed**.

Bu ikincisi, bileşen 2 ve 3'ün (soy-arası matris, işbirliği kontrolü) **bu
mekanik üzerine kurulamayacağı** anlamına geliyor — kurulsaydı Faz 5/6'nın
hatası (ölçülemez zeminde sosyal ölçüm) tekrarlanırdı.

---

## 1. Mekanik: salt etiket, enerjiye dokunmaz

- **Üreme aseksüel kalıyor**; genom **tek** ebeveynden gelir. Melezlik yalnızca
  soyağacı etiketini iki bileşenli yapar.
- **Akrabalık = en az bir ortak bileşen** (`sinek/lineage.py`). Tek bileşenli
  etiketlerde tam eşitliğe indirgenir → Faz 3–8 davranışı birebir korunur.
- **Yalnızca iki SAF soy melezleşir**; ebeveyn zaten melezse çocuk etiketi aynen
  miras alır ("melez saf döller"). Etiket en fazla iki bileşen taşır.
- **Enerji defterine dokunmaz**: ikinci ebeveyn hiçbir şey ödemez/almaz. Test
  üreme öncesi/sonrası enerji farkının iki kolda birebir aynı olduğunu
  sabitler; `energy_created` = 9/9 koşumda 0.
- `rate = 0.0`'da hiçbir rastgele çekim yok → Faz 1–8 `state_hash` korunur.

### Melez bir SINIF değildir

`test_hybrid_is_not_a_hardcoded_class` sosyal döngüde melezliğin **tek bir
ölçüm değişkenine** okunduğunu ve hiçbir karar dalına (`if`/`elif`/`while`)
girmediğini denetler. Testin ilk sürümü kodu yakaladı (`if other.genome.is_hybrid`
sayaç için de olsa bir dal açıyordu) ve kod yeniden düzenlendi.

## 2. Kalibrasyon: melez payı oranla kontrol EDİLEMİYOR

Tam ufukta (12000 adım), `rate` taraması:

| `rate` | melez payı | dış-grup payı | etkin soy | ölçüt 2 |
|---|---|---|---|---|
| 0.005 | 53.3% | 31.0% | 21.60 | GEÇTİ |
| 0.01 | 65.1% | 38.8% | 16.50 | GEÇTİ |
| 0.02 | 50.9% | 19.8% | 11.89 | GEÇTİ |
| 0.05 | 73.0% | 31.4% | 26.95 | GEÇTİ |
| 0.10 | 86.2% | **6.2%** | 13.40 | GEÇMEDİ |
| 0.25 | 90.4% | **1.5%** | 17.37 | GEÇMEDİ |

**Doğumların yalnızca binde beşi melez olduğunda bile melez payı %53'e
çıkıyor.** Sebep, koşumdan önce yazdığımız kuralın kendisi: *melez saf döller*.
Bir melez hattı bir kez oluştu mu geri dönmüyor, üstelik saf soylar melez
üretmeye devam ediyor — yani melez payı **tek yönlü bir mandal (ratchet)**:

| dönem | 0 | 2 | 5 | 9 | 13 | 17 | 20 | 23 |
|---|---|---|---|---|---|---|---|---|
| seed 42 melez % | 0.0 | 3.2 | 9.1 | 23.5 | 31.8 | 45.0 | 55.0 | **55.5** |
| seed 7 melez % | 0.0 | 2.4 | 0.5 | 29.2 | 40.7 | 57.7 | 58.2 | **60.1** |
| seed 123 melez % | 0.0 | 1.8 | 17.8 | 37.1 | 41.4 | 63.1 | 72.9 | **77.7** |

`rate` yalnızca **ne kadar hızlı** doyduğunu belirliyor, doyup doymadığını
değil. En küçük geçen değer olan **0.005** pinlendi.

Son çeyrekte melez doğum sayısı ~0: doyum sonrası saf ebeveyn kalmadığı için
üretim kendiliğinden duruyor.

## 3. ⚠⚠ Asıl bulgu: melezlik "yabancı" kategorisini eritiyor

Akrabalık "en az bir ortak bileşen" olduğu için, popülasyonun yarısı melezken
neredeyse herkes neredeyse herkese akraba oluyor. Dış-grup fırsat payı,
melez payı yükseldikçe çöküyor:

| dönem | 0 | 5 | 9 | 13 | 17 | 20 | 23 |
|---|---|---|---|---|---|---|---|
| s42 dış-grup % | 16.3 | 26.7 | 34.7 | 39.8 | 35.9 | 34.8 | **25.4** |
| s7 dış-grup % | 18.4 | 18.1 | 1.2 | 4.0 | 4.2 | 2.1 | **0.7** |
| s123 dış-grup % | 17.9 | 26.3 | 33.2 | 30.2 | 13.4 | 5.3 | **5.1** |

Melez-yok koluna karşı, son çeyrek:

| seed | etkin soy | dış-grup payı | `genetic_r` | ölçüt 2 |
|---|---|---|---|---|
| 42 | 10.24 → 21.60 | 49.7% → **31.0%** | 0.42 → 0.54 (1.29×) | GEÇTİ |
| 7 | 4.43 → 2.42 | 11.9% → **1.8%** | 0.80 → 0.47 (0.59×) | **GEÇMEDİ** |
| 123 | 5.64 → 7.07 | 16.2% → **6.6%** | 0.74 → 0.57 (0.77×) | **GEÇMEDİ** |

**Ölçüt 2: 1/3.** Ölçüt 3 (`genetic_r` ≥ 0.5×) 3/3 geçti — akrabalık yapısı
yaşıyor, çöken şey **etiket düzeyinde yabancı bulabilme**.

⚠ Bu, ölçüt dosyasında önceden yazdığımız döngüsellik uyarısının gerçekleşmiş
hâli: melez etiket sayımda kendi grubu olduğu için `lineage_effective` **artıyor
görünüyor** (10.24 → 21.60) ama aynı anda dış-grup payı düşüyor. İki sayı zıt
yönde hareket ediyor; **etiket bolluğu ölçülebilirlik demek değil**.

## 4. Asıl soru: FARK YOK (3/3)

Enerji katmanlı, her seed kendi **karıştırma kontrolüne** karşı:

| seed | paylaş(melez−saf) | t | saldır(melez−saf) | t | paylaş(melez−yabancı) | t | karar |
|---|---|---|---|---|---|---|---|
| 42 | −0.0034 | −5.89 | −0.0079 | −2.01 | −0.0153 | −8.66 | FARK YOK |
| 7 | +0.0008 | −0.03 | −0.0188 | −5.30 | +0.0017 | −1.57 | FARK YOK |
| 123 | −0.0186 | −4.88 | −0.0035 | −0.45 | −0.0210 | −3.27 | FARK YOK |

- **DIŞLAMA 0/3** (paylaşım düşük *ve* saldırı yüksek gerekiyordu),
- **KÖPRÜ 0/3**,
- **FARK YOK 3/3**.

### Gözlem (ölçüt değil): melez daha az "hedef"

Sınıflandırma kutularına girmiyor ama bir örüntü var: melez akrabaya **hem**
paylaşım **hem** saldırı, saf akrabadan düşük (paylaşımda 2/3 seed t < −4,
saldırıda 2/3 seed t < −2). Yani melez ayrımcılığa uğramıyor; daha az
**etkileşim hedefi** oluyor. Bunu bir bulgu diye yazmıyoruz: ölçüt bu kategoriyi
tanımlamamıştı, ve 2/3 seed'de zemin ölçütü zaten geçmiyor.

## 5. Yan etkiler (üç kol, son çeyrek)

| seed | kol | melez% | etkin soy | dış-grup | `genetic_r` | N | topla/kişi | işbirliği | saldırı | E_yar |
|---|---|---|---|---|---|---|---|---|---|---|
| 42 | melez-yok | 0.0 | 10.24 | 49.7% | 0.415 | 634 | 0.0456 | 0.32% | 4.16% | 0 |
| 42 | melez | 53.3 | 21.60 | 31.0% | 0.537 | 648 | 0.0452 | 0.76% | 5.01% | 0 |
| 42 | karıştırma | 8.7 | 34.66 | 95.0% | 0.391 | 748 | 0.0370 | 0.25% | 1.57% | 0 |
| 7 | melez-yok | 0.0 | 4.43 | 11.9% | 0.798 | 571 | 0.0534 | 1.08% | 12.04% | 0 |
| 7 | melez | 59.7 | 2.42 | 1.8% | 0.470 | 613 | 0.0492 | 0.38% | 8.41% | 0 |
| 7 | karıştırma | 6.7 | 25.56 | 93.6% | 0.485 | 724 | 0.0402 | 0.65% | 4.57% | 0 |
| 123 | melez-yok | 0.0 | 5.64 | 16.2% | 0.739 | 613 | 0.0501 | 5.40% | 10.88% | 0 |
| 123 | melez | 74.1 | 7.07 | 6.6% | 0.571 | 608 | 0.0499 | 1.78% | 12.99% | 0 |
| 123 | karıştırma | 7.5 | 26.86 | 94.6% | 0.364 | 702 | 0.0414 | 1.27% | 4.63% | 0 |

Koloni sağlığı korunuyor (N ±%7, kişi başı toplama ≈ sabit), enerji korunumu
9/9 koşumda tam.

⚠ Karıştırma kolunda melez payı düşük (%6.7–8.7) çünkü etiketler her adım
permüte edilince "menzilde farklı soydan biri" koşulu farklı bireylerde tutuyor
ve melez hattı birikmiyor. Kontrol **bilgiyi** siliyor ama melez üretim hızını
da değiştiriyor — bu, kontrolün bilinen bir sınırı olarak yazılmalı.

## 6. Karar: bileşen 2 ve 3 bu zemine KURULMAZ

Ölçüt 2'nin 1/3 geçmesi, soy-arası ilişki matrisinin ve işbirliği kontrolünün
**şu hâliyle** ölçülemez bir zeminde okunacağı anlamına geliyor. Faz 5 ve Faz 6
tam olarak bu hatayla üretilmişti (etkin soy ~1, dış-grup %0.1–4.6) ve Faz 7'de
yeniden koşmak zorunda kaldık.

Bileşen 2–3'e geçmeden önce melez mekaniğinin **doyumunu** çözmek gerekiyor.
Denenmemiş üç seçenek (hiçbiri koşulmadı, sıra önerisidir):

1. **Melez saf dölleMEsin**: melez × saf → saf (etiket bir nesil sonra kaybolur).
   Melez payını düşük tutar; melez her zaman birinci nesil olur.
2. **Akrabalığı SÜREKLİ yap**: "en az bir ortak bileşen" yerine örtüşme oranı
   (0, ½, 1). Yarı-akraba yarı-yabancı olur, "yabancı" kategorisi tamamen
   erimez. CLAUDE.md §7'de zaten öngörülmüştü.
3. **Melezleşmeyi mekânsal olarak kıt tut** (menzili daralt) — ama Faz 4.6'da
   hareketi kısmanın koloniyi çökerttiği ölçülmüştü; dikkatli kalibrasyon ister.

## 7. Sınırlar — ne DEMİYORUZ

- **"Melezler ayrımcılığa uğramaz" demiyoruz.** 3/3 seed FARK YOK çıktı ama
  2/3 seed'de zemin ölçütü geçmiyordu; oralarda okunan hiçbir oran güvenilir
  değil. Güvenilir tek seed (42) de FARK YOK diyor — bu 1 seed'dir.
- **Melez mekaniğinin tek tasarımı denendi.** Yukarıdaki üç alternatif
  koşulmadı.
- **Bileşen 2 ve 3 hiç koşulmadı.** Faz 8'in işbirliği gözlemi (2/5 seed'de
  bandın üstü) hâlâ kontrolsüz bir gözlem olarak duruyor.
