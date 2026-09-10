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
| **Kural** | Bu kararın bedeli/ödülü ne? | `config.yaml` → `evolution.fitness`, `rules` |

Bu ayrım kritik: bir sineğin "işbirlikçi" mi "saldırgan" mı olduğu kodda yazmaz.
Kurallar (fitness ağırlıkları, kıtlık, paylaşım ödülü) seçilim baskısı yaratır,
davranış oradan **türer**.

### Fazlar

| Faz | İçerik | Durum |
|---|---|---|
| **Faz 1** | Tek tip (klon) ajan + ortam + hareket + yemek + üreme/ölüm | ✅ tamam |
| **Faz 2** | Mutasyon + seçilim + evrimleşebilir recurrent sinir ağı | ✅ **tamam** |
| **Faz 3** | Sosyal kurallar: paylaşma / saldırma, işbirliğinin evrimi | ⏳ iskelet hazır |

`config.yaml` **her zaman en güncel fazın** varsayılanını taşır (şu an Faz 2).
Önceki fazlar `experiments/` altındaki hazır konfigürasyonlarla tek komutta
yeniden üretilir.

---

## 2. Mimari

```
run.py                  CLI girişi: config yükle, koş, logla, özetle
config.yaml             TÜM parametreler. Kod değiştirmeden deney yapılır.
experiments/*.yaml      Hazır deney/kontrol konfigürasyonları (kısmi override)
sinek/
  config.py             YAML yükleme, derin birleştirme, --set ile ezme
  world.py              2B dünya: yemek/tehlike/iklim alanları, algı alanları
  fields.py             blur + gradyan yardımcıları (algının hızlı çekirdeği)
  agent.py              Beden: sensör vektörü ↔ motor vektörü sözleşmesi, fitness
  brains/
    base.py             Brain arayüzü + kayıt defteri (registry)
    reflex.py           Faz 1 beyni: genomdan gelen ağırlıklı refleks devresi
    rnn.py              Faz 2 beyni: küçük evrimleşebilir recurrent ağ
  genome.py             Genom (params + weights) + gaussian mutasyon
  spatial.py            Uzamsal hash (Faz 3 ikili etkileşimleri için)
  persistence.py        Popülasyonu npz olarak kaydet/yükle
  simulation.py         Adım döngüsü + nesil döngüsü + seçilim
  metrics.py            Metrik toplama + CSV (adım ve nesil bazlı)
  render.py             Durum → RGB kare (tek çizici, iki çıkış)
  sinks.py              Kare çıkışı: headless PNG / canlı pygame
  pngwrite.py           Saf Python PNG yazıcı (Pillow gerekmez)
  font3x5.py            HUD yazısı için minik bitmap font
tools/plot_metrics.py   metrics.csv / generations.csv → PNG grafik
tools/benchmark_genomes.py  Evrimleşmiş koloni vs acemi koloni, aynı dünyada
tests/                  unittest — determinizm + Faz 1 + Faz 2 testleri
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
`_left` = sol bileşeni. Beyin mutlak koordinat bilmeden çalışır — evrimleşebilir
bir ağ için şart.

`social` motoru Faz 2'de üretilir ama yok sayılır; Faz 3'te
`>0 → paylaş`, `<0 → saldır` olacak.

### Beyin backend'leri

| `brain.type` | Ne yapar | Genom kullanımı |
|---|---|---|
| `reflex` | Sabit devre, ağırlıklı sensör toplamı | `genome.params` |
| `rnn` | Sızıntılı recurrent ağ, ~10–40 nöron | `genome.weights` (+ `params.wander`) |

```
rnn:  h_t = tanh(W_ih @ s + W_hh @ h_{t-1} + b_h)
      h_t = (1-leak)*h_{t-1} + leak*h_t
      o   = W_ho @ h_t + b_o
```

`W_hh` sineğin **kısa süreli belleği**: "az önce koku daha güçlü müydü?"
bilgisini ancak recurrent bağlantı taşıyabilir. Refleks beynin yapısal olarak
yapamadığı şey budur. `brain.hidden: 12` → 364 ağırlık.

Ağırlık dilimleri genomun üzerine **görünüm (view)** açar; kopya maliyeti yoktur.
Mutasyon her zaman yeni bir dizi bağlar ve beyin çocuk genomundan **sonra**
kurulur, dolayısıyla bayat görünüm oluşmaz.

### Yeni beyin takmak (ör. FlyWire connectome)

```python
from sinek.brains.base import Brain, register

@register("connectome")
class Connectome(Brain):
    @staticmethod
    def genome_size(cfg) -> int:      # genomdan kaç ağırlık istiyorum
        return ...
    def act(self, sensors, rng): ...
    def reset(self): ...              # recurrent durumu sıfırla
```

Sonra `config.yaml` → `brain.type: connectome`. Genom boyutu
`genome_size_for(cfg)` üzerinden kendiliğinden doğru olur; simülasyonun geri
kalanına dokunmak gerekmez.

### Algı neden "alan tabanlı"?

Her sineğin çevresini tek tek taraması yerine dünya, adım başına **bir kez**
bulanıklaştırılmış bir "koku alanı" ve onun gradyanını hesaplar; sinek kendi
hücresindeki değeri O(1) okur (`world.update_food_perception()`).
~20× daha hızlı ve gerçek kemotaksise daha yakın. Tehlike alanları sabit
olduğu için kurulumda bir kez hesaplanır.

### Determinizm

- Tüm rastgelelik **tek** `np.random.default_rng(seed)` üzerinden.
- Ajanlar her adımda sabit sırada (liste sırası = id sırası) işlenir.
- Seçilim `np.argsort(..., kind="stable")` ve `rng.integers` kullanır.
- `sim.state_hash()` konumları **ve genomları** özetler; mutasyon akışı bozulursa
  test yakalar.

```bash
python run.py --check-determinism      # iki koşum, hash'ler eşit olmalı
```

---

## 3. Faz 2: evrim mekaniği

### İki seçilim modu (`evolution.mode`)

| Mod | Nasıl çalışır | Ne zaman |
|---|---|---|
| `steady_state` | Faz 1 ekolojisi. Üreme sürekli/aseksüel; enerji eşiğini aşan bölünür. Seçilim **örtük**: çok yiyen çok bölünür. Boom–bust salınımı korunur. | Ekolojiyi ve popülasyon dinamiğini görmek |
| `generational` | Klasik GA. Sabit uzunlukta nesiller; nesil sonunda **tüm havuz** (yaşayanlar + o nesilde ölenler) fitness'a göre sıralanır, elitizm + turnuva seçilimi ile yeni nesil kurulur, dünya sıfırlanır. | "Ortalama başarı nesiller boyunca artıyor mu" sorusunu temiz ölçmek |

Nesilli modda üreme **otomatik kapatılır** (`_repro_enabled`): iki seçilim
mekanizması aynı anda çalışırsa hangisinin ne yaptığı ölçülemez.

Seçilim havuzuna **ölenler de dahildir**. Dışarıda bırakılırsa "erken ölen hiç
yarışmamış" sayılır ve seçilim ciddi biçimde çarpıtılır.

### Fitness = deneyin asıl düğmesi

```yaml
evolution:
  fitness:
    age: 1.0          # hayatta kalınan adım
    children: 4.0     # bırakılan yavru (generational modda hep 0)
    food_eaten: 8.0   # toplanan yemek birimi
    energy: 0.5       # ölçüm anındaki enerji
    distance: 0.0     # katedilen mesafe
```

Neyin "başarı" sayıldığını kod değil kullanıcı tanımlar. **Dikkat:** sadece
`age` ödüllendirilirse evrim *hareketsizliği* seçer — durmak (0.6 enerji/adım)
hareket etmekten (1.3 enerji/adım) ucuzdur, yani "hiçbir şey yapmayan sinek"
en uzun yaşar. `food_eaten` ağırlığı bu tuzağı kapatır.

### Başlangıç çeşitliliği (`evolution.founder_spread`)

- `0.0` → herkes kurucu genomun klonu (Faz 1 davranışı)
- `1.0` → parametreler dağılır, sinir ağları tamamen bağımsız rastgele

Aradaki değerler doğrusal geçiş yapar
(`w = (1-spread)*kurucu + spread*rastgele`).

### Mutasyon

Parametreler ve ağırlıklar **ayrı oranlarla** mutasyona uğrar
(`mutation_rate` vs `weight_mutation_rate`). Ağırlıklar 364 adet olduğu için
aynı oran kullanılırsa her doğum ağı darmadağın eder.

---

## 4. Nasıl çalıştırılır

```bash
pip install -r requirements.txt          # numpy + PyYAML (pygame opsiyonel)

python run.py                            # config.yaml (Faz 2) ile
python run.py --steps 2000 --viz none    # sadece metrik, en hızlısı
python run.py --viz pygame               # canlı pencere (SPACE: duraklat, Q: çık)
python run.py --seed 7 --name deney7
python run.py --check-determinism
python -m unittest discover -s tests     # 31 test
```

Hazır deneyler (`experiments/README.md`):

```bash
python run.py --config experiments/faz1_klonlar.yaml              # Faz 1 taban çizgisi
python run.py --config experiments/faz2_kontrol_secilimsiz.yaml   # seçilimsiz kontrol
python run.py --config experiments/faz2_surekli.yaml              # sürekli evrim
python run.py --config experiments/faz2_kitlik.yaml               # kıtlık
```

Çıktılar `runs/<name>/`:

```
config_used.yaml    o koşumda gerçekten kullanılan tam config
metrics.csv         adım adım metrikler
generations.csv     nesil bazlı evrim metrikleri (generational modda)
summary.txt         terminal özeti
frames/*.png        görselleştirme kareleri
population.npz      son popülasyonun genomları (--load-genomes ile geri yüklenir)
```

Kaydedilmiş koloniyi yeniden kullanmak (her koşum sonunda otomatik yazılır):

```bash
python run.py --load-genomes runs/faz2/population.npz --name devam
python run.py --load-genomes runs/faz2/population.npz --load-top 20 --name en_iyi20
python tools/benchmark_genomes.py runs/faz2/population.npz --steps 500
```

Grafik:

```bash
python tools/plot_metrics.py runs/faz2                     # adım bazlı
python tools/plot_metrics.py runs/faz2 --generations       # nesil bazlı evrim eğrileri
python tools/plot_metrics.py runs/faz2 runs/kontrol --generations --cols mean_fitness
```

### Kod değiştirmeden deney yapmak

```bash
# evrimin yönünü değiştir: uzun yaşamak değil, çok gezmek ödüllensin
python run.py --set evolution.fitness.food_eaten=0.0 --set evolution.fitness.distance=2.0

# daha büyük beyin
python run.py --set brain.hidden=24 --name buyuk_beyin

# kıtlık
python run.py --set world.food.regrowth_rate=0.003 --name kitlik
```

`--set` noktalı yolu doğrudan config ağacına yazar ve tekrarlanabilir.

---

## 5. Metrikler

### `metrics.csv` (adım bazlı)

| Sütun | Anlamı |
|---|---|
| `step`, `generation` | zaman ekseni |
| `population` | canlı ajan sayısı |
| `births`, `deaths` | o adımdaki doğum/ölüm |
| `death_starved / hazard / old_age` | ölüm nedeni ayrımı |
| `mean_energy`, `std_energy` | koloninin enerji durumu |
| `max_lineage` | en uzun soy zinciri |
| `food_total`, `food_fill`, `food_eaten` | kaynak stoğu ve tüketim |
| `clustering` | Morisita benzeri kümelenme: `>0` sürüleşme, `<0` kaçınma |
| `behavior_diversity` | genom **parametrelerinin** ort. std sapması |
| `weight_diversity` | sinir ağı **ağırlıklarının** ort. std sapması |
| `gp_<parametre>` | her genom parametresinin popülasyon ortalaması — evrimin **yönü** |
| `cooperation_rate` | Faz 3 için ayrılmış |

### `generations.csv` (nesil bazlı, generational modda)

`generation, step, pool, survivors, mean_fitness, median_fitness, max_fitness,
mean_age, mean_food_eaten, best_food_eaten, behavior_diversity,
weight_diversity, gp_<parametre>...`

---

## 6. Sonuçlar

### Faz 1 (seed 42, 3000 adım) — `experiments/faz1_klonlar.yaml`

Özet görseller: **[docs/faz1/](docs/faz1/)**

- **Klonlar aynı davranıyor.** `behavior_diversity = 0.0`; aynı sensör
  girdisinde tüm beyinler aynı motor çıktısını veriyor.
- **Algı-motor döngüsü çalışıyor.** Tam kör kontrol grubuna karşı ajan başına
  besin alımı **×1.15**; yamalar seyrekleştikçe **×1.32**.
- **Kodlanmamış boom–bust salınımı**, sönümlenerek ~300'e oturuyor.
- **Kaynak yamalarına kümelenme** (`crowd_bias = 0` olmasına rağmen).
- Tehlikeden kaçınma çalışıyor; ölüm ~0.

### Faz 2 (seed 42, 8000 adım = 32 nesil)

Tam tablo ve görseller: **[docs/faz2/](docs/faz2/)**

- **Evrim gerçek.** Ortalama fitness 356 → 815 (+129%), ajan başına yenen
  yemek 16.3 → 61.6 (×3.8), nesli tamamlayan 63/120 → 118/120.
- **Kemotaksis sıfırdan evrimleşti.** Evrimleşmiş koloni vs rastgele ağırlıklı
  acemi koloni, aynı dünyada, üreme ve seçilim kapalı: koku gradyanıyla
  hizalanma **0.013 → 0.424 (×32.6)**, hayatta kalma ×2.0, yemek ×2.0.
  Faz 1'in *elle yazılmış* refleks devresi 0.66 hizalanma sağlıyordu — evrim,
  kimse söylemeden, o çözümün ~2/3'ünü kendi buldu.
- **Seçilimsiz kontrol grubu** (`experiments/faz2_kontrol_secilimsiz.yaml`):
  yemek 27.9 (vs 61.6), toplam ölüm 1598 (vs 261), kümelenme 0.130 (vs 0.601).
  Dikkat: sürüklenen kolonide de yemek 16.3 → 27.9 çıkıyor — bu uyum değil,
  ağırlık büyüklüğünün rastgele yürüyüşle artması (doymuş `tanh` = daha
  kararlı hareket). "Bir şeyler iyileşti" tek başına evrim kanıtı değildir.
- **Ödüllendirilmeyen davranış evrimleşmiyor.** Tehlikeden kaçınma *kötüleşti*
  (tehlikede geçen zaman ×1.40): `evolution.fitness` içinde tehlike terimi yok
  ve tehlike kaynaklı ölüm 32 nesilde sadece 155. Risk/ödül gerilimi için
  `world.hazard.avoid_food_patches: false`.
- **`wander` yükseldi** (0.322 → 0.469): daha fazla keşif gürültüsü seçildi.
  Diğer 9 parametreyi `rnn` okumadığı için onlar nötr sürüklenme referansıdır;
  `summary.txt` ikisini ayrı raporlar.

### Kalibrasyon notları

**`food_strength` ölçeği.** Gradyan büyüklüğü, *tam dolu bir dünyada
erişilebilecek en dik gradyana* (`World._reference_gradient()`) bölünerek
normalize edilir. İlk sürümde ölçek `food_scale / food_radius` idi; sinyal
~0.08'de kalıp gezinme gürültüsü altında eziliyordu. Yeni ölçekle gradyanla
hizalanma 0.42 → 0.66'ya çıktı. **Yeni bir sensör eklerken ölçeğini böyle bir
referansa bağlayın, yoksa sensör sessizce ölür.**

**Seçilim baskısı vs çeşitlilik.** `tournament_size: 4` + düşük ağırlık
mutasyonu ile 24 nesilde `weight_diversity` 0.60 → 0.12'ye çöküyordu (erken
yakınsama: arama duruyor). `tournament_size: 3` + `weight_mutation_rate: 0.10`
aynı fitness'a ulaşıp çeşitliliği 0.43'te tutuyor. Uzun koşumlarda bu sütunu
izleyin: 0'a giderse evrim durmuştur.

**Popülasyon büyüklüğü.** 240 sineklik popülasyon 120'likten *daha kötü* sonuç
veriyor (ajan başına yemek 41.6 vs 61.3) — aynı dünyada iki kat rekabet.
Popülasyonu büyütmek GA'yı otomatik iyileştirmez.

---

## 7. Faz 3'e geçerken yapılacaklar

1. `simulation.py` → `_apply_social_rules()`: şu an bilerek
   `NotImplementedError` atıyor. `motors["social"]` işaretine göre
   `self.hash` üzerinden ikili enerji transferi uygulanacak
   (uzamsal hash zaten `_social_enabled` olduğunda kuruluyor).
2. `config.yaml` → `rules.share` / `rules.attack`: ödül, ceza, yarıçap.
3. Metrik: `cooperation_rate` sütunu doldurulacak (paylaşma girişimi /
   toplam sosyal eylem).
   Faz 2'nin kazananlarıyla başlamak için:
   `python run.py --load-genomes runs/faz2/population.npz`
4. **Başarı ölçütü**: paylaşım ödüllendirildiğinde işbirliği oranı yükselmeli;
   kıtlıkta saldırı payı artmalı. Kontrol grubu: aynı seed, `rules` kapalı.

---

## 8. Kod yazarken uyulacak kurallar

- **Parametre kodda değil config'te.** Yeni bir sabit ekliyorsan `config.yaml`'a
  koy ve `cfg.get("yol.anahtar", varsayilan)` ile oku.
- **Rastgelelik `sim.rng`'den.** `random` modülü ya da `np.random.seed`
  kullanma; determinizm testi bunu yakalar.
- **Ajan sırası bozulmasın.** Sözlük/küme üzerinde gezinip ajan işleme.
  Sıralama gerekiyorsa `kind="stable"`.
- **Sensör/motor listesine ekleme yaparsan** `SENSOR_NAMES`/`MOTOR_NAMES`'in
  **sonuna** ekle, mevcut indeksleri kaydırma (kayıtlı genomlar bozulur).
  `N_SENSORS` değişirse `rnn` genom boyutu da değişir — eski genomlar
  yüklenemez, `TinyRNN` bunu sessizce geçmez, `ValueError` atar.
- **Davranış katsayısı beyne gömülmez.** Refleks devresindeki her katsayı
  `genome.params`'tan gelir; yenisini eklerken `config.yaml → genome.params`
  **ve** `evolution.param_bounds`'a da ekle.
- **`Agent.fitness` bir metottur**, property değil: `a.fitness(sim.fitness_weights)`.
- **Testler kendi fazlarını sabitler.** `tests/test_phase1.py` refleks + mutasyon
  kapalı override'ları ile başlar; `config.yaml` varsayılanı ilerlese de Faz 1
  testleri Faz 1'i ölçmeye devam eder.
- **Faz sınırına saygı.** Faz 3 kancası bilerek `NotImplementedError` atıyor;
  sessizce yok saymak yerine yüksek sesle patlaması tercih edildi.
- Test: `python -m unittest discover -s tests` yeşil kalmalı.
