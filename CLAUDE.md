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
| **Faz 3 — eksen A** | Dış-grup bolluğu düşmanlığı tetiklemiyor; adım 2 daraltıldı | ✅ **tamam** |
| **Faz 3 — eksen B** | Kıtlık saldırıyı hiç artırmadı; H2 de reddedildi | ✅ **tamam** |
| **Faz 4 — adım 1** | Doğal avcı (grup-kör); düşmanlık da sürü işbirliği de çıkmadı | ✅ **tamam** |
| **Faz 4 — tanı** | Rejim çatalı: gerçek ama havzalar eşit değil; ölçülebilir taban bulundu | ✅ **tamam** |
| **Faz 4.5** | Ekoloji borcu: paylaşım enerji yaratıyordu; zincir onarıldı, Faz 3 sonucu tekrarlanmadı | ✅ **tamam** |
| **Faz 4.6** | Korunumlu zeminde `r·b > c` araması: 15 koşulun hiçbiri eşiği geçmedi | ✅ **tamam** |
| **Faz 5** | Karşılıklılık: üç önkoşul sağlandı, yine de evrimleşmedi (0/5) | ✅ **tamam** |
| **Faz 6** | Partner seçimi: dışlama evrimleşti, işbirliği tabandan çıkmadı | ✅ **tamam** |
| **Faz 7** | Çeşitlilik denetimi: taze başlangıç ÇÖZMÜYOR; Faz 5 geçerli zeminde tekrarlandı | ✅ **tamam** |
| **Faz 4 — adım 2** | Melez soyisim, soy-arası ilişki matrisi, gruplar arası rekabet | ⏳ |

`config.yaml` **her zaman en güncel fazın** varsayılanını taşır (şu an Faz 6 —
tek istisna `rules.kinship.radius`, aşağıda §3.11).
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
  predator.py           Faz 4: ortak, dışsal, GRUP-KÖR avcı sürüsü
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
tools/env_sweep.py      Çevresel tarama (eksen A: dış-grup bolluğu, eksen B: kıtlık)
tools/predator_sweep.py Faz 4 avcı 2×2 taraması + D/Ç sınıflandırması
tools/basin_map.py      Rejim havzası haritalama (eşik veriden türetilir)
tools/surplus_probe.py  Paylaşım verici enerji katmanına göre: fazlalık mı, maliyet mi?
tools/selection_probe.py  Enerji → üreme → seçilim zinciri sağlıklı mı (tamamlanmış yaşamlar)
tools/hamilton_probe.py   Hamilton'un b ve c'sini YAVRU cinsinden ölçer (varsaymaz)
tools/encounter_probe.py  Tekrarlı karşılaşma: EPİZOT mu, uzun bitişiklik mi?
tools/partner_report.py   Faz 6 üç kol: önkoşul + asıl ölçüt + politika ölçütü ayrı
tools/exclusion_probe.py  Dışlama: YAPISAL mı BİREYSEL mi; seçilmeyenlerin profili
tools/diversity_report.py Faz 7: ölçüt 1B (etkin soy + dış-grup) ve çeşitliliğin bedeli
tests/                  unittest — determinizm + faz testleri + araç/yöntem testleri
```

### Sensör/motor sözleşmesi

Beden ile beyin arasındaki **tek** bağ iki vektördür:

```
sensors (21 float) ──► Brain.act() ──► motors (5 float)
```

```python
SENSOR_NAMES = [bias, energy, age, food_here, food_fwd, food_left,
                food_strength, hazard_fwd, hazard_left, hazard_near,
                mate_fwd, mate_left, crowd,
                kin, near_agent, neighbor_need,     # Faz 3
                pred_fwd, pred_left, pred_near,     # Faz 4
                partner_known, partner_ledger]      # Faz 5
MOTOR_NAMES  = [turn, thrust, eat, share, attack]   # Faz 3
```

Faz 6'da bu "komşu" artık mekânın dayattığı en yakın komşu değil: menzildeki
en yakın `k` aday bulunur ve hedef genomdaki `pick_*` ağırlıklarıyla **seçilir**
(`rules.partner`). Ağırlıklar 0 iken davranış seçimsiz kolla özdeştir.

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
  olması (alıcının dönüşüm verimi). `0.0` = doğrusal (adım 1 davranışı).

Sonuç: `b/c` 0.73 → 1.16, paylaşım oranı %2.09 → %6.02, kontrolden ayrıştı
(t = +2.48).

### ⚠⚠ DÜZELTME (Faz 4.5): bu "kaçış" enerji üretimiydi

`need_bonus` **alıcıya vericinin kaybettiğinden 4 kata kadar fazla gerçek
enerji** veriyordu: `taken = min(amount·(1+need_bonus·need), boşluk)` ve veren
yalnızca `amount + overhead` ödüyordu. Yani paylaşım **korunumlu değildi** ve
her transfer koloniye net enerji **ekliyordu**. Ölçüldü: %90 işbirliği olan bir
koşumda üretilen enerji yenen yemeğe eşit, %97'de 3.2 katı
([docs/faz45/](docs/faz45/ekoloji_borcu.md)).

Artık `rules.share.need_mode` var:

| mod | davranış |
|---|---|
| **`fitness`** (varsayılan) | **KORUNUMLU**: alıcı en fazla aktarılanı alır; çarpan yalnızca muhasebedeki `b`'ye girer. Dinamiği hiç değiştirmez — yani `b/c ≤ 1` tavanı geri gelir |
| `energy` | eski davranış. Faz 3 adım 1.5 – Faz 4 tanısı arası her şey bu modda üretildi; deney dosyalarına açıkça pinlendi |

`energy_created` sayacı korunumlu modda tam 0'dır
(`test_sharing_conserves_energy_by_default`). **Yeni bir sosyal kural eklerken
önce enerji defterinin tuttuğunu doğrulayın**; `r·b/c`'nin 1'i geçip geçmediği
ancak ondan sonra anlamlı bir sorudur.

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

## 3.6 Faz 4 adım 1: doğal avcı

### Avcı grup-kör olmak ZORUNDA

`PredatorPack._nearest` hedefini **yalnızca mesafeye** göre seçer; soyisme,
enerjiye, yaşa bakmaz. Belirli bir soyu hedefleseydi grup düşmanlığını elle
kurmuş, yani Faz 3'ün 1. kuralını (rol/kast kodlanmaz) ihlal etmiş olurduk.
`tests/test_phase4.py::test_predator_target_is_group_blind` soyisimleri
karıştırıp hedefin değişmediğini doğrular.

### Sürüleşme kodlanmaz, kârlı hale getirilir

Avcı başına adımda **tek vuruş** + bekleme süresi (`cooldown`). N kişilik bir
kümede vurulan olma olasılığınız 1/N'e düşer — seyreltme (dilution / selfish
herd). "Avcı gelince gruplaş" diye bir kural yoktur; gruplaşma yalnızca
kârlı hale gelir, seçilim bulursa bulur.

Avcı ajanlar **hareket ettikten sonra** vurur (`simulation.step` 3.6): kaçmanın
bir anlamı olsun diye.

### ⚠ Kalibrasyonu deneyin TAM UFKUNDA yapın

Avcı gücü önce 1500 adımda kalibre edildi (20 avcı → ölümlerin %23'ü, koloni
tavanda sağlıklı). 12000 adımda aynı ayar **karıştırma kontrolünü tüketti**
(9873. adımda 700 → 0) ve dış-grup fırsat payını %2.7'ye düşürdü. Kısa
kalibrasyon eksik değil, **yanıltıcıydı**.

Yeniden kalibrasyon, sonuç görülmeden ilan edilmiş üç ölçütle yapıldı — ikisi
doğrudan **ölçülebilirliği** korur:

1. hem asıl kol hem karıştırma kontrolü tam süreyi yaşar,
2. son çeyrekte dış-grup fırsat payı ≥ %10,
3. ölümlerin ≥ %10'u avcıya bağlanır.

Bunları birden sağlayan en güçlü baskı seçilir (seed 42'de 12 avcı).

### 2×2 tasarım

| | gerçek etiket | karıştırma kontrolü |
|---|---|---|
| **avcı var** | `faz4_avci` | `faz4_avci_kontrol` |
| **avcı yok** | `faz4_avcisiz` | `faz4_avcisiz_kontrol` |

Her kolun ayrımcılığı **kendi** kontrolüne karşı okunur; iki `t` ancak ondan
sonra kıyaslanır. `tools/predator_sweep.py` bunu yapar ve iki ölçüm hatasını
yüksek sesle bayraklar: kontrol erken bittiyse ("OKUNMAZ") ve dış-grup payı
%10'un altındaysa ("GÜRÜLTÜ").

---

## 3.7 Faz 4 tanı: rejim çatalı ve ölçülebilir taban

Tam rapor: **[docs/faz4tani/tani_bistabilite.md](docs/faz4tani/tani_bistabilite.md)**

### İki durum gerçekten de kararlı — ama havzalar eşit değil

12 seed, yalnızca seed değişerek: işbirliği %4.4–%91.9, ama **11'i %42'nin
üstünde**. Yoğun paylaşım durumu baskın çekim havzası, seyrek toplayıcı durum
nadir. Buna karşılık 2×2 genom takası iki durumun da **kendi kendini
sürdürdüğünü** gösteriyor (seed 42 + 777'nin genomları → %97.3; seed 777 +
42'nin genomları → %17.3). Yani çatal gerçek, havzalar eşit değil.

Havzayı **seed belirlemiyor, popülasyonun kendisi belirliyor**. Erken dinamik
de belirlemiyor: 7. döneme (4000. adım) kadar erken işbirliği ile son çeyrek
arasındaki korelasyon r ≤ +0.42; ayrışma 4000–8000 arasında oluyor.

### Paylaşım toplamayı EZMİYOR

Kişi başı toplama 12 seed'de yalnızca 1.5× aralıkta (VK %13) oynarken paylaşım
41× oynuyor. Korelasyon −0.827 ama etki büyüklüğü yok. "Yumak" foraging'in
yerine geçmiyor, üstüne biniyor.

### Ara rejim yok: sistem ya ölü ya kaçak

`need_bonus` ekseninde geçiş 1.0 ile 2.0 arasında:

| `need_bonus` | işbirliği medyan | seed'ler arası yayılım |
|---|---|---|
| 0.0 | %1.3 | 1.3 puan |
| 1.0 | %2.1 | **0.8 puan** |
| 2.0 | %15.1 | **89.6 puan** ← kritik nokta |
| 3.0 (taban) | %59.4 | 85.5 puan |

Eşikte varyans patlıyor. `overhead` daha zayıf bir kaldıraç; karışma
(`max_speed`) medyanı bandın içine çekiyor ama dış-grup fırsat payını %9.1'e
düşürerek ölçülebilirliği bozuyor. **Bu üç kaldıraçta "her iki davranışın da
yaşadığı" bir ayar yok.**

### ⚠ Popülasyonu sınırlayan şey çevre değil, `agents.max_count`

Popülasyon her koşumun **%99.4'ünde tavanda** (N=700), ~72. adımdan itibaren.
Tavan 3000'e çıkarılınca koloni 3000'i de dolduruyor; yemek yenilenmesi 16.7×
kısılınca popülasyon yine 700. `max_count` config'e "bellek/hız emniyeti" diye
konmuştu; fiilen **Faz 3 ve Faz 4'ün her deneyinde taşıma kapasitesi o olmuş**.

Sonucu: üreme bir slot kuyruğu (~1 doğum/adım, 700 aday), dolayısıyla enerji
fitness'a ancak zayıf dönüşüyor. Bu yüzden **enerji biriminde ölçülen `b/c`
seçilim ölçütü değildir**: `r·b/c` 12 koşumun hepsinde 1'in altında (0.37–0.91)
olmasına rağmen işbirliği %92'ye çıkabiliyor. Eksen B'nin "kıtlık" koşulları da
popülasyonu hiç değiştirmemişti — bireyleri fakirleştirdiler, koloniyi değil.

### Taban: parametre değil, başlangıç durumu

İki durum da kararlı olduğuna göre çözüm doğru durumda **başlamak**.
`experiments/faz4_taban.yaml` + `docs/faz4tani/population_taban.npz`: rejim
Faz 3 adım 2 ile birebir aynı (`test_new_base_changes_only_the_starting_population`),
yalnızca tohum farklı. 5 seed'de işbirliği %10.0–22.7 (yayılım 12.7 puan),
dış-grup fırsat payı %51, etkin soy 7.2, tükenme yok — koşumlardan önce ilan
edilmiş beş ölçütün hepsi geçildi. İşbirliğinin **yukarı doğru yeri var**, yani
bir müdahalenin etkisi tavanda kaybolmaz.

Bir müdahale eklendiğinde ölçüt **yeniden** denetlenmelidir.

---

## 3.8 Faz 4.5: ekoloji borcu ve seçilim zincirinin onarımı

Tam rapor: **[docs/faz45/ekoloji_borcu.md](docs/faz45/ekoloji_borcu.md)**

### Paylaşım korunumlu değildi (§3.5'teki düzeltme)

`need_bonus` alıcıya gerçek fazladan enerji veriyordu. Pompanın büyüklüğü
işbirliğiyle birlikte büyüyor: %4 işbirliğinde üretilen enerji yenen yemeğin
%7'si, %90'da %96'sı, %97'de %321'i. Tanının "kaçak havza"sının (yumak)
mekanizması budur; sınırsız bir iç enerji kaynağı varken çevre bağlayıcı
olamaz.

### Bölüm 1 — çevre artık sınırlıyor

İki yapısal değişiklik: korunumlu paylaşım (`need_mode: fitness`) ve
`max_count: 5000` (bağlayıcı değil). **Yemek arzı değişmedi.**

| | eski | yeni |
|---|---|---|
| tavanda geçen adım | %99.4 | **%0.0** |
| adım başına yanan üreme hakkı | ~456 | **0** |
| denge popülasyonu | 700 (tavan) | **~750 (çevre)** |

N yemek arzına doğru orantılı yanıt veriyor (×0.25 → 215, ×0.40 → 337,
×0.60 → 450, ×1.00 → 750): çevresel sınırlamanın doz-yanıt kanıtı. 5/5 seed
ölçütü geçti.

### Bölüm 2 — zincir gerçekten kırıkmış

`tools/selection_probe.py` tamamlanmış yaşamları toplar. **Yaş kontrol
edilmeden okunamaz**: yaşlı ajan hem çok yer hem çok ürer.

| ölçüm | eski | yeni |
|---|---|---|
| yemek → yavru (ham) | +0.317 | +0.692 |
| **yemek → yavru (yaş kontrollü)** | **+0.047** | **+0.738** |
| hiç üremeyen yetişkin | %67.1 | %43.8 |
| **VERMEK → yavru (yaş + YEMEK kontrollü)** | **+0.114** | **−0.080** |
| ALMAK → yavru (yaş + yemek kontrollü) | +0.437 | +0.319 |

Eski kurulumda çok toplamak üremeye neredeyse hiç dönüşmüyordu ve **vermek
kârlıydı** — "paylaşım ödüllendirilmez" kuralı kodda değil ama sonuçta ihlal
oluyordu. Paylaşım sorularında servet de kontrol edilmeli: yalnız yaş
kontrolüyle iki kurulumda da "vermek kârlı" görünür.

### Bölüm 3 — Faz 3'ün ana bulgusu tekrarlanmadı

Aynı rejim, temiz ekoloji, 5 seed, her biri kendi karıştırma kontrolüyle:

| | eski zemin | temiz ekoloji |
|---|---|---|
| kontrolden ayrıştı | **5/5** | **0/5** |
| `kin_bias_adj` asıl | +28.02 ± 10.05 | +1.27 ± 0.55 |
| `kin_bias_adj` kontrol | +0.39 ± 0.15 | +1.94 ± 0.46 |
| Welch t | +10.75 ± 5.33 | −4.58 ± 4.92 |

Paylaşım oranı %1.1–2.4'e iniyor — Faz 3 adım 1'in (need_bonus = 0) sonucuyla
aynı yer. Ham iç/dış oranı 4 seed'de hâlâ 1'in üstünde (%2.40 / %0.56 = 4.3×)
ama enerji katmanlı ve **kontrole karşı** okunan ölçü hayır diyor — `kin_bias`'in
tek başına neden kanıt olmadığının bir örneği daha.

Yan bulgu: saldırı bu zeminde yabancıya yöneliyor (`atk_t` 4/5 seed'de −2'nin
altında). Temiz ekolojide **düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor**.

---

## 3.9 Faz 4.6: korunumlu zeminde `r·b > c` aranması

Tam rapor: **[docs/faz46/hamilton_arayisi.md](docs/faz46/hamilton_arayisi.md)**

### İki ölçüm tuzağı kapatıldı

1. **`r` etiketten okunamaz.** `kin_assortment` soyisim eşitliğini ölçer; aynı
   soyisim mutasyonla ayrışır, `split_rate` ile ayrılan soylar ayrılma anında
   genetik olarak aynıdır. Yeni metrik `genetic_r`: aktör ile en yakın
   komşusunun **genom** benzerliği (regresyon tanımı, rastgele eşleşmede 0,
   klonlarda 1).
2. **`b/c` varsayılamaz.** `need_bonus` çarpanını muhasebeye koyup "`b/c` = 2.3"
   demek kendi varsayımını ölçmektir. `bc_ratio` (enerji, ≤ 1) ile
   `bc_ratio_fit` (çarpanlı **tahmin**) ayrıldı; asıl ölçüm
   `tools/hamilton_probe.py` ile **yavru cinsinden** yapılır:
   `yavru ~ yaş + yemek + VERİLEN + ALINAN`. Ölçüm varsayımı çürüttü:
   tahmin 2.0–2.9, **ölçülen 0.64–1.48**.

### Sonuç: eşik aşılamıyor, ve nedeni yapısal

15 dürüst koşul (hepsinde enerji korunumu TAM), `r·b/c` aralığı **0.475–0.989**,
**1'i geçen 0/15**.

- **`b/c` kolu yapısal tıkalı**: `c = amount + overhead`, `b ≤ amount` ⇒ enerji
  `b/c ≤ 1`. Azalan verimin ölçülen gerçek payı yalnızca %10–48.
- **`r` kolu ekolojik tıkalı**: 0.89'un üstü için hareketi daha da kısmak
  gerekiyor, o da koloniyi çökertiyor (`max_speed` 0.02 → N = 17).
- **İkisi birlikte büyümüyor**: korelasyon(`r`, `b/c`) = **−0.51**. Akrabaları
  sıkıştırmak `r`'yi ×2.09 artırırken `b/c`'yi 1.48 → 0.98'e düşürüyor.

Kontrollü evrim testi (en iyi ölçülebilir nokta, `r·b/c` = 0.901, 5 seed):
ayrışma **3/5** (ölçüt ≥2/3 istiyordu), etki **0.16 puan** — Faz 3'ün pompalı
zemininde bu fark +28 puandı. `r·b/c` = 0.989'a çıkan koşul ise dış-grup
payını %3–9'a düşürüp **ölçülemez** hale geldi.

### ⚠ Kaldıraç beklentinin tersine çıktı

`min_donor_energy` 10 → 100 ("yalnız tok olan versin, maliyet düşsün"): `ĉ`
düşmedi, **`b̂` düştü** (0.0126 → 0.0083) ve `b/c` 0.98 → 0.64'e indi. Paylaşım
fırsatları zaten iyi durumdaki çiftlere daraldığı için. Ölçülmeseydi ters
raporlanacaktı.

### Yan bulgu

Saldırı 5/5 seed'de yabancıya yöneliyor (`atk_t` −6.7…−14.7) — korunumlu
zeminde **düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor**. Faz 4.5'in yan
bulgusu farklı bir koşulda tekrarlandı.

---

## 3.10 Faz 5: tanıma, hafıza ve karşılıklılık

Tam rapor: **[docs/faz5/karsiliklilik.md](docs/faz5/karsiliklilik.md)**

### Üç önkoşul ÖNCE garanti edilir

Karşılıklılık (Axelrod) tekrarlı karşılaşma + tanıma + hafıza ister. Üçü
olmadan "karşılıklılık reddedildi" denemez; doğru cümle "koşul yoktu"dur.

**⚠ Epizot ≠ adım.** Bir sinek 100 adım aynı komşunun yanında durursa bu **tek**
karşılaşmadır. `tools/encounter_probe.py` ikisini ayırır: taban ekolojide
adım-tekrarı %95.0 (şişirilmiş) ama epizot-tekrarı %29.1, ajanların **%50.6**'sı
aynı bireyle ≥3 **ayrı** buluşma yaşıyor (ölçüt %30) — zemin var, ekolojiyi
değiştirmeye gerek kalmadı. Mekânı sıkıştırmak zemini **düşürüyor** (%28.4):
uzun bitişiklik epizot değildir.

### Mekanik: kapasite verilir, kural verilmez

`Agent.ledger` — partner kimliği → geçmişin net işareti. **Alıcı** kaydeder
(enerji aldıysa `+`, saldırı yediyse `−`); kapasite 16, tahliye deterministik.
İki yeni sensör: `partner_known`, `partner_ledger`.

**"Karşılık ver" diye bir kural YOKTUR.**
`tests/test_phase5.py::test_memory_is_information_not_rule` kaynakta defter
bayraklarının (`owes`/`grudge`) yalnızca ölçüm sayaçlarına gittiğini, hiçbir
karar dalına girmediğini denetler.

### ⚠ Kontrol tasarımı: örneklemi yok eden kontrol geçersizdir

İlk kontrolüm `shuffle_identity` idi (tanıma kimlikleri karışır). Ölçüldüğünde
defteri pozitif fırsat **17 751 → 417** (43× küçük): bilgi mi örnek mi
kayboldu ayırt edilemez. Faz 3'te `random_surname_at_birth`'ün ilk sürümündeki
hatanın aynısı.

**Asıl kontrol `shuffle_ledger`**: değerler ajanın **kendi** partnerleri
arasında karıştırılır. Aynı sayıda partner, aynı değerler; yalnızca "hangi
partner hangi değere sahip" bilgisi gider. Örneklem korunur (%6.4–10.5 vs
%4.3–10.8).

### Sonuç: karşılıklılık evrimleşmedi

5 seed, her biri kendi eşleşmiş kontrolüyle:

| ölçü | sonuç |
|---|---|
| karşılıklılık ayrıştı | **0/5** (`t` = −0.94 ± 1.56; iki seed'de kontrol daha yüksek) |
| misilleme ayrıştı | **1/5** (ölçüt ≥4/5) |
| enerji korunumu | 10/10 koşumda tam |

**Misilleme görüntüsü tamamen konfound**: hafızalı kolda `retal_bias_adj`
+4.3…+8.0 puan, ama kontrolde de +4.3…+6.9. Sıfıra karşı okunsaydı yanlış
pozitif raporlanacaktı.

**Kanal tutarlı biçimde okunmuyor**: nedensel sonda hafızalı kolda +0.038
(3/5 pozitif), kontrolde +0.030 (4/5). ⚠ Yalnızca seed 42'ye bakılsaydı
(+0.083 vs +0.033) "kanal okunuyor" denecekti.

### İki negatif bağımsız olmayabilir (hipotez)

Paylaşımın taban oranı ~%1. Karşılıklılığın seçilebilmesi için önce
**paylaşımın kendisinin** yeterince sık olması, yani "bana veren" diye bir
sınıfın oluşması gerekir. Faz 4.6 paylaşımın neden bu kadar nadir olduğunu
gösterdi (`r·b/c < 1`). Yani karşılıklılık, **üzerine kurulacağı işbirliği
olmadığı için** başlayamıyor olabilir. Ölçülmedi.

---

## 3.11 Faz 6: partner seçimi

Tam rapor: **[docs/faz6/partner_secimi.md](docs/faz6/partner_secimi.md)**
Ölçüt (koşumlardan önce yazıldı): **[docs/faz6/olcut.md](docs/faz6/olcut.md)**

### Mekanik: seçme yeteneği verilir, politika verilmez

Faz 5'e kadar hedef **her zaman en yakın** komşuydu — kiminle paylaşacağını
mekân dayatıyordu. `rules.partner.enabled` ile menzildeki en yakın `candidates`
aday bulunur (`spatial.candidates`) ve hedef genomdan gelen beş ağırlıkla
puanlanır:

```
skor = pick_kin·kin + pick_ledger·defter + pick_need·ihtiyaç
     + pick_energy·enerji + pick_dist·(−mesafe)
```

Beş ağırlık `genome.params`'ta, `param_bounds`'ta sınırlı, **0.0'dan başlar** ve
mutasyona uğrar. Hepsi 0 iken skor eşittir, beraberliği mesafe bozar → davranış
seçimsiz kolla **özdeş** (`test_zero_weights_match_no_choice` state_hash ile
sabitler). **"İyi partner seç" diye bir kural yoktur**
(`test_choice_policy_is_not_hardcoded` skorda elle yazılmış katsayı aramaz).

Kontroller: `enabled: false` (seçimsiz, Faz 5'in birebir aynısı) ve
`control: random` (havuz var, seçim rastgele — "yetenek mi akıllı kullanım mı").

### ⚠⚠ Mekanik iki ayrı nedenle SESSİZCE ölüydü

İlk parti seçim kolunu seçimsiz kolla **birebir aynı** `state_hash`'te verdi:

1. **`load_population` yeni parametreleri yüklemiyordu.** Ağırlık taşıması
   (`migrate_weights`) Faz 2'den beri vardı ama **parametre** taşıması yoktu;
   `mutate` de mevcut anahtarlar üzerinde gezdiği için `pick_*` asla mutasyona
   uğramadı. Artık config varsayılanlarıyla ekleniyor ve
   `meta["migrated"]["new_params"]` ile **raporlanıyor**.
2. **Aday havuzu ortalama 1.35 kişi.** `kinship.radius = 2.5`'te çoğu ajanın
   menzilinde tek komşu var. **Seçenek yoksa seçim de yoktur.**

Buradan çıkan önkoşul (Faz 5'in "üç önkoşul" disiplininin aynısı): ortalama
havuz **≥ 2.0** ve kararların **≥ %50'si çok adaylı** (`pool_multi` sütunu).
Menzil tarandı, ölçütü geçen **en küçük** değer `radius = 5.0` ve **üç kola da
aynı** uygulandı. `experiments/faz6_secim.yaml` bunu pinler;
`config.yaml` varsayılanı **2.5'te bırakıldı** çünkü Faz 1–5'in bütün taban
çizgileri o menzilde ölçüldü — varsayılanı oynatmak eski deney dosyalarını
sessizce başka bir deneye çevirirdi (rejim testi ikisini karşılaştırır).

### Sonuç: işbirliği kurulmadı, ama dışlama evrimleşti

5 seed × 3 kol, 12000 adım, `docs/faz5/population_hafiza.npz` tohumundan:

| ölçüt | sonuç |
|---|---|
| korunum | `energy_created` = 0, **15/15** koşum |
| ölçülebilirlik | ❌ dış-grup payı %0.1–2.0, etkin soy ~1 → **akrabalık kanadı okunmaz** |
| **işbirliği tabanı aştı** | ❌ kontrolden ayrışma 3/5, taban bandından (%0.6–2.4) çıkma **0/5** |
| rastgele seçim de aynısını yapıyor | **4/5** seed → artışın kaynağı politika değil **havuzun varlığı** |
| dışlama politikası evrimleşti | ✅ bireysel dışlama %12–37, rastgelede %6.4–7.4 (**5/5**) |
| ama "iyi vericiyi" seçmiyor | defter oranı medyan 1.06, rastgelede 1.24 |

Yan bulgu: havuz eklenince **saldırı paylaşımdan daha çok büyüyor**
(medyan ×2.31 vs ×1.23, 4/5 seed). Faz 4.5/4.6'nın asimetrisi üçüncü kez
tekrarlandı: korunumlu zeminde düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor.

### ⚠ Aynı ölçü, referansa göre ZIT işaret

`pick_ledger_sel` (seçilen − **en yakın**) çoğu seed'de negatif; sondanın
"seçilen − **seçilmeyen**" karşılaştırması seed 42'de pozitif. Çelişki yok:
en yakın komşu, tekrarlı bitişiklik yüzünden havuz ortalamasından daha sık
defteri pozitiftir. Politika yoksa seçilecek olan en yakındır, dolayısıyla
**politikanın katkısı ancak en yakına karşı** izole edilir. Havuz ortalamasına
karşı okunan seçicilik, politika hiç yokken bile +0.05 çıkıyor (ölçüldü).

### Üç mekanizma da elendi

Akrabalık (Faz 4.6), karşılıklılık (Faz 5), partner seçimi (Faz 6) — üçü de
önkoşulları **ölçülerek** sağlandıktan sonra reddedildi. Faz 6'da ayrıca
yeteneğin **kullanıldığı** gösterildi (dışlama 5/5), yani bu negatif "mekanik
ölü kaldı" değil, "mekanik çalıştı ve işbirliği üretmedi".

Hipotez (ölçülmedi): seçilecek "iyi verici" sınıfı fiilen yok — defteri pozitif
aday payı %2.7–17.8, çoğu seed'de %10'un altında. Partner seçimi de,
karşılıklılık gibi, **üzerine kurulacağı işbirliği olmadığı için**
başlayamıyor olabilir.

---

## 4. Nasıl çalıştırılır

```bash
pip install -r requirements.txt          # numpy + PyYAML (pygame opsiyonel)

python run.py                            # config.yaml (Faz 2) ile
python run.py --steps 2000 --viz none    # sadece metrik, en hızlısı
python run.py --viz pygame               # canlı pencere (SPACE: duraklat, Q: çık)
python run.py --seed 7 --name deney7
python run.py --check-determinism
python -m unittest discover -s tests     # 149 test
```

Hazır deneyler (`experiments/README.md`):

```bash
python run.py --config experiments/faz1_klonlar.yaml              # Faz 1 taban çizgisi
python run.py --config experiments/faz2_kontrol_secilimsiz.yaml   # seçilimsiz kontrol
python run.py --config experiments/faz2_surekli.yaml              # sürekli evrim
python run.py --config experiments/faz2_kitlik.yaml               # kıtlık
python run.py --config experiments/faz3b_saldiri.yaml             # Faz 3 adım 2
python run.py --config experiments/faz4_avci.yaml                 # Faz 4 doğal avcı
```

Faz 4'ün **ölçülebilir tabanı** (tohum zorunlu, yoksa avcısız koldan farksız):

```bash
python run.py --config experiments/faz4_taban.yaml \
  --load-genomes docs/faz4tani/population_taban.npz --seed 42
python tools/basin_map.py --seeds 1 7 42 123 777 --out runs/havza.jsonl
python tools/basin_map.py --summary runs/havza.jsonl
```

Faz 4.5'in **temiz ekolojisi** (korunumlu paylaşım + bağlayıcı olmayan tavan):

```bash
python run.py --config experiments/faz45_ekoloji.yaml \
  --load-genomes docs/faz4tani/population_taban.npz --seed 42
python tools/selection_probe.py --steps 8000   # enerji -> ureme -> secilim
python tools/hamilton_probe.py --steps 8000 \
  --set agents.motors.max_speed=0.05 --set rules.share.overhead=0.0   # r, b, c
```

Faz 5 (tanıma + hafıza; karşılıklılık ölçümü):

```bash
python tools/encounter_probe.py --steps 4000            # önkoşul 1: EPİZOT tekrarı
python run.py --config experiments/faz5_hafiza.yaml \
  --load-genomes docs/faz45/population_ekoloji.npz --seed 42
# ASIL kontrol — örneklemi korur, yalnızca bilgiyi siler:
python run.py --config experiments/faz5_hafiza.yaml --seed 42 --viz none \
  --set rules.memory.control=shuffle_ledger --name f5_kontrol
python tools/kin_probe.py runs/f5_kontrol/population.npz \
  --channel partner_ledger --set rules.memory.enabled=true
```

Faz 6 (partner seçimi; üç kol, hepsi Faz 5 tohumuyla ve **aynı** menzille):

```bash
for k in secim secimsiz rastgele; do
  case $k in
    secim)    A="" ;;
    secimsiz) A="--set rules.partner.enabled=false" ;;
    rastgele) A="--set rules.partner.control=random" ;;
  esac
  python run.py --config experiments/faz6_secim.yaml \
    --load-genomes docs/faz5/population_hafiza.npz --seed 42 --viz none $A \
    --name f6_${k}_s42
done
python tools/partner_report.py --seeds 42 7 123 1 777
# Dislama: politikanin kendi katkisi, ayni genomlarla rastgele secime karsi
python tools/exclusion_probe.py --steps 3000 --control none \
  --load runs/f6_secim_s42/population.npz
python tools/exclusion_probe.py --steps 3000 --control random \
  --load runs/f6_secim_s42/population.npz
```

Faz 4'ün 2×2'si (dört kol da Faz 2 tohumuyla, her biri kendi kontrolüyle):

```bash
for k in avci avci_kontrol avcisiz avcisiz_kontrol; do
  python run.py --config experiments/faz4_$k.yaml \
    --load-genomes docs/faz2/population.npz --seed 42 --viz none
done
python tools/predator_sweep.py --from-runs \
  runs/faz4_avci runs/faz4_avci_kontrol runs/faz4_avcisiz runs/faz4_avcisiz_kontrol \
  --seed-label 42
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
| `bc_ratio` | **ENERJİ** birimi `b/c` — korunumlu aktarımda yapısal olarak ≤ 1 |
| `rescue_share` | paylaşımların kaçı ölmek üzere olan birine gitti |
| `attack_events`, `attack_damage`, `attack_kills`, `death_killed` | saldırı muhasebesi |
| `hostility_rate` | saldırı / fırsat |
| `attack_in_group`, `attack_out_group` | `P(saldır \| akraba)`, `P(saldır \| yabancı)` |
| `attack_kin_bias`, `attack_kin_bias_adj` | saldırıda akrabalık ayrımcılığı (ham / düzeltilmiş) |
| `death_predator`, `predator_strikes`, `predator_kills` | avcı muhasebesi |
| `predation_risk` | kişi başı avlanma baskısı (öldürme / ajan) |
| `forage_per_capita`, `share_per_capita` | ajan-adım başına **mutlak** toplama / aktarım (oran değil) |
| `energy_created` | paylaşımın yarattığı/yok ettiği net enerji — korunumlu modda **tam 0** |
| `genetic_r`, `genetic_r_pairs` | Hamilton'un `r`'si: aktör–komşu **genom** benzerliği (etiket değil) |
| `bc_ratio_fit` | `need_bonus` çarpanlı `b/c` **tahmini** — bir varsayım, kanıt değil |
| `recip_bias`, `recip_bias_adj` | karşılıklılık: `P(paylaş \| defter +)` − `P(paylaş \| defter ≤0)` (ham / enerji katmanlı) |
| `retal_bias_adj` | misilleme: `P(saldır \| defter −)` − `P(saldır \| defter ≥0)`, katmanlı |
| `opp_ledger_pos/neg`, `ledger_pos_share` | defter örneklem büyüklükleri (küçükse oran gürültüdür) |
| `immigrants` | Faz 7: taze kurucu genomla doğan yavru sayısı (etiket değil GENOM çeşitliliği) |
| `pool_size` | ortalama aday havuzu (Faz 6) — 1'e yakınsa **seçim diye bir şey yoktur** |
| `pool_multi` | kararların kaçı ≥2 adaylıydı — seçimin ÖNKOŞULU (ortalama tek başına yetmez) |
| `pick_not_nearest` | seçim en yakını atladı mı (yetenek gerçekten kullanılıyor mu) |
| `pick_kin_sel`, `pick_ledger_sel` | seçicilik: seçilen − **EN YAKIN** (politika yoksa 0) |
| `pick_kin_sel_raw`, `pool_kin_rate` | seçilen − havuz ortalaması — **KONFOUNDLU**, kanıt değil |
| `repro_blocked`, `at_cap` | tavan yüzünden yanan üreme hakkı / popülasyon tavana değdi mi |
| `gp_<parametre>` | her genom parametresinin popülasyon ortalaması — evrimin **yönü** |
| `cooperation_rate` | Faz 3 için ayrılmış |

### `generations.csv` (nesil bazlı, generational modda)

`generation, step, pool, survivors, mean_fitness, median_fitness, max_fitness,
mean_age, mean_food_eaten, best_food_eaten, behavior_diversity,
weight_diversity, food_fill, population, clustering, deaths, births,
death_predator, predator_strikes, predator_kills, predation_risk,
lineage_*, coop_*, attack_*, kin_*, opp_*, gp_<parametre>...`

Faz 4'te `clustering` ve avcı sütunları dönem satırına taşındı: **yan etkiler
ölçülmeden** "avcı şunu üretti" denemez.

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

⚠⚠ **Bu bölüm ve aşağıdaki bütün `need_bonus > 0` sonuçları, paylaşımın
enerji ÜRETTİĞİ bir dünyada ölçüldü (§3.5 düzeltmesi).** Her kolun kendi
kontrolüne karşı okunması geçerliydi, ama temel bulgu — in-grup fedakârlığın
evrimleşmesi — korunumlu ekolojide **tekrarlanmadı** (5/5 → 0/5 seed, §3.8).

Dört hücreli matris (son çeyrek, fırsata koşullu):

| | asıl in-grup | asıl dış-grup | kontrol in | kontrol dış |
|---|---|---|---|---|
| PAYLAŞ | **56.11%** | 21.51% | 4.85% | 4.47% |
| SALDIR | 5.10% | 3.84% | 4.09% | 4.18% |

- **Grup-içi fedakârlık evrimleşti.** Paylaşım in/out oranı ×2.6; düzeltilmiş
  ayrımcılık +28…+57 puan, kontrolde +0.3…+1.1 (≈50× fark). Kontrolün dört
  hücresi birbirinin aynı — kontrol tam olarak yapması gerekeni yaptı.
- **Grup-dışı düşmanlık bu rejimde evrimleşmedi.** Saldırı in-grupta biraz
  daha yüksek (%5.10 vs %3.84); düzeltilmiş ayrımcılık kararsız ve
  paylaşımdan ~20× küçük. Saldırı oranı kontrolde de aynı şekilde yükseliyor.
  ⚠ **DÜZELTME (eksen A):** bu, *bu taban rejime özgüymüş*. Dünya
  parametreleri oynatıldığında 12 koşumun 10'unda saldırı yabancıya yöneldi;
  kör kalan tek koşul dokunulmamış taban rejimdi. "Bu kurulumda düşmanlık
  evrimleşmiyor" genellemesi fazla genişti — bkz.
  [docs/faz3/eksenA_disgrup_bollugu.md](docs/faz3/eksenA_disgrup_bollugu.md).
- Sonda yine simülasyon içi ölçüden **zayıf** çıkıyor (paylaşımda %61.0 vs
  kontrol %56.6). Sonda rastgele sensör uzayında ortalama duyarlılık ölçer;
  gerçek koşumda beyin dar bir bölgede çalışır. İkisi ayrı raporlanır.
- Sınır: etkin soy 4.7'ye düştü (`max_speed 0.20` akrabaları bir arada tutuyor
  — assortment 0.751'i mümkün kılan da, dış-grup örneklemini küçülten de bu).
  Misilleme/hafıza/itibar ve **gruplar arası rekabet** yok; literatürde
  parochial düşmanlık genelde o baskı altında çıkar.

### Faz 3 sağlamlık taraması (5 seed, aynı rejim, her biri kontrolüyle)

Tam tablo: **[docs/faz3/adim2_seed_taramasi.md](docs/faz3/adim2_seed_taramasi.md)**

⚠⚠ Bu tarama da `need_mode: energy` dünyasındadır; temiz ekolojideki
karşılığı 0/5'tir (§3.8).

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

### Faz 3 eksen A — dış-grup bolluğu (6 koşul × 2 seed, her biri kontrolüyle)

Tam tablo: **[docs/faz3/eksenA_disgrup_bollugu.md](docs/faz3/eksenA_disgrup_bollugu.md)**

- **H1 reddedildi.** Dış-grup fırsat payı ile saldırı ayrımcılığı arasında
  ilişki yok (r = −0.133, R² = 0.018). En güçlü düşmanlık (`atk_t` −18.04)
  en DÜŞÜK dış-grup payına (%4.8) sahip koşumda.
- **Adım 2'nin "saldırı akrabalığa kör" bulgusu taban rejime özgü.**
  12 koşumun 10'u (5 farklı koşulun hepsi) yabancıya yöneldi; kör kalan tek
  koşul `A1_taban`. Ölçüm yanlış değildi, genelleme fazla genişti.
- **Eşik hikâyesi yok.** `A1_taban`/s42 (assortment 0.767) kör,
  `A2_tam_karisma`/s42 (0.768) yabancıya — aynı assortment, zıt karar.
- **Kendi taramamda konfound:** eksen A kaldıraçları yemek dengesini de
  oynattı (%22.7–%49.4) ve yemek doluluğu `atk_t`'nin en güçlü tek
  yordayıcısı çıktı (+0.502). Eksen B artık kasıtlı süpürülmeli.
- Çoklu regresyon (n=12, 3 tahminci, R² = 0.424) zayıf; tahminciler arası
  bağımlılık yüksek (dış-grup ~ soy +0.875). Söylenebilecek tek net şey
  H1'in reddi.

### Faz 3 eksen B — kaynak kıtlığı (3 seviye × seed 42, her biri kontrolüyle)

Tam tablo: **[docs/faz3/eksenB_kitlik.md](docs/faz3/eksenB_kitlik.md)**

- **H2 reddedildi.** Kişi başı kaynak girdisinde **16 kat** aralık tarandı
  (0.573 → 0.036); saldırı üç seviyede de taban rejimin (%4.42) *altında*
  kaldı (%1.98 / %3.37 / %3.11). Koloni hiçbirinde çökmedi.
  **D/Ç ayrımı gündeme bile gelmedi** — kıtlık saldırganlığı hiç hareket
  ettirmiyor.
- **`food_fill` koşullar arası geçersizmiş.** Bir orandır ve kapasite koşula
  göre değişir: `B_cok_kit` yamaları 24→14 indirdiği için en kıt koşul en
  **yüksek** doluluğu (%59.4) gösterdi. Doğru değişken **kişi başı kaynak
  girdisi** (`yenilenme × kapasite / N`).
- **Pooling A+B işe yaradı:** yemek ile assortment artık ayrık (r = +0.023),
  yani tek eksende yapılamayan ayrıştırma mümkün oldu.
- **Ama hiçbir çevresel skaler kararı öngörmüyor.** n=15'te kör (4) ve
  yabancıya (11) sınıfları assortment'ta (0.216–0.768 vs 0.221–0.768) ve
  dış-grup payında tamamen örtüşüyor. Dört değişkenli regresyon R² = 0.511
  ama düzeltilmiş R² ≈ 0.32 ve `assortment ~ dış_pay` −0.822 bağımlı.
- ⚠ **Ara raporda verdiğim "düşük assortment → yabancıya" örüntüsü yanlıştı.**
  `B_cok_kit` assortment 0.216 (en düşük) ile **kör**. Örüntü yok.

### Faz 4 adım 1 — doğal avcı (3 seed × 2×2, her kol kendi kontrolüyle)

Tam tablo: **[docs/faz4/adim1_avci.md](docs/faz4/adim1_avci.md)**

- **Avcı dış-grup düşmanlığı ÜRETMEDİ.** `atk_t` avcılı kolda −3.55, avcısız
  kolda −5.52 — avcı altında saldırı yabancıya *daha az* yöneliyor. Saldırı
  seviyesi de 3 seed'in yalnızca birinde arttı ve orada akrabalığa **kör**
  kaldı (D/Ç: Ç, ayrım gütmeyen artış).
- **In-grup ayrımcılığını güçlendirmedi; SİLDİ.** Paylaşım patlıyor (seed 42:
  %6.9 → %97.1) ama **in ile dış eşit** (%97.8). Aynı patlama etiketin
  bilgisiz olduğu kontrolde de var (%2.6 → %53.5) → süren şey akrabalık değil
  **yoğunluk**. `share_t` avcılı +4.46, avcısız +7.35. Nedensel sonda da aynı
  yönde: paylaşım farkı avcılı kolda +0.0087, avcısız kolda +0.0548.
- **Fedakârlık ile düşmanlık avcı altında BAĞLANMADI.** Dönemler arası
  `coop_in × attack_out` r: avcılı −0.24, avcısız +0.01; işaret seed'den
  seed'e dönüyor ve karıştırma kontrolünde de benzer değerler çıkıyor.
- **Koloni iki kararlı duruma sahip**: "seyrek toplayıcı" ve "yoğun paylaşım
  yumağı". Yumak avcısız kollarda ve bilgisiz kontrollerde de çıkıyor;
  koşumlar arası büyüklük farkının çoğunu avcı değil bu **havza seçimi**
  açıklıyor. 20 avcılı partide kontrolün tükenmesi bunun uç hâliydi.
  ⚠ **DÜZELTME (tanı taraması):** burada "iki kararlı rejim arasında
  salınıyor" demiştim; 3 seed için doğru görünüyordu. 12 seed'de havzalar
  **eşit değil** — ortak başlangıçtan 11/12 koşum yumağa gidiyor, seyrek durum
  nadir ve adım 1'in seed 42'si tam o nadir koşumdu. Bkz. §3.7.
- **Faz 3 adım 2'nin seed 42 "saldırı kör" bulgusu tekrarlanmadı**: sensör
  sözleşmesi 16 → 19'a çıkınca aynı seed'in avcısız kolu `atk_t = −10.43`
  veriyor. Eksen A'nın uyarısı bir kez daha doğrulandı.
- Yan etkiler (avcılı vs avcısız, seed 42): kümelenme 0.474 → 0.989, etkin soy
  9.53 → 2.81, dış-grup payı %57.9 → %22.8, yemek doluluğu 0.239 → 0.883.
  Avcı yalnızca tehdit eklemiyor; bunlardan ikisi **ölçümün kendisini** bozuyor.

### Faz 4 tanı — rejim çatalı (51 koşum: 12 seed harita + 8 koşul × 5 seed + takas)

Tam tablo: **[docs/faz4tani/tani_bistabilite.md](docs/faz4tani/tani_bistabilite.md)**

- **Çatal gerçek ama havzalar eşit değil.** Ortak başlangıçtan 12 seed'in 11'i
  yoğun paylaşım durumuna gidiyor; seyrek toplayıcı durum nadir. Yine de genom
  takası iki durumun da kendi kendini sürdürdüğünü gösteriyor.
- **Havzayı popülasyon belirliyor, seed değil.** seed 42 + 777'nin genomları
  → %97.3; seed 777 + 42'nin genomları → %17.3. Erken dinamik de öngörmüyor
  (4000. adıma kadar r ≤ +0.42).
- **"Paylaşım toplamayı eziyor" hipotezi reddedildi.** Paylaşım 41× oynarken
  kişi başı toplama yalnızca 1.5× oynuyor.
- **Ara rejim yok.** `need_bonus` 1.0 → 2.0 → 3.0 boyunca işbirliği
  %2.1 → %15.1 → %59.4, yayılım 0.8 → 89.6 → 85.5 puan. Eşikte varyans
  patlıyor; düşük yayılımlı tek ayarlar paylaşımın söndüğü ayarlar.
- **⚠ Yapısal bulgu: popülasyonu `agents.max_count` sınırlıyor, çevre değil.**
  Adımların %99.4'ü tavanda; tavan 3000'e çıkınca koloni 3000'i de dolduruyor,
  yemek 16.7× kısılınca yine 700. Üreme bir slot kuyruğu olduğu için enerji
  fitness'a zayıf dönüşüyor — `r·b/c` 12 koşumun hepsinde 1'in **altında**
  (0.37–0.91) olmasına rağmen işbirliği %92'ye çıkabiliyor.
- **Taban bulundu ve parametre değişikliği gerektirmiyor**:
  `experiments/faz4_taban.yaml` + `docs/faz4tani/population_taban.npz`.
  5 seed'de işbirliği %10.0–22.7 (yayılım 12.7 puan), dış-grup payı %51,
  etkin soy 7.2 — önceden ilan edilmiş beş ölçütün hepsi geçildi.

### Faz 4.5 — ekoloji borcu (yemek arzı taraması + 5 seed × 2 + seçilim sondası)

Tam tablo: **[docs/faz45/ekoloji_borcu.md](docs/faz45/ekoloji_borcu.md)**

- **⚠⚠ Paylaşım enerji yaratıyordu.** `need_bonus` alıcıya vericinin
  kaybettiğinden 4 kata kadar fazla gerçek enerji veriyordu. Üretilen enerji /
  yenen yemek: %4 işbirliğinde %7, %90'da **%96**, %97'de **%321**. Tanının
  "kaçak havza"sının mekanizması bu; `need_mode: fitness` ile korunum sağlandı.
- **Çevresel sınırlama, yemek arzına dokunmadan sağlandı.** Pompa kalkıp tavan
  kaldırılınca koloni kendiliğinden N ≈ 750'de dengeleniyor (eski tavan 700'e
  yakın). Tavanda geçen adım %99.4 → %0.0; yanan üreme hakkı ~456/adım → 0.
  N, yemek arzına doğru orantılı yanıt veriyor (doz-yanıt). 5/5 seed.
- **Seçilim zinciri gerçekten kırıkmış.** Yaş kontrollü "yemek → yavru" bağı
  **+0.047 → +0.738**; hiç üremeyen yetişkin payı %67.1 → %43.8. Ham korelasyon
  (+0.317) bunu gizliyordu.
- **Eski kurulumda VERMEK kârlıydı.** Yaş *ve* servet kontrol edildiğinde bile
  paylaşan daha çok üremişti (+0.114); korunumlu kurulumda bu −0.080'e dönüyor.
  "Paylaşım ödüllendirilmez" kuralı kodda değil ama **sonuçta** ihlal oluyormuş.
- **Faz 3'ün ana bulgusu temiz zeminde TEKRARLANMADI.** In-grup fedakârlık
  5/5 → **0/5** seed'de kontrolden ayrıştı; `kin_bias_adj` asıl +1.27 ± 0.55,
  kontrol +1.94 ± 0.46 (kontrol daha yüksek). Paylaşım oranı %1.1–2.4 —
  Faz 3 adım 1'in (need_bonus = 0) sonucuyla aynı yer.
- Yan bulgu: temiz ekolojide **saldırı** yabancıya yöneliyor (`atk_t` 4/5
  seed'de −2'nin altında) — düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor.
- Yan düzeltme: `death_killed` ve `death_predator` sütunları `BASE_COLUMNS`'ta
  vardı ama satıra hiç yazılmıyordu; CSV'de boş hücre, `summary.txt`'de 0
  görünüyordu.

### Faz 4.6 — korunumlu zeminde `r·b > c` araması (15 sonda + 16 kontrollü koşum)

Tam tablo: **[docs/faz46/hamilton_arayisi.md](docs/faz46/hamilton_arayisi.md)**

- **Eşik aşılamadı: `r·b/c` en yüksek 0.989, 0/15 koşul 1'i geçti.** Enerji
  korunumu 15/15 koşumda tam.
- **`b` ve `c` ölçüldü, varsayılmadı.** Yavru cinsinden regresyon (yaş + yemek
  kontrollü): `b̂` ve `ĉ` her koşulda sıfırdan açıkça farklı (|t| = 10–70).
  **`need_bonus` varsayımı gerçek faydayı 2–3 kat fazla tahmin ediyormuş**
  (tahmin 2.0–2.9, ölçülen 0.64–1.48).
- **`r` ile `b/c` ters hareket ediyor** (korelasyon −0.51). Akrabaları
  sıkıştırmak `r`'yi 0.43 → 0.89 çıkarıyor ama `b/c`'yi 1.48 → 0.98'e
  düşürüyor: komşular zaten benzer ve benzer doygunlukta.
- **En iyi ölçülebilir noktada sinyal ölçütü geçmiyor**: `r·b/c` = 0.901'de
  ayrışma 3/5 seed (ölçüt ≥2/3), etki 0.16 puan (Faz 3'ün pompalı zemininde
  +28 puandı). `r·b/c` = 0.989'a çıkan koşul dış-grup payını %3–9'a düşürüp
  ölçülemez hale geldi.
- **⚠ `min_donor_energy` kaldıracı beklentinin TERSİNE çalıştı**: 10 → 100
  yapınca `ĉ` düşmedi, `b̂` düştü (0.0126 → 0.0083), `b/c` 0.98 → 0.64.
- Yan bulgu: saldırı 5/5 seed'de yabancıya yöneliyor (`atk_t` −6.7…−14.7).
  Korunumlu zeminde düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor.

### Faz 5 — karşılıklılık (4 önkoşul koşulu + 5 seed × 2 kol + sonda)

Tam tablo: **[docs/faz5/karsiliklilik.md](docs/faz5/karsiliklilik.md)**

- **Üç önkoşul da ölçülerek sağlandı.** Tekrarlı karşılaşma: ajanların %50.6'sı
  aynı bireyle ≥3 **ayrı** buluşma (ölçüt %30), dönüş aralığı medyan 16 adım.
  Tanıma: iki yeni sensör. Hafıza: RNN iç durumu zaten kalıcı + dışsal defter.
- **Karşılıklılık EVRİMLEŞMEDİ: 0/5 seed** kontrolden ayrıştı (`t` = −0.94 ± 1.56).
  İki seed'de kontrol asıl koldan daha yüksek.
- **Misilleme 1/5** (ölçüt ≥4/5). Görünen +4.3…+8.0 puanlık "bana saldırana
  saldırırım" tamamen konfound: kontrol de +4.3…+6.9 veriyor.
- **Defter kanalı tutarlı okunmuyor**: sonda hafızalı +0.038 (3/5 pozitif),
  kontrol +0.030 (4/5). Tek seed'e bakılsaydı ters okunurdu.
- **⚠ Kontrol tasarımı dersi:** ilk kontrol (`shuffle_identity`) örneklemi yok
  ediyordu (defteri pozitif fırsat 17 751 → 417). Asıl kontrol
  `shuffle_ledger` örneklemi korur, yalnızca bilgiyi siler.
- **⚠ Epizot ≠ adım**: adım-tekrarı %95.0 ama epizot-tekrarı %29.1. Uzun
  bitişiklik tekrarlı karşılaşma değildir; sıkışık mekân zemini düşürüyor.
- Enerji korunumu 10/10 koşumda tam.

### Faz 6 — partner seçimi (menzil taraması + 5 seed × 3 kol + dışlama sondası)

Tam tablo: **[docs/faz6/partner_secimi.md](docs/faz6/partner_secimi.md)**

- **⚠⚠ İlk parti hiç ölçüm yapmamıştı.** Seçim kolu, seçimsiz kolla birebir
  aynı `state_hash`'i verdi: (a) `load_population` yeni `pick_*` parametrelerini
  yüklemiyordu, dolayısıyla mutasyona da uğramıyorlardı; (b) aday havuzu
  ortalama 1.35 kişiydi. **Seçenek yoksa seçim de yoktur.** Önkoşul ilan edildi
  (havuz ≥ 2.0 ve kararların ≥ %50'si çok adaylı) ve `pool_multi` sütunu eklendi.
- **Menzil ölçütü geçen en küçük değerde sabitlendi** (`radius = 5.0`, havuz
  2.85, çok adaylı %81.3) ve **üç kola da aynı** uygulandı. Yan etkiler ölçüldü:
  N 644 → 668, kişi başı toplama sabit, `genetic_r` sabit, korunum 0.
- **İŞBİRLİĞİ TABAN BANDINDAN ÇIKMADI.** Kontrolden yukarı ayrışma 3/5 seed
  (t +3.6…+13.6) ama en yüksek seviye %0.93 — ölçüt %2.4'ün üstünü istiyordu.
  **0/5.** Aracın ilk sürümü yalnızca t'ye bakıp "KURDU" yazıyordu; ölçütün
  ikinci yarısı koda eklendi (`BASELINE_HIGH`) ve test dosyayla karşılaştırıyor.
- **Ayrışan yerde bile kaynağı politika değil: 4/5 seed'de rastgele seçim
  aynısını (ya da fazlasını) yapıyor.** Yükselişi yapan şey havuzun varlığı.
  Rastgele-seçim kontrolü tam bunun için ilan edilmişti.
- **Havuz işbirliğini değil düşmanlığı büyütüyor**: seçimsiz → rastgele geçişte
  paylaşım medyan ×1.23, saldırı medyan **×2.31** (4/5 seed). Faz 4.5/4.6
  asimetrisi üçüncü kez tekrarlandı.
- **Dışlama politikası GERÇEKTEN evrimleşti (5/5).** Aynı genomlar, yalnızca
  seçim kuralı değişerek: bireysel dışlama %12.3–36.6 vs rastgele %6.4–7.4.
  Ama "iyi vericiyi seç" biçiminde değil — defter oranı medyan 1.06, rastgelede
  1.24 (4/5 seed'de rastgele daha seçici). ⚠ Yalnızca seed 42'ye bakılsaydı
  (2.21 vs 1.24) "karşılıklı seçim evrimleşti" denecekti.
- **⚠ Ölçülebilirlik ölçütü GEÇMEDİ**: dış-grup fırsat payı %0.1–2.0, etkin soy
  ~1.0 (Faz 5 tohumu tek soya inmiş). Akrabalık kanadı okunmaz; `pick_kin_sel`
  iki sıfırın farkı olduğu için Welch t'si +14.73'e kadar çıkıyor ve rapor o
  hücreyi bayraklıyor.
- Enerji korunumu 15/15 koşumda ve sondada tam.

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

## 7. Faz 4 adım 2'ye geçerken yapılacaklar

1. ✅ **Doğal avcı** eklendi (`sinek/predator.py`, `rules.predator`). Sonuç:
   düşmanlık da sürü işbirliği de çıkmadı — avcı tek başına literatürdeki
   tetikleyicinin yalnızca yarısıymış. Eksik olan **gruplar arası rekabet**:
   ortak tehdit kaynak paylaşmıyor, bir soyun kazancı diğerinin kaybı değil.
   Bunu eklemeden parochial düşmanlık beklenmemeli.
2. ✅ **Rejim çatalı** teşhis edildi (§3.7). Ölçülebilir taban hazır:
   `experiments/faz4_taban.yaml` + `docs/faz4tani/population_taban.npz`.
   Adım 2'nin bütün kolları bu tohumla kurulmalı; müdahale eklenince Bölüm B
   ölçütü **yeniden** denetlenmeli.
3. ✅ **Ekoloji borcu** kapatıldı (§3.8). Popülasyonu artık çevre sınırlıyor,
   seçilim zinciri sağlam, paylaşım korunumlu. Yeni taban:
   `experiments/faz45_ekoloji.yaml`.
4. ✅ **Soru cevaplandı (§3.9): bu mekanik repertuvarda `r·b > c` ulaşılamıyor.**
   `b/c` kolu yapısal (korunumlu aktarımda ≤ 1), `r` kolu ekolojik (0.89 üstü
   koloniyi çökertiyor) ve ikisi ters hareket ediyor. Fedakârlık istenirse
   **yeni bir kanal** gerekir: misilleme/hafıza, itibar, tekrarlı etkileşim,
   kısmi akrabalık (melez soyisim) veya grup seçilimi. Bunlardan biri
   eklenmeden fedakârlık beklenmemeli.
5. ✅ **Karşılıklılık da elendi (§3.10).** Üç önkoşul ölçülerek sağlandı,
   yine de 0/5. İki negatif bağımsız olmayabilir: karşılıklılık, üzerine
   kurulacağı işbirliği (~%1 paylaşım) olmadığı için başlayamıyor olabilir.
   Sınamak için paylaşımı **ödüllendirmeden** dışarıdan yükseltip
   karşılıklılığın o zaman çıkıp çıkmadığına bakmak gerekir.
6. ✅ **Partner seçimi de elendi (§3.11).** Önkoşul ölçülerek sağlandı
   (havuz 2.57–2.91), yetenek gerçekten kullanıldı (dışlama 5/5 seed'de
   rastgeleden ayrıştı) — ama işbirliği taban bandından çıkmadı (0/5) ve
   ayrıştığı yerde bile rastgele seçim aynısını yapıyor (4/5). **Üç mekanizma
   da elendi.** Bundan sonra denenecek üç aday, önem sırasıyla:
   (a) **soy çeşitliliğini geri getirmek** — Faz 5/6 tohumunda etkin soy ~1 ve
   dış-grup payı %2; akrabalıkla ilgili her ölçü bu zeminde okunmuyor,
   (b) **gruplar arası rekabet** (bir soyun kazancı diğerinin kaybı — Faz 4
   adım 1'in eksik yarısı), (c) paylaşımı **ödüllendirmeden** dışarıdan
   yükseltip karşılıklılık/seçimin o zaman ayrım yapıp yapmadığına bakmak.
   ⚠ (a) her durumda ilk sırada: ölçülebilirlik ölçütü (dış-grup payı ≥ %10)
   Faz 6'da GEÇMEDİ, yani yeni bir sosyal mekanik eklemek yine okunamaz bir
   ölçüm üretir.
7. **Melez soyisim**: `Genome.surname` tek tam sayı. Faz 4'te X-Y birleşik
   etiket olacak; `lineage_stats`, `kin_assortment` ve kontrol grupları
   etiketi yalnızca **eşitlik** üzerinden kullanır, dolayısıyla etiket tipini
   değiştirmek bu kodu bozmaz — kısmi akrabalık isteniyorsa
   `agent.sense`'teki `kin` hesabı sürekli bir orana çevrilir.
8. **Soy-arası ilişki matrisi**: `opp_kin`/`opp_nonkin` ikili sayımı
   `(soy_i, soy_j)` matrisine genişletilecek. `stratified_kin_bias`
   `action` parametresiyle zaten genel; hücre başına da uygulanabilir.
9. Adım 2 tohumu: `docs/faz6/population_secim.npz` (seçimli),
   `docs/faz5/population_hafiza.npz` (hafızalı) ya da
   `docs/faz45/population_ekoloji.npz` (hafızasız temiz ekoloji).
   Eski zeminin tabanı `docs/faz4tani/population_taban.npz`, Faz 4 adım 1'in
   avcılı kazananları `docs/faz4/population.npz`.

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
- **Tek rejim de sonuç değildir.** Adım 2 "saldırı akrabalığa kör" dedi ve
  5 seed'de tekrarlandı — ama rejim biraz oynatılınca 10/12 koşumda tersine
  döndü. Bir negatifi genellemeden önce `tools/env_sweep.py` ile çevreyi
  süpürün.
- **Kaldıracınızın ne yaptığını ÖLÇÜN.** Eksen A'da `split_rate`'i düşürmek
  dış-grup payını yükseltti (beklentinin tersi) ve kaldıraçlar yemek
  dengesini de oynattı. Tarama koşullarında niyetlenen değişkenin yanında
  yan etkileri de kaydedin (`kin_assortment`, `food_fill`, `opp_*`).
- **ORANLARI koşullar arası kıyaslamayın.** `food_fill = mevcut/kapasite`
  bir orandır; kapasiteyi değiştiren bir koşul (yama sayısı) onu
  karşılaştırılamaz kılar — eksen B'de en kıt koşul en yüksek doluluğu
  gösterdi. Kıtlık için **kişi başı** büyüklük kullanın
  (`yenilenme × kapasite / N`).
- **Ara sonucu örüntü diye sunmayın.** Eksen A'nın ilk 8 noktası temiz bir
  assortment eşiği gösteriyordu; kalan 4 nokta ve eksen B onu tamamen
  çürüttü. Örüntü iddiası ancak tüm koşullar bitince yazılır.
- **Bir aracın rejimi bir deney dosyasını taklit ediyorsa test edin.**
  `test_seed_sweep_regime_matches_step2` ikisi ayrışırsa kırmızıya döner.
- **Kalibrasyonu deneyin TAM UFKUNDA yapın.** Avcı gücü 1500 adımda sağlıklı
  görünüp 12000 adımda karıştırma kontrolünü tüketti. Kısa kalibrasyon eksik
  değil, yanıltıcıdır.
- **Ölçütü sonucu görmeden ilan edin.** Avcı sayısı, üç önceden yazılmış
  ölçütle seçildi (kontrol yaşar / dış-grup payı ≥ %10 / avcıya bağlı ölüm
  ≥ %10). Aksi halde parametre, istenen sonucu verene kadar ayarlanmış olur.
- **Kontrolü ölmüş bir koldan sonuç okumayın.** `predator_sweep` bunu ve
  dış-grup payının %10'un altına düşmesini yüksek sesle bayraklar; iki durumda
  da o kol OKUNMAZ.
- **Doygun rejimden ayrımcılık okumayın.** In ve dış birlikte %97'ye
  çıktığında dört hücreli matris tavan etkisiyle ayrımı gizler; `share_t`
  (dönem bazlı, kontrole karşı) ve nedensel sonda ayrıca bakılmalıdır.
- **Faz sınırı değiştiğinde eski deney dosyalarını sabitleyin.** `config.yaml`
  Faz 4'e ilerleyince Faz 1/2/3 deney dosyalarına ve `seed_sweep.REGIME`'e
  `rules.predator.enabled=false` eklendi; yoksa eski fazlar sessizce başka bir
  deneye dönüşürdü. Test bunu tutar (`TestPredatorArms`).
- **ORAN yerine KİŞİ BAŞI MUTLAK hız kullanın.** `food_fill` bir stoktur ve
  kapasiteye bağlıdır; "koloni topluyor mu yoksa enerjiyi yalnızca dolaştırıyor
  mu" sorusu ancak `forage_per_capita` / `share_per_capita` ile sorulabilir.
  20 avcılı kontrolün toplamayı gerçekten bıraktığı (0.0001) da böyle
  doğrulandı.
- **Sınıflandırma eşiğini veriden türetin.** `basin_map` eşiği sıralı
  değerlerdeki en büyük boşluktan alır ve boşluk ikincisine yakınsa "bimodal
  değil" der. Uydurma bir eşik, olmayan bir çatalı var gösterir.
- **Popülasyon tavanda mı diye bakın.** `agents.max_count` bağlayıcıysa üreme
  bir slot kuyruğudur ve enerji fitness'a zayıf dönüşür; enerji biriminde
  ölçülen `b/c` o durumda seçilim ölçütü **değildir**.
- **Varyans patlaması eşiğin imzasıdır.** Bir kaldıraçta seed'ler arası yayılım
  tepe yapıyorsa oradasınız kritik noktadasınız; o ayarı taban seçmeyin.
- **ENERJİ DEFTERİNİ TUT.** Enerji aktaran her yeni kural için korunumu
  doğrulayan bir test yazın. `need_bonus` "alıcının dönüşüm verimi" diye
  belgelenmişken alıcıya 4 kata kadar fazla GERÇEK enerji veriyordu; sonuç
  sınırsız bir iç enerji kaynağı, çevreden kopmuş bir popülasyon ve kârlı
  hale gelen bir "fedakârlık" oldu. `energy_created` sayacı bunun için var.
- **Bir fitness iddiasını enerji olarak uygulamayın.** "Aynı kalori aç bir
  alıcıya daha değerlidir" bir fitness iddiasıdır; muhasebeye girer, enerji
  defterine değil (`need_mode: fitness`).
- **Popülasyon tavana yapışıyorsa seçilim kırıktır.** `at_cap` ve
  `repro_blocked` ölçün. Tavan bağlıyorken "çok toplayan çok ürer" bağı
  +0.05'e kadar düşüyordu; tavan kalkınca +0.74. Enerji biriminde ölçülen
  `b/c` o durumda seçilim ölçütü **değildir**.
- **Fitness korelasyonlarında YAŞ ve SERVET birlikte kontrol edilir.** Yaşlı
  ajan hem çok yer hem çok ürer; çok toplayan hem çok paylaşır hem çok ürer.
  Yalnız yaş kontrolüyle "vermek kârlı" görünüyordu; servet eklenince işaret
  döndü.
- **Bir bulgu, üretildiği dünyanın özelliği olabilir.** Faz 3'ün ana sonucu
  kendi kontrolüne karşı 5/5 ayrışıyordu ve ölçüm doğruydu — ama o dünyada
  paylaşım enerji üretiyordu. Zemin değişince 0/5. Zemini değiştiren her
  düzeltmeden sonra ana bulguları **yeniden doğrulayın**.
- **`r`'yi ETİKETTEN değil GENOMDAN okuyun.** `kin_assortment` soyisim
  eşitliğidir; `genetic_r` genom benzerliğidir. Hamilton eşitsizliği ikincisiyle
  çalışır — aynı soyisim mutasyonla ayrışır, yeni bölünen soy ise ayrılma
  anında genetik olarak aynıdır.
- **Bir katsayıyı muhasebeye koyup onunla kanıt üretmeyin.** `need_bonus`
  çarpanlı `b/c` bir varsayımdır (`bc_ratio_fit`), ondan "Hamilton sağlandı"
  çıkmaz. `b` ve `c` simülasyonun kendi para biriminde — **yavru** cinsinden —
  ölçülür (`tools/hamilton_probe.py`). Ölçüm, varsayımı 2–3 kat fazla
  bulmuştu.
- **Eşiğe yaklaşırken ölçülebilirliği kaybetmeyin.** `r·b/c` 0.989'a çıkan
  koşul dış-grup fırsat payını %3'e düşürdü; o kol okunmaz. Her taramada
  ölçülebilirlik şartını da denetleyin.
- **Kontrol ÖRNEKLEMİ değil BİLGİYİ silmelidir.** `shuffle_identity` defteri
  pozitif fırsatı 17 751'den 417'ye düşürüyordu; o kontrole karşı okunan hiçbir
  oran yorumlanamaz. `shuffle_ledger` aynı sayıda partneri ve aynı değerleri
  bırakıp yalnızca eşleşmeyi bozar. Yeni bir kontrol yazarken **örneklem
  büyüklüğünü iki kolda da ölçüp karşılaştırın**.
- **Tekrarlı karşılaşmada EPİZOT sayın, adım değil.** Aynı komşunun yanında
  100 adım durmak tek karşılaşmadır. Adım-tekrarı %95 iken epizot-tekrarı
  %29'du; mekânı sıkıştırmak zemini yükseltmiyor, **düşürüyor**.
- **YENİ BİR YETENEK EKLERKEN SEÇENEĞİN VAR OLDUĞUNU ÖLÇÜN.** Faz 6'da partner
  seçimi açıldı ama aday havuzu ortalama 1.35 kişiydi: seçim kolu, seçimsiz
  kolla **birebir aynı** `state_hash`'i verdi ve üç koşum boşa gitti. Yeteneğin
  *kullanılabilirliği* bir önkoşuldur ve ölçülür (`pool_multi`). Ortalama tek
  başına yetmez — 1 ve 4 adaylı kararların karışımı da 2.5 ortalama verir.
- **SÖZLEŞME BÜYÜDÜĞÜNDE PARAMETRELER DE TAŞINMALI.** `migrate_weights` Faz
  2'den beri sensör sütunu ekliyordu, ama `genome.params`'a eklenen yeni bir
  isim kayıtlı popülasyonda **yoktu** ve `mutate` mevcut anahtarlar üzerinde
  gezdiği için asla mutasyona uğramadı. Yeni parametre config varsayılanıyla
  eklenir ve `meta["migrated"]["new_params"]` ile **raporlanır**; sessizce genom
  değiştirmek gizlenmemesi gereken şeydir.
- **ÖLÇÜTÜN HER YARISINI KODA KOYUN.** Faz 6 ölçütü iki şey istiyordu:
  kontrolden yukarı ayrışma **ve** taban bandından çıkma. Araç yalnızca Welch
  t'ye bakıp "2/3 GEÇTİ → KURDU" yazdı; oysa seviye tabanın içindeydi.
  "Kontrolden yukarı ayrıştı" ile "kurdu" aynı şey değildir; test aracı ölçüt
  dosyasıyla karşılaştırır.
- **YETENEK Mİ POLİTİKA MI: rastgele-kullanım kontrolü şart.** Faz 6'da
  işbirliği %0.44 → %0.89 çıktı, ama **rastgele** seçim de aynısını yaptı
  (4/5 seed). Yeni bir karar yeteneği eklerken "yeteneği rastgele kullanan" bir
  kol olmadan artışı politikaya yazamazsınız.
- **SEÇİCİLİK REFERANSI, POLİTİKA YOKKEN SEÇİLECEK OLANDIR.** Havuz ortalamasına
  karşı okunan seçicilik politika hiç yokken bile +0.05 çıkıyor; en yakın komşu
  uzamsal olarak zaten daha akraba ve tekrarlı bitişiklik yüzünden daha sık
  defteri pozitif. Aynı sonda referansa göre **zıt işaret** verebiliyor —
  hangisinin kanıt olduğu önceden yazılır.
- Test: `python -m unittest discover -s tests` yeşil kalmalı.
