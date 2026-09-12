# Faz 3 ara tarama — eksen B: kaynak kıtlığı saldırganlık üretiyor mu?

Eksen A H1'i (dış-grup bolluğu) reddetti ama yemek doluluğu `atk_t`'nin en
güçlü tek yordayıcısı olarak **kazara** ortaya çıkmıştı. Burada kasıtlı test
ediyoruz. Yeni mekanik yok; yalnızca `world.food.*`.

3 seviye × seed 42, her biri soyisim-karıştırma kontrolüyle, 12000 adım.

---

## 1. Sonuç: H2 reddedildi — hiçbir kıtlık seviyesi saldırıyı artırmadı

| koşul | kişi başı kaynak **girdisi** | assortment | N | saldırı | iç / dış | `atk_t` | seviye |
|---|---|---|---|---|---|---|---|
| taban (referans) | 0.286 | 0.690 | 700 | %4.42 | — | +0.27 | — |
| `B_bol` | **0.573** | 0.454 | 700→700 | %1.98 | 1.03 / 3.05 | **−13.27** | artmadı |
| `B_kit` | 0.115 | 0.768 | 700→700 | %3.37 | **4.90 / 3.27** | −0.32 | artmadı |
| `B_cok_kit` | **0.036** | 0.216 | 700→700 | %3.11 | 4.18 / 5.00 | −0.91 | artmadı |

Kişi başı kaynak girdisinde **16 kat** aralık tarandı. Saldırı üç seviyede de
taban rejimin (%4.42) **altında** kaldı. Koloni hiçbirinde çökmedi (700→700).

**D/Ç ayrımı hiç gündeme gelmedi**, çünkü saldırı hiç artmadı. Yani ne
"kıtlık düşmanlık üretir" ne de "kıtlık çaresizlik üretir" — kıtlık bu
kurulumda saldırganlığı hiç hareket ettirmiyor.

Ters yönde bir işaret var: **bolluk** (`B_bol`) saldırının *seviyesini*
düşürüp *yönünü* yabancıya çevirdi (dış/iç 2.96×, `atk_t` −13.27). Bu H2'nin
tersi, ama tek nokta — hipotez bile değil, not.

## 2. Ölçüm hatası: `food_fill` koşullar arası geçersizmiş

`food_fill` bir **orandır** (mevcut / kapasite) ve kapasite koşula göre
değişiyor. `B_cok_kit` yama sayısını 24 → 14 düşürdüğü için kapasitesi
20046 → 12444'e indi:

| koşul | kapasite | doluluk | toplam yemek | **kişi başı girdi** |
|---|---|---|---|---|
| `B_bol` | 20046 | %45.5 | 9123 | 0.573 |
| `B_kit` | 20046 | %35.7 | 7155 | 0.115 |
| `B_cok_kit` | **12444** | **%59.4** | 7390 | **0.036** |

En kıt koşul **en yüksek doluluk oranını** verdi. Doğru değişken kişi başı
kaynak girdisi (`yenilenme × kapasite / N`); tablolar artık onunla okunuyor.

Bu, kendi yazdığım "kaldıracınızın ne yaptığını ölçün" kuralının ikinci kez
beni yakalaması. Eksen A'da kaldıraç beklenmedik yönde çalışmıştı; burada
**ölçüm birimi** yanlıştı.

## 3. Ara raporumdaki örüntü çöktü

İki tur önce "düşük assortment → yabancıya, yüksek → kör örüntüsü her iki
eksende de tutuyor" demiştim. **Tutmuyor:**

| koşum | assortment | karar |
|---|---|---|
| `B_cok_kit`/42 | **0.216** (tablonun en düşüğü) | **kör** |
| `A2_tam_karisma`/42 | 0.768 (en yükseklerden) | yabancıya |
| `A1_taban`/42 | 0.767 | kör |
| `B_kit`/42 | 0.768 | kör |

Aynı assortment değerinde zıt kararlar, ve en düşük assortment kör.
Örüntü yok.

## 4. Birleşik analiz (eksen A + B, n = 15)

Pooling'in metodolojik kazancı: **yemek ile assortment artık ayrık**
(r = +0.023; eksen A'da −0.000). Yani iki eksen birlikte, tek eksende
yapılamayan ayrıştırmayı mümkün kıldı.

| değişken | `atk_t` ile r | aralık |
|---|---|---|
| kişi başı girdi | −0.210 | 0.036 – 0.777 |
| kişi başı stok | +0.391 | 6.3 – 22.8 |
| assortment | +0.339 | 0.216 – 0.768 |
| dış-grup payı | −0.134 | 0.048 – 0.724 |

Hiçbiri güçlü değil. Dört değişkenli regresyon R² = 0.511 ama n = 15 ve
4 tahminci — düzeltilmiş R² ≈ 0.32, ve `assortment ~ dış_pay` hâlâ −0.822
bağımlı. Bu tabloyla nedensel bir iddia kurulamaz.

**Asıl gözlem: iki sınıf her değişkende neredeyse tamamen örtüşüyor.**

| karar | n | assortment | kişi başı girdi | dış-grup payı |
|---|---|---|---|---|
| kör | 4 | 0.216 – 0.768 | 0.036 – 0.286 | 0.133 – 0.509 |
| yabancıya | 11 | 0.221 – 0.768 | 0.286 – 0.777 | 0.048 – 0.724 |

Yalnızca kişi başı girdi ayrışıyor gibi duruyor — ama bu bir mekanizma
değil, **tasarımın yeniden ifadesi**: eksen A koşullarının hepsi varsayılan
yemek parametrelerini kullanıyor ve popülasyon tavanda olduğu için hepsi
otomatik olarak ≥ 0.286'da. Kör kalan dördü de "taban + eksen B'nin iki kıt
koşulu". Yani ayrışma, hangi koşulların koşulduğunu tekrarlıyor.

## 5. Nereye varıyoruz

- **H1 reddedildi** (eksen A): dış-grup bolluğu düşmanlığı öngörmüyor.
- **H2 reddedildi** (eksen B): kıtlık saldırıyı hiç artırmadı; D/Ç sorusu
  gündeme bile gelmedi.
- **Ölçtüğümüz hiçbir çevresel skaler, saldırının yabancıya yönelip
  yönelmeyeceğini öngörmüyor.** 15 koşumun 11'i yabancıya, 4'ü kör, ve iki
  sınıf her değişkende örtüşüyor.

Bu güçlü bir negatif ve Faz 4'ün gerekçesini sağlamlaştırıyor: grup-dışı
düşmanlık tek bir çevre düğmesiyle açılıp kapanan bir şey değil.
Literatürdeki tetikleyici **gruplar arası rekabet** (ortak tehdit / avcı) —
Faz 4'ün asıl testi bu olmalı.

## 6. Yeniden üretmek

```bash
python tools/env_sweep.py --conditions B_bol B_kit B_cok_kit --seeds 42
python tools/env_sweep.py --summary sonuc.jsonl
```

Ham veri: `eksenB_taramasi.jsonl`, özet: `eksenB_taramasi.txt`.
Eksen A verisi: `eksenA_taramasi.jsonl`.
