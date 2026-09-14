# Faz 8 — çeşitlilik koruması: yoğunluğa bağlı seçilim

Ölçüt koşumlardan önce yazıldı: **[olcut.md](olcut.md)**.

Faz 7 ölçtü: güçlü yönlü seçilim soy çeşitliliğini siliyor ve göçmen enjeksiyonu
bunu çözmüyor (0/6 koşul). Sosyal mekanikler çeşitlilik olmadan ölçülemez, yani
çeşitliliği korumak sonraki her şeyin önkoşulu.

**Sonuç: yoğunluğa bağlı seçilim süpürgeyi durduruyor — 4/5 seed, ölçütün
dört parçasını birden geçerek, koloniyi çökertmeden.** Karıştırma kontrolü
0/5, üstelik *daha fazla* enerji gideri ödeyerek: mekanizma ekstra bir yük
değil, **etiket bilgisi** üzerinden çalışıyor.

---

## 1. Mekanik: çevre kuralı, davranış değil

`rules.crowding`: bir ajan, menzilindeki **aynı etiketli** komşu sayısıyla
orantılı ek metabolik gider öder.

```
gider = cost × (menzildeki aynı etiketli komşu sayısı)
```

Nadir olan ucuz yaşar — negatif frekans bağımlılığı, çeşitliliği koruyan
bilinen en güçlü mekanizmalardan biri.

Projenin kurallarına uyum:

- **Hiçbir soy adıyla hedeflenmez.** Ceza yalnızca yerel frekansa bakar. Bütün
  soyisimler tutarlı biçimde yeniden adlandırıldığında ceza dağılımı **birebir
  aynı** kalır (`test_crowding_is_lineage_blind`).
- **Bir GİDERdir, kaynak değil.** Toplam enerji tam olarak `crowding_drain`
  kadar düşer (`test_crowding_only_destroys_energy`); paylaşımın korunumuna
  dokunmaz — `energy_created` 15/15 koşumda 0.
- **`cost = 0`'da hiçbir şey değişmez**: Faz 1–7 `state_hash`'leri birebir
  korunur (`test_zero_cost_is_byte_identical`).

### ⚠ Test bir hata yakaladı

`_spawn` `crowd_label`'ı genomdan okuyor, ama **kurucular sonradan** yeniden
adlandırılıyor (`a.genome.surname = i`). Düzeltilmeseydi bütün kurucular aynı
etiketi taşıyacak ve ceza "herkes aynı soydan" diye hesaplanacaktı — kaldıraç
sessizce yanlış şeyi ölçerdi. Faz 6'daki "sessizce ölü mekanik"in aynısı,
bu kez testle önceden yakalandı.

## 2. Kalibrasyon: tam ufukta, ölçütü geçen EN KÜÇÜK değer

12000 adım, seed 42, taze zemin (`experiments/faz8_yogunluk.yaml`):

| `cost` | etkin soy | dış-grup | en büyük soy | N/taban | topla/taban | karar |
|---|---|---|---|---|---|---|
| 0.02 | 2.40 | 10.2% | 61.2% | 112% | 85% | GEÇMEDİ |
| 0.05 | 1.01 | 0.3% | 99.8% | 110% | 86% | GEÇMEDİ |
| 0.10 | 1.40 | 4.0% | 93.4% | 102% | 96% | GEÇMEDİ |
| 0.20 | 4.93 | 22.1% | 42.7% | 96% | 103% | GEÇMEDİ (etkin soy 4.93 < 5.0) |
| **0.30** | **10.24** | **49.7%** | **26.2%** | **100%** | **98%** | **GEÇTİ** |
| 0.40 | 6.93 | 24.9% | 40.5% | 92% | 110% | GEÇTİ |
| 0.60 | 13.03 | 42.3% | 25.7% | 94% | 108% | GEÇTİ |

`0.20` ikinci bir seed'de de geçmedi (3.10 / %9.4), yani eşiğin altında olduğu
doğrulandı. **0.30** deney dosyasına pinlendi.

⚠ 0.02–0.20 arası **tek düze değil** (2.40 → 1.01 → 1.40 → 4.93). Tek seed'de
ölçüldüğü için bu bir "eşik eğrisi" diye okunmamalı; söylenebilecek tek şey
0.30'un ölçütü geçen en küçük *taranmış* değer olduğudur.

## 3. Ana sonuç: 5 seed × 3 kol

| seed | taban | kaldıraç (0.30) | karıştırma kontrolü |
|---|---|---|---|
| 42 | 1.33 ❌ | **10.24 ✅** | 1.73 ❌ |
| 7 | 1.02 ❌ | 4.43 ❌ | 1.51 ❌ |
| 123 | 1.84 ❌ | **5.64 ✅** | 3.53 ❌ |
| 1 | 1.23 ❌ | **15.11 ✅** | 2.88 ❌ |
| 777 | 2.67 ❌ | **10.93 ✅** | 1.19 ❌ |
| **özet** | **0/5** | **4/5 GEÇTİ** | **0/5** |

(Ölçüt ≥2/3 istiyordu; 5 seed'de eşik 4.) Tek ıska seed 7 ve yalnızca **etkin
soy** yarısında (4.43 vs 5.0); dış-grup payı %11.9 ve en büyük soy %37.0 ile o
seed'de de iki ölçüt geçiyor.

### Süpürge gerçekten duruyor

En büyük soy payı — süpürgenin doğrudan imzası:

| seed | taban | kaldıraç |
|---|---|---|
| 42 | 92.8% | **26.2%** |
| 7 | 99.7% | **37.0%** |
| 123 | 86.7% | **44.9%** |
| 1 | 96.3% | **14.8%** |
| 777 | 52.5% | **28.8%** |

### ⚠⚠ Kontrol kritik olanı gösterdi: mekanizma BİLGİ, yük değil

Karıştırma kontrolünde ceza **karıştırılmış** etiketlerden hesaplanır: aynı
tür gider, sıfır bilgi. Ödenen gider kaldıraç kolundan **daha az değil**:

| seed | kaldıraç gideri | karıştırma gideri | karıştırma etkin soy |
|---|---|---|---|
| 42 | 56 594 | **83 551** | 1.73 |
| 7 | 59 989 | **79 963** | 1.51 |
| 123 | 60 889 | 52 597 | 3.53 |
| 1 | 48 458 | 51 750 | 2.88 |
| 777 | 42 444 | **102 253** | 1.19 |

Kontrol 3/5 seed'de kaldıraçtan **daha fazla** enerji yakıyor ve yine de
çeşitliliği korumuyor. Yani kaldıraç "seçilim baskısını zayıflattığı için"
değil, **kimin kalabalık olduğunu bildiği için** çalışıyor. Bu ayrım kontrol
olmadan yapılamazdı.

## 4. Ölçüt 4: koloni çökmedi — hatta toplama İYİLEŞTİ

| seed | N taban → kaldıraç | topla/kişi taban → kaldıraç |
|---|---|---|
| 42 | 634 → 634 | 0.0465 → 0.0456 |
| 7 | 743 → 571 | 0.0388 → **0.0534** |
| 123 | 733 → 613 | 0.0408 → **0.0501** |
| 1 | 741 → 594 | 0.0370 → **0.0498** |
| 777 | 706 → 632 | 0.0401 → **0.0467** |

Popülasyon %0–23 düşüyor (ölçüt ≤%50 düşüş istiyordu), ama **kişi başı toplama
4/5 seed'de yükseliyor** (%117–135). Yani ek gider koloniyi fakirleştirmiyor;
tek kültürün yerini alan çok soylu koloni kişi başına daha iyi topluyor.
Enerji korunumu 15/15 koşumda tam.

## 5. Döngüsellik denetimi: etiket mi, genom mu?

Kaldıraç doğrudan **etikete** bakıyor, yani etiket çeşitliliğinin yükselmesi
kısmen tanım gereği. Ölçüt dosyası bu yüzden iki ek şart koymuştu:

| seed | `weight_diversity` taban → kaldıraç | `genetic_r` taban → kaldıraç | oran |
|---|---|---|---|
| 42 | 0.3449 → 0.3674 ↑ | 0.517 → 0.415 | 0.80 |
| 7 | 0.3234 → 0.3180 ≈ | 0.435 → 0.798 | 1.83 |
| 123 | 0.3614 → 0.3831 ↑ | 0.559 → 0.739 | 1.32 |
| 1 | 0.3015 → 0.4692 ↑ | 0.324 → 0.666 | 2.06 |
| 777 | 0.5022 → 0.3345 ↓ | 0.775 → 0.440 | 0.57 |

- **`weight_diversity` düşmüyor**: 3/5 yükseliyor, 1 sabit, 1 düşüyor.
  Dürüst ifade: genom çeşitliliği **korunuyor**, güvenilir biçimde
  *artmıyor*.
- **`genetic_r` çökmüyor**: 5/5 seed'de tabanın yarısının üstünde (en düşük
  0.57×). Akrabalık yapısı yaşıyor — yani in/out ölçülebilir hale gelirken
  ölçülecek akrabalık yok olmadı. `kin_assortment` da benzer (0.418–0.839,
  hiçbirinde sıfıra inmiyor).

Her iki döngüsellik şartı da geçti.

## 6. Gözlem (ÖLÇÜT DEĞİL): işbirliği bazı seed'lerde taban bandını aştı

| seed | işbirliği taban → kaldıraç |
|---|---|
| 42 | 1.59% → 0.32% |
| 7 | 0.95% → 1.08% |
| 123 | 1.66% → **5.40%** |
| 1 | 0.88% → 1.29% |
| 777 | 1.06% → **3.49%** |

Faz 4.5–7 boyunca paylaşım oranı %0.4–2.4 bandından hiç çıkmamıştı; burada 2/5
seed'de çıkıyor. **Bu bir bulgu değil, bir gözlemdir**: Faz 8'in ölçütü
işbirliğini kapsamıyor, bu koşumlarda eşleşmiş bir *sosyal* kontrol (soyisim
karıştırma) yok, ve kaldıraç ekolojiyi de değiştiriyor. Sınanması sonraki fazın
işi. Saldırı oranı da 4/5 seed'de yükseliyor (%3.4–6.1 → %8.2–12.0), yani
"işbirliği arttı" diye okunacak basit bir tablo yok.

## 7. Sonuç ve karar

| soru | cevap |
|---|---|
| Yoğunluğa bağlı seçilim süpürgeyi durduruyor mu | ✅ **4/5 seed**, dört ölçüt birden |
| Mekanizma bilgi mi, ekstra yük mü | ✅ **bilgi** — kontrol daha çok gider ödeyip 0/5 |
| Koloni çöküyor mu | ❌ hayır; kişi başı toplama 4/5 seed'de **yükseliyor** |
| Etiket mi genom mu | genom çeşitliliği **korunuyor**, `genetic_r` çökmüyor |
| Enerji korunumu | 15/15 koşumda tam |

Ölçüt dosyasındaki karar kuralının birinci satırı: **melez soylar, soy-arası
ilişki matrisi ve grup seçilimi artık ölçülebilir bir zemine oturuyor.**
Sonraki faz o olabilir.

Zemin: `experiments/faz8_yogunluk.yaml` (+ tohum gerekmez — taze başlangıçta
çalışıyor, ki Faz 7'de taze zemin en kötüsüydü).

## 8. Sınırlar — ne DEMİYORUZ

- **Diğer iki kaldıraç denenmedi.** Geniş dünya ve uzamsal sığınaklar
  (coğrafi ayrışma) bu fazda hiç koşulmadı; "en iyi kaldıraç budur" demiyoruz,
  "bu kaldıraç ölçütü geçti" diyoruz.
- **Tek bir `cost` değeri 5 seed'de sınandı.** 0.30 ölçütü geçen en küçük
  *taranmış* değer; ara değerler (0.25, 0.35) denenmedi ve 0.02–0.20 aralığı
  tek düze değil.
- **Kaldıraç ekolojiyi de değiştiriyor**: popülasyon %0–23 düşüyor, kişi başı
  toplama ve saldırı oranı yükseliyor. Bu zeminde ölçülecek her sosyal sonuç
  **kendi eşleşmiş kontrolüne** karşı okunmalı; Faz 4.5'in dersi (bir yeri
  onarmak başka yerde ölçümü bozabilir) burada da geçerli.
- **Mekanizma etikete bakıyor.** Genom benzerliğine bakan bir sürüm (niş
  örtüşmesi) daha ilkeli olurdu ama sıcak yolda pahalı; denenmedi.
