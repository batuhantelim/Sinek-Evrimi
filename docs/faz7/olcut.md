# Faz 7 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya Faz 7 koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Kök sorun

Her faz bir öncekinin **kazananlarını** tohumladı (`population.npz`). Zinciri
kurarken amaç hesabı boşa harcamamaktı, ama her tohumlama çeşitliliği bir
kademe daralttı. Faz 6'da ölçülen zemin: **etkin soy ~1.0**, dış-grup fırsat
payı **%0.1–2.0**. Yani "grup-içi vs grup-dışı" ölçülürken ortada **tek grup**
kalmıştı.

Son üç negatif (akrabalık, karşılıklılık, partner seçimi) bu zeminde üretildi.
Faz 7 yeni bir mekanizma **aramıyor**; o negatiflerin **artefakt olup olmadığını**
sınıyor.

⚠ Bu, elenen soyları geri çağırmak DEĞİLDİR — o seçilimi iptal ederdi. Her
deneye **tam çeşitlilikle adil bir başlangıç** vermektir.

## Bölüm 1 — çeşitlilik altyapısı

### Ölçüt 1A: taze başlangıç gerçekten farklı mı (doğrulama)

Aynı rejim (Faz 4.5 temiz ekolojisi), aynı seed, tek fark tohum:
`docs/faz4tani/population_taban.npz` ile **taze** (rastgele 0. nesil).
Taze kolun son çeyrekte **etkin soyu ve dış-grup payı** tohumlu koldan
belirgin biçimde yüksek olmalı. Değilse sorun tohumlama değil, başka bir
yerdedir ve Faz 7'nin gerekçesi çürür.

### Ölçüt 1B: ÇEŞİTLİLİK ÖLÇÜTÜ (asıl hedef)

Bir koşum "ölçülebilir çeşitlilikte" sayılır ancak şu ikisi **son çeyrekte**
birlikte sağlanırsa:

- **etkin soy ≥ 5.0** (Faz 3 zemini 4.7–4.9, Faz 4 tabanı 7.2 idi; 5.0 bu
  ikisinin arasında ve in/out örneklemi için yeterli),
- **dış-grup fırsat payı ≥ %10** (projenin Faz 4'ten beri kullandığı
  ölçülebilirlik şartı).

En az **2/3 seed** (umut verirse 5). Sağlanmazsa çeşitliliği ayakta tutan bir
mekanizma kurulur ve **en küçük** yeterli ayarda sabitlenir.

### Ölçüt 1C: çeşitliliğin bedeli ÖLÇÜLÜR

Çeşitlilik bedavaya gelmez. Her ayarda şunlar raporlanır ve mekanizma
bunlardan birini bozuyorsa açıkça yazılır:

- **korunum**: `energy_created` = 0 (aksi hâlde koşum GEÇERSİZ),
- **yetkinlik**: kişi başı toplama (`forage_per_capita`) — taze koloni acemi
  başlar; Faz 2 kör kontrole karşı ×1.15–1.32 avantaj ölçmüştü,
- **çevresel sınırlama**: `at_cap` = 0, `repro_blocked` ≈ 0 (Faz 4.5 kazanımı
  korunmalı),
- **tükenme yok**, popülasyon deney boyunca yaşıyor,
- **determinizm**: taze başlangıç da seed'e bağlı tekrar-üretilebilir
  (`--check-determinism` ve `state_hash` testi).

### ⚠ Etiket çeşitliliği ≠ genetik çeşitlilik

`split_rate`'i yükseltmek etkin soyu kolayca büyütür ama bölünen soy, bölündüğü
anda ebeveyniyle **genetik olarak aynıdır**. Bu yüzden Bölüm 1'de üç ölçü ayrı
raporlanır: `lineage_effective` (etiket), `weight_diversity` +
`behavior_diversity` (genom), `genetic_r` (gerçekleşen akrabalık). Ölçüt 1B
etiket üzerinden yazılmıştır, ama **genetik ölçüler de yükselmiyorsa** mekanizma
"çeşitlilik üretti" diye raporlanamaz.

## Bölüm 2 — fazları bağımsızlaştır

- Tohum bir **config anahtarı** olur (`run.load_genomes`), CLI onu ezer.
  Böylece "önceki fazdan tohumla" ile "taze başla" bir deney dosyasında
  seçilebilir; varsayılan **taze**.
- Eski deney dosyaları kendi tohumlarını **açıkça** yazar — varsayılan
  değişince eski bir deney sessizce başka bir deneye dönüşmemeli
  (Faz 4'teki `predator.enabled: false` dersi).

## Bölüm 3 — taze zeminde AKRABALIĞI yeniden test

Faz 4.6 korunumlu zeminde `r·b/c` ≤ 0.989 buldu (0/15 koşul eşiği geçti) ve
kontrollü evrim testinde ayrışma 3/5 seed, etki 0.16 puandı. O ölçümler **etkin
soy ~1–3** zemininde yapıldı.

Taze + çeşitli zeminde aynı iki soru, aynı ölçülerle:

1. **`r·b/c` > 1 oluyor mu?** `genetic_r` × ölçülen `b/c`. `b` ve `c`
   varsayılmaz, `tools/hamilton_probe.py` ile **yavru cinsinden** ölçülür.
2. **In-grup fedakârlık kendi karıştırma kontrolünden ayrışıyor mu?**
   `kin_bias_adj`, Welch t > 2, **≥ 2/3 seed** (umut verirse 5).

### Karar kuralı (önceden yazıldı)

| sonuç | anlamı | sonraki adım |
|---|---|---|
| `r·b/c` ≤ 1 **ve** ayrışma < 2/3 | Faz 4.6 negatifi **gerçek**, çeşitlilik artefaktı değil | karşılıklılık/partner seçimini tekrarlamaya gerek yok; negatif sağlamlaştı |
| ikisinden **biri** değişti | eski negatif kısmen çeşitlilik çöküşünün artefaktı | Faz 5 ve Faz 6 **taze zeminde tekrar edilir** |

Her iki sonuç da raporlanır; "beklediğim çıkmadı" diye ölçüt değiştirilmez.

## Değişmeyen kurallar

Korunumlu enerji (`energy_created` = 0, test zorlar); rol/kast kodlanmaz;
paylaşım/saldırı ödüllendirilmez (test korumalı); in/out ayrı ölçülür;
determinizm; kişi başı birim; kaldıracın yan etkisi ölçülür; her oran kendi
**eşleşmiş kontrolüne** karşı okunur.
