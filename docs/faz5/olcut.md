# Faz 5 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya karşılıklılık deneyleri
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Soru

Faz 4.6 işbirliğinin **birinci** mekanizmasını (akrabalık / Hamilton) eledi:
korunumlu zeminde `r·b/c` 1'i geçemiyor. Şimdi **ikinci** mekanizma:
**karşılıklılık**. Matematiği farklı (tekrarlı oyunlar, Axelrod), dolayısıyla
sonuç da farklı olabilir.

## Üç önkoşul ÖNCE garanti edilir

Bunlar olmadan "karşılıklılık reddedildi" denemez — doğru cümle "koşul yoktu".

| # | önkoşul | nasıl sağlanır | nasıl doğrulanır |
|---|---|---|---|
| 1 | **tekrarlı karşılaşma** | mevcut ekoloji (değişiklik gerekmeyebilir) | `tools/encounter_probe.py` |
| 2 | **tanıma** | kalıcı birey `id` zaten var; sensöre iki kanal eklenir | sensör testi |
| 3 | **hafıza** | RNN iç durumu zaten adımlar arası korunuyor (`reset()` yalnızca sondada çağrılıyor) + dışsal defter | korunum + sensör testi |

### Önkoşul 1 için ⚠ KRİTİK AYRIM: epizot ≠ adım

Bir sinek 100 adım aynı komşunun yanında dururrsa bu **tek** bir karşılaşmadır,
100 değil. Axelrod'un tekrarlı oyunu araya başka partnerlerin girdiği **ayrı
buluşmalar** ister. Sonda ikisini ayrı raporlar; **epizot-tekrarı** asıl ölçüdür.

**Zemin sayılma şartı:** ajanların **en az %30'u**, aynı bireyle **≥3 ayrı
buluşma** yaşamış olmalı. Sağlanmazsa önce ekoloji ayarlanır (menzil/ömür),
karşılıklılık ölçülmez.

## Mekanik (kapasite verilir, kural verilmez)

- `Agent.ledger`: partner `id` → geçmiş etkileşimlerin net işareti. **Alıcı**
  kaydeder: birinden enerji aldıysa `+`, biri saldırdıysa `−`.
- İki yeni sensör (sözleşmenin **sonuna**): `partner_known` (bu bireyle daha
  önce karşılaştım mı) ve `partner_ledger` (onunla geçmişimin net işareti).
- **"Karşılık ver" diye bir kural YOK.** Yalnızca bilgi kanalı. Evrim
  kullanırsa kullanır.
- Enerji korunumu değişmez (`need_mode: fitness`, `energy_created ≈ 0`).

## Kontroller (her koşum kendi kontrolüyle okunur)

| kontrol | ne bozar | beklenen |
|---|---|---|
| **hafızasız** | `rules.memory.enabled: false` — iki sensör de sabit 0 | karşılıklılık ÇIKMAMALI; çıkarsa metrik sahtedir |
| **kimlik karıştırma** | `rules.memory.control: shuffle_identity` — defter her adım yanlış bireyi gösterir | geçmiş anlamsızsa karşılıklılık çökmeli |

## "Karşılıklılık evrimleşti" sayılma ölçütü

En az 3 seed'de (umut verirse 5'e çıkarılır):

1. **Korunum**: `energy_created` ≈ 0 (aksi hâlde koşum GEÇERSİZ, atılır).
2. **Zemin**: epizot-tekrarı ölçütü (yukarıdaki %30) sağlanmış.
3. **Ölçülebilirlik**: defteri pozitif olan fırsatlar ile olmayanların **her
   biri** toplam fırsatların ≥%5'i (yoksa oran gürültüdür).
4. **Ayrışma**: `recip_bias_adj` — `P(paylaş | defter +)` ile
   `P(paylaş | defter ≤ 0)` arasındaki **verici enerjisine göre katmanlanmış**
   fark — kendi hafızasız kontrolünden Welch t > 2 ile ve doğru yönde
   ayrışıyor, seed'lerin **en az 2/3'ünde**.

Katmanlama şart: defteri pozitif olan ajan **enerji almıştır**, dolayısıyla
zengindir ve zaten daha çok paylaşır. Bu, `kin_bias` konfoundunun aynısıdır
(§3.5) ve düzeltilmeden okunamaz.

## Ayrıca raporlanacak

- Genel işbirliği oranı: hafızalı kol hafızasız kontrolden ayrışıyor mu?
- **Karşılıklı düşmanlık**: `P(saldır | defter −)` vs `P(saldır | defter ≥ 0)`,
  aynı katmanlı düzeltmeyle. Misilleme de karşılıklılıktır.
- Faz 4.6 yan bulgusu (saldırı yabancıya yönelir) hafızayla değişiyor mu?
- Yan etkiler: `genetic_r`, dış-grup payı, kişi başı toplama, popülasyon.

## Negatif de sonuçtur

Çıkmazsa: bu minimal dünyada işbirliği **iki** büyük mekanizmayla da
(akrabalık ve karşılıklılık) evrimleşmiyor — Faz 4.6'yı tamamlayan, kapsamlı
bir negatif. Ama ancak üç önkoşul **ölçülerek** sağlandıysa böyle denebilir.
