# CLAUDE.md — Evrimleşen Sinek Kolonisi

Ajan tabanlı bir yapay yaşam (ALife) simülasyonu. Amaç: çok sayıda basit "sinek"
ajanını bir ortama koyup **çeşitlilik + seçilim + mutasyon** üzerinden nesiller
boyunca davranışın kendiliğinden ortaya çıkmasını (emergence) gözlemlemek.

İlham: Sugarscape (*Growing Artificial Societies*), Axelrod'un işbirliğinin evrimi
deneyleri, Avida/Tierra.

---

## 1. Projenin mantığı

Kod, davranışı **tarif etmez**; davranışın çıkabileceği bir **tezgah** kurar.
Üç şey ayrı tutulur:

| Katman | Soru | Dosya |
|---|---|---|
| **Beden** | Ne hissedebilirim, ne yapabilirim? | `sinek/agent.py` |
| **Beyin** | Hissettiğimden ne karar çıkar? | `sinek/brains/` |
| **Kural** | Bu kararın bedeli/ödülü ne? | `config.yaml` → `rules:` |

Bu ayrım kritik: bir sineğin "işbirlikçi" mi "saldırgan" mı olduğu kodda yazmaz.
Kurallar (paylaşım ödülü, saldırı cezası, kıtlık) genom üzerinden seçilim
baskısı yaratır, davranış oradan **türer**.

### Fazlar

| Faz | İçerik | Durum |
|---|---|---|
| **Faz 1** | Tek tip (klon) ajan + ortam + hareket + yemek + üreme/ölüm | ✅ **tamam** |
| **Faz 2** | Genom mutasyonu + seçilim + evrimleşebilir sinir ağı beyni | ⏳ sıradaki |
| **Faz 3** | Sosyal kurallar: paylaşma / saldırma, işbirliğinin evrimi | ⏳ iskelet hazır |

Faz 1'de `evolution.enabled: false` — **bilerek**. Tüm ajanlar tek bir kurucu
genomun kopyasıdır, dolayısıyla `behavior_diversity` metriği **tam olarak 0**
döner. Bu, "çeşitlilik girmeden evrim olmaz" kontrol grubudur; Faz 2 sonuçları
buna karşı okunacak.

---

## 2. Mimari

```
run.py                  CLI girişi: config yükle, koş, logla, özetle
config.yaml             TÜM parametreler. Kod değiştirmeden deney yapılır.
sinek/
  config.py             YAML yükleme, derin birleştirme, --set ile ezme
  world.py              2B dünya: yemek/tehlike/iklim alanları, algı alanları
  fields.py             blur + gradyan yardımcıları (algının hızlı çekirdeği)
  agent.py              Beden: sensör vektörü ↔ motor vektörü sözleşmesi
  brains/
    base.py             Brain arayüzü + kayıt defteri (registry)
    reflex.py           Faz 1 beyni: genomdan gelen ağırlıklı refleks devresi
  genome.py             Genom + gaussian mutasyon
  spatial.py            Uzamsal hash (Faz 3 ikili etkileşimleri için)
  simulation.py         Adım döngüsü: dünya → algı → karar → eylem → ölüm/üreme
  metrics.py            Metrik toplama + CSV
  render.py             Durum → RGB kare (tek çizici, iki çıkış)
  sinks.py              Kare çıkışı: headless PNG / canlı pygame
  pngwrite.py           Saf Python PNG yazıcı (Pillow gerekmez)
  font3x5.py            HUD yazısı için minik bitmap font
tools/plot_metrics.py   metrics.csv → PNG grafik (matplotlib gerekmez)
tests/                  unittest — determinizm + Faz 1 davranış testleri
```

### Sensör/motor sözleşmesi

Beden ile beyin arasındaki **tek** bağ iki vektördür:

```
sensors (13 float) ──► Brain.act() ──► motors (4 float)
```

```python
SENSOR_NAMES = [bias, energy, age, food_here, food_fwd, food_left,
                food_strength, hazard_fwd, hazard_left, hazard_near,
                mate_fwd, mate_left, crowd]
MOTOR_NAMES  = [turn, thrust, eat, social]
```

Yön sensörleri **egosentrik**: `_fwd` = sineğin baktığı yön bileşeni,
`_left` = sol bileşeni. Böylece beyin mutlak koordinat bilmeden çalışır —
evrimleşebilir bir ağ için şart.

`social` motoru Faz 1'de üretilir ama yok sayılır; Faz 3'te
`>0 → paylaş`, `<0 → saldır` olacak.

### Yeni beyin takmak (Faz 2 / FlyWire)

```python
from sinek.brains.base import Brain, register

@register("rnn")
class TinyRNN(Brain):
    @staticmethod
    def genome_size(cfg) -> int:      # genomdan kaç ağırlık istiyorum
        return (13 + H) * H + H * 4
    def act(self, sensors, rng): ...
    def reset(self): ...             # recurrent durumu sıfırla
```

Sonra `config.yaml` → `brain.type: rnn`. Simülasyonun geri kalanına
dokunmak gerekmez. Aynı kanca ileride opsiyonel bir **connectome backend**
(ör. FlyWire) için de kullanılacak — bu yüzden Faz 1'de connectome yok,
sadece arayüz temiz bırakıldı.

### Algı neden "alan tabanlı"?

Her sineğin çevresini tek tek taraması yerine dünya, adım başına **bir kez**
bulanıklaştırılmış bir "koku alanı" ve onun gradyanını hesaplar; sinek kendi
hücresindeki değeri O(1) okur (`world.update_food_perception()`).
~20× daha hızlı ve gerçek kemotaksise daha yakın. Tehlike alanları sabit
olduğu için kurulumda bir kez hesaplanır.

### Determinizm

- Tüm rastgelelik **tek** `np.random.default_rng(seed)` üzerinden.
- Ajanlar her adımda sabit sırada (liste sırası = id sırası) işlenir.
- Doğumlar listenin sonuna deterministik sırayla eklenir.
- `sim.state_hash()` durumun kısa parmak izini verir.

```bash
python run.py --check-determinism      # iki koşum, hash'ler eşit olmalı
```

---

## 3. Nasıl çalıştırılır

```bash
pip install -r requirements.txt          # numpy + PyYAML (pygame opsiyonel)

python run.py                            # config.yaml ile, headless + PNG kareler
python run.py --steps 1000 --viz none    # sadece metrik, en hızlısı
python run.py --viz pygame               # canlı pencere (SPACE: duraklat, Q: çık)
python run.py --seed 7 --name deney7
python run.py --check-determinism
python -m unittest discover -s tests     # 11 test
```

Çıktılar `runs/<name>/` altına yazılır:

```
runs/faz1/
  config_used.yaml    o koşumda gerçekten kullanılan tam config
  metrics.csv         adım adım metrikler
  summary.txt         terminal özeti
  frames/*.png        görselleştirme kareleri
```

Grafik:

```bash
python tools/plot_metrics.py runs/faz1
python tools/plot_metrics.py runs/faz1 runs/kontrol_kor --cols population,mean_energy
```

### Kod değiştirmeden deney yapmak

```bash
# kıtlık: yemek üç kat yavaş yenilensin
python run.py --set world.food.regrowth_rate=0.003 --name kitlik

# kör kontrol grubu: yemeği koklayamayan sinekler
python run.py --set genome.params.food_attraction=0.0 \
              --set genome.params.hunger_gain=0.0 --name kontrol_kor

# sürüleşme eğilimi
python run.py --set genome.params.crowd_bias=1.2 --name suru
```

`--set` noktalı yolu doğrudan `config.yaml` ağacına yazar ve tekrarlanabilir.
Kısmi bir YAML dosyası da verebilirsiniz; eksik anahtarlar `config.yaml`'dan
tamamlanır.

---

## 4. Metrikler (`metrics.csv`)

| Sütun | Anlamı |
|---|---|
| `population` | canlı ajan sayısı |
| `births`, `deaths` | o adımdaki doğum/ölüm |
| `death_starved / hazard / old_age` | ölüm nedeni ayrımı |
| `mean_energy`, `std_energy` | koloninin enerji durumu |
| `max_lineage` | en uzun soy zinciri (kaçıncı nesil) |
| `food_total`, `food_fill` | kaynak stoğu ve doluluk oranı |
| `food_eaten` | o adımda tüketilen yemek birimi |
| `clustering` | Morisita benzeri kümelenme: `>0` sürüleşme, `<0` kaçınma |
| `behavior_diversity` | genom parametrelerinin ort. std sapması (**Faz 1'de 0**) |
| `cooperation_rate` | Faz 3 için ayrılmış |

`clustering` ve `behavior_diversity` sütunları Faz 1'de anlamlı sonuç
üretmeyecek olsa da şema baştan sabit — grafik/analiz kodu fazlar arasında
bozulmasın diye.

---

## 5. Faz 1 sonuçları (seed 42, 3000 adım)

Çıktılar: `runs/faz1/` ve kontrol grubu `runs/kontrol_kor/`.
Özet görseller depoda: **[docs/faz1/](docs/faz1/)**.

- **Klonlar aynı davranıyor.** `behavior_diversity = 0.0`; aynı sensör
  girdisinde tüm beyinler aynı motor çıktısını veriyor (test edildi).
- **Algı-motor döngüsü çalışıyor.** Tam kör kontrol grubuna karşı (koku ile yön
  bulma *ve* yem üstünde yavaşlama kapalı) ajan başına besin alımı **×1.15**;
  yamalar seyrekleştikçe avantaj **×1.32**'ye çıkıyor — arama zorlaştıkça
  duyunun değeri artıyor.
- **Boom–bust salınımı.** Popülasyon aşırı artıp kaynağı tüketiyor, çöküyor,
  kaynak yenilenince tekrar artıyor; salınım sönümlenerek ~300 civarına
  oturuyor. Bu **kodlanmadı** — enerji bütçesi ile yenilenme hızının
  etkileşiminden çıktı.
- **Kaynak yamalarına kümelenme.** `clustering > 0`; karelerde yamalar içinde
  otlama izleri (yenmiş koridorlar) görünüyor. Kümelenme sinekler birbirini
  çektiği için değil (`crowd_bias = 0`), aynı kaynağa yöneldikleri için oluşuyor.
- **Tehlikeden kaçınma.** Tehlike kaynaklı ölüm ~0. Kaçınma çalışıyor, ama
  tehlikeler `avoid_food_patches: true` ile yamalardan uzağa konduğu için
  seçilim baskısı zayıf. Faz 2'de risk/ödül gerilimi istiyorsanız bunu
  `false` yapın — tehlike yemeğin üstüne oturur.

Faz 1'de **olmayan** ve olmaması gereken şey: davranış ayrışması. O Faz 2'nin işi.

### Kalibrasyon notu

`food_strength` sensörü, gradyan büyüklüğünü **tam dolu bir dünyada
erişilebilecek en dik gradyana** (`World._reference_gradient()`) bölerek
normalize eder. İlk sürümde ölçek `food_scale / food_radius` idi; sinyal
~0.08'de kalıyor, gezinme gürültüsü altında eziliyordu. Yeni ölçekle gradyanla
hizalanma (`food_fwd` ortalaması) 0.42 → 0.66'ya çıktı. Yeni bir sensör
eklerken ölçeğini böyle bir referansa bağlayın, yoksa sensör sessizce ölür.

---

## 6. Faz 2'ye geçerken yapılacaklar

1. `config.yaml` → `evolution.enabled: true` (altyapı hazır: `Genome.mutate`).
2. `sinek/brains/rnn.py`: küçük recurrent ağ (~10–40 nöron), ağırlıklar
   `genome.weights`'ten. `Brain.genome_size()` ile boyut bildirilir.
3. `simulation.py` → nesil döngüsü: sabit uzunluklu nesiller + `Agent.fitness`
   üzerinden seçilim (şu an üreme sürekli/aseksüel).
4. Metrikler: nesil başına ortalama fitness, genom parametre histogramı.
   **Başarı ölçütü**: nesiller boyunca ortalama fitness artmalı ve
   `behavior_diversity` 0'dan yukarı çıkmalı.

## 7. Kod yazarken uyulacak kurallar

- **Parametre kodda değil config'te.** Yeni bir sabit ekliyorsan `config.yaml`'a
  koy ve `cfg.get("yol.anahtar", varsayilan)` ile oku.
- **Rastgelelik `sim.rng`'den.** `random` modülü ya da `np.random.seed`
  kullanma; determinizm testi bunu yakalar.
- **Ajan sırası bozulmasın.** Sözlük/küme üzerinde gezinip ajan işleme.
- **Sensör/motor listesine ekleme yaparsan** `SENSOR_NAMES`/`MOTOR_NAMES`'in
  **sonuna** ekle, mevcut indeksleri kaydırma (kayıtlı genomlar bozulur).
- **Faz sınırına saygı.** Faz 3 kancası bilerek `NotImplementedError` atıyor;
  sessizce yok saymak yerine yüksek sesle patlaması tercih edildi.
- Test: `python -m unittest discover -s tests` yeşil kalmalı.
