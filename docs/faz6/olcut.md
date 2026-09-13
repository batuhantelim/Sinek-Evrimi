# Faz 6 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya Faz 6 koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Soru

İki mekanizma elendi: akrabalık (Faz 4.6, `r·b/c` ≤ 0.989) ve karşılıklılık
(Faz 5, 0/5). Üçüncüsü: **partner seçimi**. Farkı yapısal — ilk ikisi `r·b>c`
eşitsizliğini *aşmaya* çalışıyordu; partner seçimi eşitsizliğin **kimin
arasında** kurulduğunu değiştirir.

Şu anki kısıt: ajan yalnızca **en yakın** komşuyla etkileşiyor. Kiminle
paylaşacağını mekân dayatıyor.

## Mekanik: seçme yeteneği verilir, politika verilmez

- Menzildeki en yakın **k aday** bulunur (varsayılan 4).
- Ajan her adayı **genomundan gelen ağırlıklarla** puanlar:
  `skor = w_kin·kin + w_ledger·defter + w_need·ihtiyaç + w_energy·enerji + w_dist·(−mesafe)`
- En yüksek skorlu aday hedef olur (beraberlikte küçük `id` — determinizm).
- Beş ağırlık `genome.params`'ta, `evolution.param_bounds`'ta sınırlı ve
  **mutasyona uğrar**. Başlangıçta hepsi **0.0** (yani saf beraberlik →
  en yakın; seçimsiz kola özdeş başlangıç).
- **"İyi partner seç" diye bir kural YOK.** Politika evrimleşirse evrimleşir;
  `gp_pick_*` ortalamaları evrimin ne bulduğunu gösterir.

## Kontroller (her koşum kendi kontrolüyle okunur)

| kontrol | ne bozar | beklenen |
|---|---|---|
| **seçimsiz** (`enabled: false`) | hedef yine en yakın komşu — Faz 5'in birebir aynısı | işbirliği tabanda kalmalı |
| **rastgele seçim** (`control: random`) | aday havuzu var ama seçim rastgele | "seçme yeteneği" mi "akıllı seçim" mi ayrımı |
| akrabalık karıştırma | soyisim bilgisizleşir | akrabalığa yönelik seçim çökmeli |
| defter karıştırma | geçmiş bilgisizleşir | geçmişe yönelik seçim çökmeli |

## "Partner seçimi işbirliğini kurdu" sayılma ölçütü

En az 3 seed'de (umut verirse 5):

1. **Korunum**: `energy_created` ≈ 0 (aksi hâlde koşum GEÇERSİZ, atılır).
2. **Ölçülebilirlik**: tükenme yok; son çeyrekte dış-grup fırsat payı ≥ %10.
3. **ASIL ÖLÇÜT — işbirliği tabanın üstüne çıktı**: son çeyrek paylaşım oranı,
   kendi **seçimsiz** kontrolünden Welch t > 2 ile **ve** yukarı yönde
   ayrışıyor, seed'lerin **en az 2/3'ünde**. Faz 4.5/4.6/5'te taban %0.6–2.4
   bandındaydı; "kurdu" demek için bu banttan çıkması gerekir.
4. **Seçim politikası evrimleşti mi**: seçilen partnerlerin özellikleri
   (akraba payı, defteri pozitif payı) **aday havuzunun** ortalamasından
   farklı olmalı — rastgele-seçim kontrolüne karşı okunur.

Ölçüt 3 geçmez ama 4 geçerse: "seçim politikası evrimleşti ama işbirliğini
kurmadı" diye raporlanır — ikisi ayrı sorudur.

## Ayrıca raporlanacak

- **Dışlama**: adayların kaçı hiç seçilmiyor; seçilmeyenler vermeyen/saldıran
  mı?
- İşbirliği çıkarsa **kime**: akrabaya mı (in/out), iyi-verene mi (defter),
  ayrımsız mı? Üç ölçü de kendi katmanlı düzeltmesiyle.
- Faz 4.6/5 asimetrisi (düşmanlık ayrım gözetir, iyilik gözetmez) değişiyor mu?
- Yan etkiler: `genetic_r`, etkin soy, kişi başı toplama, popülasyon,
  `pick_not_nearest` (seçim gerçekten kullanılıyor mu).

## Negatif de sonuçtur

Çıkmazsa: işbirliğinin **üç** büyük mekanizması da bu minimal dünyada
çalışmıyor — akrabalık, karşılıklılık, partner seçimi. Kapsamlı bir negatif.
Ama ancak seçim yeteneğinin gerçekten **kullanıldığı** (`pick_not_nearest > 0`)
gösterilirse böyle denebilir.

---

## EK (ilk parti sonrası, 2026-09-13): ÖNKOŞUL — aday havuzu

İlk parti koştuktan sonra ortaya çıktı: **seçim mekaniği hiç devreye
girmemişti.** İki ayrı neden:

1. **Kayıtlı genomlarda `pick_*` parametreleri yoktu.** `load_population`
   yalnızca dosyada yazılı isimleri yüklüyordu; `mutate` de mevcut anahtarlar
   üzerinde gezdiği için yeni parametreler **asla mutasyona uğramadı**.
   Seçim kolu, seçimsiz kolla **birebir aynı** `state_hash` verdi. Ağırlık
   taşımasının parametre karşılığı eksikti; eklendi ve taşıma artık
   `meta["migrated"]["new_params"]` ile **raporlanıyor** (sessiz değil).
2. **Aday havuzu ortalama 1.4 kişi.** `kinship.radius = 2.5` ile çoğu ajanın
   menzilinde tek komşu var; seçilecek bir şey yok.

Bu, Faz 5'in "üç önkoşul" disiplininin aynısı: **seçim, seçenek olmadan
ölçülemez.** Dolayısıyla ana soru (ölçüt 3) henüz **hiç test edilmedi**.

### Yeni önkoşul (ana ölçüt bundan sonra okunur)

Ortalama aday havuzu **≥ 2.0** ve kararların **≥ %50'sinde en az 2 aday**
bulunmalı. Sağlanmazsa `rules.kinship.radius` yükseltilir — **her iki kola da
birebir aynı** uygulanır ve yan etkileri (işbirliği tabanı, dış-grup payı,
`genetic_r`, kişi başı toplama) raporlanır.

Ölçüt 1–4 aynen geçerli.

### Önkoşul taraması sonucu: `rules.kinship.radius = 5.0`

Beş menzil, seed 42, 3000 adım, aynı tohum (`docs/faz5/population_hafiza.npz`),
seçim kolu:

| menzil | havuz | çok adaylı karar | en-yakın-değil | işbirliği | N | `genetic_r` | etkin soy | dış-grup payı | topla/kişi | paylaş/kişi |
|---|---|---|---|---|---|---|---|---|---|---|
| 2.5 (Faz 5) | 1.35 | — | 15.3% | 2.38% | 644 | 0.762 | 3.76 | 3.4% | 0.0447 | 0.0548 |
| 4.0 | 1.91 | 54.8% | 42.0% | 1.24% | 598 | 0.732 | 2.66 | 1.4% | 0.0474 | 0.0537 |
| **5.0** | **2.85** | **81.3%** | 29.0% | 1.24% | 668 | 0.774 | 3.04 | 2.3% | 0.0454 | 0.0699 |
| 6.0 | 3.02 | 85.2% | 49.4% | 1.44% | 657 | 0.696 | 1.93 | 2.3% | 0.0451 | 0.0884 |
| 8.0 | 3.32 | — | 74.6% | 1.22% | 437 | 0.759 | 3.21 | 3.5% | 0.0633 | 0.0762 |

Önkoşulu (havuz ≥ 2.0 **ve** çok adaylı karar ≥ %50) geçen en küçük değer
**5.0**. `4.0` çok adaylı kararda geçiyor ama ortalama havuzda kalıyor (1.91).

**Yan etkiler ölçüldü, hiçbiri ölçümü bozmuyor:** popülasyon 644 → 668,
kişi başı toplama neredeyse sabit (0.0447 → 0.0454), `genetic_r` sabit
(0.762 → 0.774), enerji üretimi 0.0. Kişi başı paylaşım yükseliyor
(0.0548 → 0.0699) ama **işbirliği oranı düşüyor** (%2.38 → %1.24): fırsat
sayısı paylaşımdan hızlı büyüyor. Bu yüzden ana ölçüt mutlak seviyeye değil,
**aynı menzildeki seçimsiz kontrole** karşı okunur.

⚠ **Bu tohumda dış-grup fırsat payı %1.4–3.5** — Faz 4.6'daki %10
ölçülebilirlik şartının çok altında. Etkin soy da ~3. Yani "işbirliği çıkarsa
**kime**" sorusunun *akrabalık* kanadı bu zeminde **okunamaz**; rapor bunu
GÜRÜLTÜ olarak işaretler. Ana soru (işbirliği tabanın üstüne çıkıyor mu) ve
defter kanadı bundan etkilenmez.
