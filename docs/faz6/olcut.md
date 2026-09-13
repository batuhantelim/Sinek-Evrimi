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
