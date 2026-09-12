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
| **Faz 3 — adım 1** | Soyisim + akrabalık sensörü + paylaşma + kontrol grupları | ✅ **tamam** |
| **Faz 3 — adım 1.5** | Hamilton kuralı `r·b/c` taraması; yapısal engelin bulunması | ✅ **tamam** |
| **Faz 3 — adım 2** | `attack` + dört hücreli in/out analizi | ✅ **tamam** |
| **Faz 3 — sağlamlık** | 5 seed'de tekrar; yön sağlam, büyüklük oynak | ✅ **tamam** |
| **Faz 4** | Doğal avcı, melez soyisim, soy-arası ilişki matrisi | ⏳ |

`config.yaml` **her zaman en güncel fazın** varsayılanını taşır (şu an Faz 3).
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
  genome.py             Genom (params + weights + soyisim) + gaussian mutasyon
  physics.py            Sıcak yol için dondurulmuş fizik sabitleri
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
tools/kin_probe.py      Akrabalık sensörü sondası: beyin akrabalığı okuyor mu?
tools/sweep_hamilton.py Hamilton kuralı rejim taraması (her rejim + kontrolü)
tools/parochial_report.py  Dört hücreli in/out matrisi + birlikte hareket
tools/seed_sweep.py     Adım 2'yi çok seed'de tekrarlar (tekrarlanabilirlik tablosu)
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
                mate_fwd, mate_left, crowd,
                kin, near_agent]                    # Faz 3
MOTOR_NAMES  = [turn, thrust, eat, share, attack]   # Faz 3
```

`share` ve `attack` aynı komşuyu hedefler ve **birbirini dışlar**: hangisi
kendi eşiğini daha çok aşıyorsa o gerçekleşir. Böylece "verecek miyim /
alacak mıyım" tek bir karar olarak evrimleşir.

`kin` ve `near_agent` **ayrı** kanallardır. Tek kanalda `{-1, 0, +1}` ile
"akraba mı" ile "menzilde biri var mı" ayrılamaz; o kanala düşen ağırlık
yorumlanamaz hale gelir. Bu ayrımı ilk sürümde yapmamıştım ve sonda
(`tools/kin_probe.py`) ölçümü kirletiyordu.

Sözleşme büyüdüğünde eski genomlar kaybolmaz: `persistence.migrate_weights`
yeni sensör sütunlarını ve motor satırlarını **sıfırla** ekler — ağ yeni girdiyi
başta görmez, davranış birebir korunur, mutasyon zamanla bağlantıyı açar.

Yön sensörleri **egosentrik**: `_fwd` = sineğin baktığı yön bileşeni,
`_left` = sol bileşeni. Beyin mutlak koordinat bilmeden çalışır — evrimleşebilir
bir ağ için şart.

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

### Sıcak yol: `Physics`

`Agent.sense` ve `apply_motors` ajan × adım başına çağrılır. Config ağacını
orada dolaşmak (`cfg.agents.motors.max_turn`) adım başına milyonlarca
`Cfg.__getattr__` üretiyordu — profilde sürenin ~%40'ı. `sinek/physics.py`
config'i kurulumda bir kez düz alanlara açar; skaler `np.clip` de `min/max`
ile değiştirildi. Sonuç: 52 → 23 ms/adım. **Bu fonksiyonlara `cfg` değil
`sim.physics` geçilir.**

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

## 3.5 Faz 3: akrabalık ve işbirliği

### Üç kural (ihlali deneyi geçersiz kılar)

1. **Rol/kast kodlanmaz.** Koşullar kurulur, iş bölümü çıkarsa çıkar.
   `tests/test_phase3.py::test_no_caste_is_hardcoded` kaynakta
   "queen/worker/caste" geçmediğini denetler.
2. **Paylaşım ödüllendirilmez.** `evolution.fitness` içinde paylaşım terimi
   **yoktur**; `Agent.fitness` `given`/`received`/`shares_made` alanlarına
   bakmaz. Test bunu hem config'te hem kodda doğrular. Verenin **net** kaybı
   vardır (aktarılan enerji + `overhead`). Kâr yalnızca dolaylı olabilir.
3. **İşbirliği in-group / out-group ayrı ölçülür.** İttifak kural olarak
   atanmaz; sadece oranlar raporlanır.

### Mekanik

- **Soyisim** (`Genome.surname`): her kurucuya benzersiz, yavru miras alır.
  Sadece soyağacı etiketi — *aynı soyisim genetik özdeşlik değildir*, mutasyon
  zamanla ayırır.
- **`share` motoru**: eşiği aşarsa **en yakın** komşuya enerji aktarır.
  Alıcı hep en yakın komşu olduğu için karar "kime" değil "verecek miyim"dir;
  akrabalık sensörü de aynı komşuyu bildirir, böylece ayrımcılık doğrudan
  ölçülebilir: `P(paylaş | en yakın akraba)` vs `P(paylaş | en yakın yabancı)`.
- Alıcı `energy.max`'ı aşamaz, aşan kısım **boşa gider** — azalan verim,
  altruizmin evrimleşebilmesi için gereken temel.
- Transferler id sırasında ardışık uygulanır (deterministik).

### Kontrol grupları (`rules.kinship.control`)

| Değer | Ne bozar |
|---|---|
| `none` | — (asıl koşum) |
| `random_surname_at_birth` | Etiket **kalıtsal değil**: yavru, yaşayan popülasyondan rastgele bir soyisim alır. Grup büyüklüğü dağılımı korunur, akrabalık bilgisi gider |
| `shuffle_surnames` | Her adım yaşayanlar arasında permütasyon — etiket tanımı gereği bilgisiz. En sert kontrol |
| `scatter_offspring` | Yavru haritaya rastgele doğar: akrabalık bilgisi durur, uzamsal fırsat gider |

`random_surname_at_birth` ilk sürümde `randint(0, N)` çekiyordu; bu neredeyse
herkesi yabancı yapıp `opp_kin` örneğini yok ediyordu ve kontrolün in-group
oranı ölçülemeyecek kadar gürültülü çıkıyordu. Artık **yaşayan popülasyondan**
çekiliyor.

### Soy çeşitliliği ve `split_rate`

Soylar yalnızca tükenebilir (yeni kurucu yoktur), boom–bust darboğazları da
sert: 160×100 dünyada 200 kurucu 6000 adımda **3 etkin soya** düşüyordu.
Herkes akraba olunca in/out ayrımı anlamını yitirir. İki önlem:

- **Daha geniş dünya** (240×150, 24 yama): soylara yerel sığınak bırakır,
  aynı adımda ~13 etkin soy. Faz 1/2'den farklı olmasının sebebi budur.
- **`rules.kinship.split_rate`**: yavrunun soyismi küçük bir olasılıkla yeni
  olur. Yeni bölünen soy, bölündüğü anda ebeveyniyle genetik olarak aynıdır —
  yani etiket akrabalığı **eksik** bildirir. Bu, hipotez lehine değil
  **aleyhine** çalışır; pozitif bulguyu şişiremez, ancak zayıflatır.

Her koşumda `lineage_effective` ve `opp_kin` izlenmelidir: örneklem küçülürse
oran gürültüdür.

### ⚠ Hamilton kuralı bu tasarımda yapısal olarak sağlanamıyordu

Paylaşım muhasebesi: `c = amount + overhead`, `b = min(amount, boşluk) ≤ amount`.
Yani **`b/c ≤ 1` yapısaldır**; `r ≤ 1` de tanım gereği. Hamilton `r·b/c > 1`
ister — doğrusal aktarımla **imkânsız**. 9 rejimlik tarama bunu doğruladı:
ölçülen en yüksek `r·b/c = 0.52` (bkz. [docs/faz3/adim15_hamilton.md](docs/faz3/adim15_hamilton.md)).

Tek kaçış, enerjinin fitness'a dönüşümünün doğrusal olmadığı yer: ölmek üzere
olan bir alıcı. İki ekleme bunu erişilebilir kıldı:

- **`neighbor_need` sensörü** — beyin komşusunun açlığını göremiyordu, o anı
  hedefleyemiyordu. Bilgi kanalı, ödül değil.
- **`rules.share.need_bonus`** — aynı kalorinin aç bir alıcıya daha değerli
  olması (alıcının dönüşüm verimi). Verene hiçbir şey kazandırmaz;
  "paylaşım ödüllendirilmez" kuralı korunur. `0.0` = doğrusal (adım 1 davranışı).

Sonuç: `b/c` 0.73 → 1.16, paylaşım oranı %2.09 → %6.02, kontrolden ayrıştı
(t = +2.48). **Yeni bir sosyal kural eklerken önce `r·b/c`'nin 1'i
geçebildiğini doğrulayın**, yoksa negatif sonuç mekanizmadan değil
muhasebeden gelir.

### Saldırı (`rules.attack`)

Paylaşımla aynı iskelet: en yakın komşuyu hedefler, eşik aşılırsa gerçekleşir,
in/out ayrı ölçülür, enerji katmanlı düzeltme `stratified_kin_bias(action="atk")`
ile aynı fonksiyondan gelir.

**Maliyet sabit, kazanç hedefin enerjisiyle sınırlı** — fakire saldırmak net
zarardır. Bu, "herkes herkese saldırır" dejenere çözümünü engeller.
Saldırı da **ödüllendirilmez**: `attacks_made`, `damage_dealt`, `stolen`
yalnızca ölçüm içindir (`test_fitness_has_no_attack_term`).

### ⚠ `kin_bias` tek başına kanıt değildir

Akrabalar uzamsal kümelenir → kümeler zengin yamalardadır → oradaki sinekler
toktur → **paylaşacak bütçesi olan tok sinektir**. Yani "akrabaya daha çok
paylaşıldı" sonucu hiçbir ayrımcılık olmadan da çıkar.

Ölçüldü: akrabalık sensörünü **okuyamayan** refleks beyinle (ayrımcılık
matematiksel olarak imkânsız) ham `kin_bias` **+3.80 puan** çıkıyor.

İki düzeltme:

1. **`kin_bias_adj`** — verici enerjisine göre 5 katmana ayırıp
   Mantel–Haenszel ağırlığıyla birleştirir. Aynı yapay kurulumda +3.80 → +0.36.
2. **`tools/kin_probe.py`** — ajanları hiç çalıştırmaz. Aynı sensör vektörünü
   beyne iki kez verir, **sadece** akrabalık kanalını değiştirir ve paylaşım
   motorundaki farkı ölçer. Uzamsal etki, enerji, yoğunluk sabit; kalan fark
   saf ayrımcılıktır.

**Her ikisi de mutlak değil, eşleşmiş bir kontrol koşumuna karşı okunur.**

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
| `lineage_count / _effective / _largest` | soy çeşitliliği (etkin sayı = Shannon entropisinin üssü) |
| `share_events`, `share_energy` | paylaşım sayısı ve aktarılan enerji |
| `cooperation_rate` | paylaşım / fırsat |
| `coop_in_group`, `coop_out_group` | `P(paylaş \| akraba)`, `P(paylaş \| yabancı)` |
| `kin_bias` | ham fark — **konfoundlu**, tek başına kullanmayın |
| `kin_bias_adj` | enerji katmanlı düzeltilmiş fark — güvenilen ölçü |
| `opp_kin`, `opp_nonkin` | örneklem büyüklükleri (küçükse oran gürültüdür) |
| `kin_assortment` | `(gözlenen−beklenen)/(1−beklenen)` ≈ Hamilton'un `r`'si |
| `kin_expected`, `kin_observed` | assortment'in taban çizgisi ve gözlemi |
| `bc_ratio` | gerçekleşen `b/c` — doğrusal aktarımda yapısal olarak ≤ 1 |
| `rescue_share` | paylaşımların kaçı ölmek üzere olan birine gitti |
| `attack_events`, `attack_damage`, `attack_kills`, `death_killed` | saldırı muhasebesi |
| `hostility_rate` | saldırı / fırsat |
| `attack_in_group`, `attack_out_group` | `P(saldır \| akraba)`, `P(saldır \| yabancı)` |
| `attack_kin_bias`, `attack_kin_bias_adj` | saldırıda akrabalık ayrımcılığı (ham / düzeltilmiş) |
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

### Faz 3 adım 1 (seed 42, 12000 adım = 24 dönem)

Tam tablo ve görseller: **[docs/faz3/](docs/faz3/)**

- **Paylaşma seçilimle elendi.** Paylaşım oranı %28.2 → %1.0. Beklenen:
  net maliyeti var, fitness'ta karşılığı yok, dolaylı getirisi maliyeti
  karşılamıyor.
- **Akrabalığa yönelik fedakârlık EVRİMLEŞMEDİ.** Ham `kin_bias` +0.37 puan
  (12/12 dönem pozitif) — ama soyisimlerin her adım karıştırıldığı, yani
  etiketin tanımı gereği bilgisiz olduğu kontrolde **+0.63**. Nedensel sonda
  aynı sonucu veriyor: asıl koşum +0.029 (%53.8 akrabayı kayırıyor), anlamsız
  etiketli kontrol +0.104 (%82.4).
- **Kontrolsüz okunsaydı yanlış pozitif raporlanacaktı.** Ham metrik,
  akrabalık sensörünü okuyamayan refleks beyinle bile +3.80 puan veriyor
  (bkz. §3.5, konfound). Faz 3 adım 2'de saldırı metrikleri de aynı
  disiplinle okunmalı.
- **Genom taşıması doğrulandı**: Faz 2 tohumunun sonda farkı tam olarak
  0.000 — yeni sensör sütunu gerçekten sıfırla başlıyor.
- Soy çeşitliliği 300 kurucu → 14 soy (etkin 4.9). Ölçüm için yeterli ama
  daha uzun koşumlarda `lineage_effective` ve `opp_kin` izlenmeli.

### Faz 3 adım 2 (seed 42, 12000 adım = 24 dönem)

Tam tablo: **[docs/faz3/adim2_parochial.md](docs/faz3/adim2_parochial.md)**

Dört hücreli matris (son çeyrek, fırsata koşullu):

| | asıl in-grup | asıl dış-grup | kontrol in | kontrol dış |
|---|---|---|---|---|
| PAYLAŞ | **56.11%** | 21.51% | 4.85% | 4.47% |
| SALDIR | 5.10% | 3.84% | 4.09% | 4.18% |

- **Grup-içi fedakârlık evrimleşti.** Paylaşım in/out oranı ×2.6; düzeltilmiş
  ayrımcılık +28…+57 puan, kontrolde +0.3…+1.1 (≈50× fark). Kontrolün dört
  hücresi birbirinin aynı — kontrol tam olarak yapması gerekeni yaptı.
- **Grup-dışı düşmanlık EVRİMLEŞMEDİ.** Saldırı in-grupta biraz daha yüksek
  (%5.10 vs %3.84); düzeltilmiş saldırı ayrımcılığı kararsız (−2.6 … +3.5) ve
  paylaşımdan ~20× küçük. Saldırı oranı **kontrolde de birebir aynı şekilde**
  yükseliyor (1.3% → 4.1%): saldırı bir strateji olarak evrimleşiyor ama
  **akrabalığa kör**.
- **"İyilik ve öteki'ne kötülük aynı madalyonun iki yüzü" — bu kurulumda
  değil.** Sebep: saldırının kârlılığı hedefin akrabalığına değil
  **zenginliğine** bağlı (maliyet sabit, kazanç hedefin enerjisiyle sınırlı).
  Ayrıca komşuların %84'ü akraba; yabancı zaten nadir.
- Sonda yine simülasyon içi ölçüden **zayıf** çıkıyor (paylaşımda %61.0 vs
  kontrol %56.6). Sonda rastgele sensör uzayında ortalama duyarlılık ölçer;
  gerçek koşumda beyin dar bir bölgede çalışır. İkisi ayrı raporlanır.
- Sınır: etkin soy 4.7'ye düştü (`max_speed 0.20` akrabaları bir arada tutuyor
  — assortment 0.751'i mümkün kılan da, dış-grup örneklemini küçülten de bu).
  Misilleme/hafıza/itibar ve **gruplar arası rekabet** yok; literatürde
  parochial düşmanlık genelde o baskı altında çıkar.

### Faz 3 sağlamlık taraması (5 seed, aynı rejim, her biri kontrolüyle)

Tam tablo: **[docs/faz3/adim2_seed_taramasi.md](docs/faz3/adim2_seed_taramasi.md)**

- **In-grup fedakârlık 5/5 seed'de kontrolden ayrıştı.** `kin_bias_adj`
  asıl +28.02 ± 10.05 puan, kontrol +0.39 ± 0.15; Welch t +10.75 ± 5.33,
  en zayıfı +5.43. Yön sağlam.
- **Dış-grup düşmanlık 4/5 seed'de akrabalığa kör** — adım 2 sonucu tekrarlandı.
- **Büyüklük oynak**: `kin_bias_adj` 11.4–36.1 puan, in-grup paylaşım oranı
  %17.5–%91.3. Tek seed'in mutlak seviyesini "koloninin işbirliği düzeyi"
  diye okumayın; **oran ve yön** raporlanır, mutlak seviye değil.
- seed 42 adım 2'yi birebir tekrarladı — determinizm ve rejim eşleşmesi
  ayrıca doğrulandı (`test_seed_sweep_regime_matches_step2` bunu koruyor).
- **İpucu (kanıt değil):** tek istisna seed 2024, aynı zamanda en düşük
  assortment'a (0.23) ve en yüksek dış-grup fırsat payına (%53) sahip.
  5 nokta üzerinde korelasyon 0.900, ama 2024 çıkarılınca −0.087 — yani
  korelasyon tek noktaya dayanıyor. Sınamak için dış-grup fırsat payını
  doğrudan süpüren bir tarama gerekir.

### Kalibrasyon notları

**Sıcak yol.** `sense`/`apply_motors` içinde config ağacı dolaşmak ve skaler
`np.clip` kullanmak adım süresinin ~%60'ını yiyordu: 52 → 23 ms/adım
(`sinek/physics.py`). Yeni bir ajan-başına-adım fonksiyonu yazarken aynı
tuzağa düşmeyin.

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

## 7. Faz 4'e geçerken yapılacaklar

1. **Doğal avcı**: dünyaya hareketli tehdit. `rules` altında ayrı bir blok;
   `world.hazard` sabit disklerin aksine ajanları takip eder. Gruplar arası
   ortak tehdit, adım 2'de çıkmayan **grup-dışı düşmanlığın** literatürdeki
   tetikleyicisidir — asıl test bu olabilir.
2. **Melez soyisim**: `Genome.surname` tek tam sayı. Faz 4'te X-Y birleşik
   etiket olacak; `lineage_stats`, `kin_assortment` ve kontrol grupları
   etiketi yalnızca **eşitlik** üzerinden kullanır, dolayısıyla etiket tipini
   değiştirmek bu kodu bozmaz — kısmi akrabalık isteniyorsa
   `agent.sense`'teki `kin` hesabı sürekli bir orana çevrilir.
3. **Soy-arası ilişki matrisi**: `opp_kin`/`opp_nonkin` ikili sayımı
   `(soy_i, soy_j)` matrisine genişletilecek. `stratified_kin_bias`
   `action` parametresiyle zaten genel; hücre başına da uygulanabilir.
4. **Gruplar arası rekabet** eklenmeden parochial düşmanlık beklenmemeli
   (bkz. adım 2 sonucu).
5. Adım 2'nin kazananlarıyla başlamak:
   `python run.py --load-genomes runs/faz3b_saldiri/population.npz`

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
- **`sense` / `apply_motors` `cfg` değil `Physics` alır** (`sim.physics`).
  Sıcak yolda config ağacı dolaşılmaz.
- **Fitness'a asla sosyal terim eklenmez.** `given`, `received`, `shares_made`
  yalnızca ölçüm içindir. Ödüllendirilirse işbirliği bulgusu değersizleşir;
  `test_fitness_has_no_sharing_term` bunu bekler.
- **Grup-içi/grup-dışı oranlar kontrol koşumuna karşı okunur**, sıfıra karşı
  değil. Ham `kin_bias` uzamsal kümelenme yüzünden konfoundludur.
- **Testler kendi fazlarını sabitler.** `tests/test_phase1.py` refleks + mutasyon
  kapalı override'ları ile başlar; `config.yaml` varsayılanı ilerlese de Faz 1
  testleri Faz 1'i ölçmeye devam eder.
- **Faz sınırına saygı.** Bilinmeyen bir kural değeri varsayılana düşmez,
  `ValueError` atar; sessizce yok saymak yerine yüksek sesle patlamak tercih edildi.
- **Tek seed sonuç değildir.** Bir bulguyu rapor etmeden önce
  `tools/seed_sweep.py` ile birkaç seed'de tekrarlayın: Faz 3'te yön 5/5
  tuttu ama büyüklükler 3–5× aralıkta oynadı.
- **Bir aracın rejimi bir deney dosyasını taklit ediyorsa test edin.**
  `test_seed_sweep_regime_matches_step2` ikisi ayrışırsa kırmızıya döner.
- Test: `python -m unittest discover -s tests` yeşil kalmalı.
