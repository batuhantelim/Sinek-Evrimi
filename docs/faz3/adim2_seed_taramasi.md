# Faz 3 — sağlamlık taraması: adım 2'nin 5 seed'de tekrarı

Adım 2'nin bulgusu tek seed üstünde duruyordu. Bu tarama **hiçbir mekaniği
değiştirmeden** aynı rejimi 5 seed'de tekrarlar; her seed için hem asıl koşum
hem soyisim-karıştırma kontrolü çalışır (kontrolsüz sonuç okunmaz).

Rejim, `experiments/faz3b_saldiri.yaml` ile **birebir aynı** — bunu
`tests/test_tools.py::test_seed_sweep_regime_matches_step2` denetliyor:
tarama ile deney dosyası ayrışırsa "sadece seed değişiyor" iddiası çöker ve
test kırmızıya döner.

12000 adım = 24 dönem, Faz 2 tohumu (`docs/faz2/population.npz`).

---

## 1. Tekrarlanabilirlik tablosu

Dört hücre son çeyrek, fırsata koşullu; `kin_adj` son yarının ortalaması (puan).

| seed | paylaş iç | paylaş dış | saldır iç | saldır dış | kin_adj asıl | kontrol | t | ayrıştı | atk_t | saldırı | r | soy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7 | 44.50% | 26.58% | 5.06% | 5.52% | +26.16 | +0.43 | +6.77 | **EVET** | −0.39 | kör | 0.61 | 7.1 |
| 42 | 56.11% | 21.51% | 5.10% | 3.84% | +35.07 | +0.60 | +18.55 | **EVET** | +0.92 | kör | 0.77 | 4.5 |
| 123 | 91.30% | 74.37% | 1.05% | 0.93% | +31.38 | +0.19 | +5.43 | **EVET** | −1.80 | kör | 0.82 | 3.5 |
| 999 | 90.25% | 63.53% | 3.53% | 3.31% | +36.06 | +0.44 | +9.55 | **EVET** | −1.32 | kör | 0.66 | 4.1 |
| 2024 | 17.52% | 3.52% | 2.09% | 3.71% | +11.43 | +0.30 | +13.42 | **EVET** | −10.23 | **yabancıya** | 0.23 | 10.6 |

**seed 42 adım 2'yi birebir tekrarladı** (%56.11 / %21.51 / %5.10 / %3.84).
Determinizm ve rejim eşleşmesi böylece ayrıca doğrulanmış oldu.

## 2. Özet

**In-grup fedakârlık: 5/5 seed'de kontrolden ayrıştı.**

| | asıl | kontrol |
|---|---|---|
| `kin_bias_adj` | **+28.02 ± 10.05** puan | +0.39 ± 0.15 puan |
| Welch t | +10.75 ± 5.33 (en zayıf **+5.43**) | — |
| in/dış oranı | 2.38× ± 1.55 | — |

En zayıf seed'de bile t = +5.43, yani eşiğin (2.0) iki katından fazla.
Kontrol her seed'de düz (+0.19 … +0.60). **Yön sağlam.**

**Dış-grup düşmanlık: 4/5 seed'de akrabalığa kör** (`|t| < 2`).
Tek istisna seed 2024: `t = −10.23`, yani yabancıya daha çok saldırıyor.

## 3. Dürüst okuma: yön sağlam, büyüklük değil

- **Yön** tekrarlanabilir: 5/5 fedakârlık ayrımı, 4/5 saldırı körlüğü.
- **Büyüklük oynak**: `kin_bias_adj` 11.4 – 36.1 puan (3× aralık); in-grup
  paylaşım oranı **%17.5 – %91.3** (5× aralık). Tek seed'in mutlak sayılarını
  "koloninin işbirliği düzeyi" diye okumak yanlış olur.
- Bu oynaklık, adım 2'nin %56.11 gibi sayılarının **rejimin değil o seed'in**
  özelliği olduğunu gösteriyor. Raporlanacak şey oran ve yön, mutlak seviye değil.

## 4. Aykırı seed 2024 — bir ipucu, bulgu değil

2024 her boyutta diğerlerinden ayrı: en düşük assortment (r = 0.23), en çok
soy (10.6), en düşük paylaşım — ve **saldırının yabancıya yöneldiği tek seed**.

| seed | r | dış-grup fırsat payı | atk_t |
|---|---|---|---|
| 2024 | 0.23 | **53.1%** | −10.23 |
| 7 | 0.61 | 27.0% | −0.39 |
| 999 | 0.66 | 16.4% | −1.32 |
| 42 | 0.77 | 13.3% | +0.92 |
| 123 | 0.82 | 9.2% | −1.80 |

Beş nokta üzerinde `assortment` ile `atk_t` korelasyonu **0.900**, dış-grup
fırsat payıyla **−0.882**. Okunaklı bir hikâye: *yabancı nadirse düşmanlık
seçilemez; yabancı sıkça karşılaşılan bir şey olunca seçilebilir hale gelir.*

**Ama bu korelasyon tek noktaya dayanıyor.** 2024 çıkarılınca kalan dört
seed'de korelasyon **−0.087**'ye düşüyor ve dördünün de `|t| < 2` (hepsi kör).
Yani elimizde bir **hipotez** var, kanıt değil. Sınamak için dış-grup fırsat
payını doğrudan değişken yapan bir tarama gerekir (assortment'ı `max_speed`
ve `spawn_radius` ile süpürüp her seviyede birkaç seed) — adım 2'nin
"gruplar arası rekabet gerekir" yorumuyla da uyumlu bir test olur.

## 5. Sınırlar

- 5 seed küçük bir örneklem; oranlar ±1 seed'lik oynamaya duyarlı.
- Tüm seed'ler **aynı Faz 2 tohumundan** başlıyor. Farklı başlangıç
  popülasyonlarıyla tekrar, ayrı bir sağlamlık sorusudur.
- Etkin soy 3.5 – 10.6 aralığında; en düşük uçlarda dış-grup örneklemi
  küçülüyor (seed 123'te fırsatların yalnızca %9.2'si dış-grup).

## 6. Yeniden üretmek

```bash
python tools/seed_sweep.py --seeds 7 42 123 999 2024 --out sonuc.jsonl
python tools/seed_sweep.py --summary sonuc.jsonl
```

Ham sonuçlar: `seed_taramasi.jsonl`, özet tablo: `seed_taramasi.txt`.
