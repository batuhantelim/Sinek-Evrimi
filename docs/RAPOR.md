# Evrimleşen Sinek Kolonisi — Faz 1–7 Bulgu Raporu

**Bu belge DONMUŞ bir kayıttır.** 2026-09-14 tarihinde, `65ad118` commit'inde
o ana kadar **kanıtlanmış** olanı yazar. Gelecekteki denemeleri beklemez,
"canlı doküman" değildir. Yeni bulgular yeni bir rapora yazılır.

Kapsam: 7 faz, 213 kaydedilmiş koşum, 164 test, 37 commit.

> **SONRADAN DÜŞÜLEN NOT (2026-09-14, Faz 8).** Bu belgenin gövdesi
> değiştirilmedi — dondurulmuş kayıt öyle kalır. Ancak §2.4 ve §5'te "açık
> sorun" diye yazılan **çeşitlilik koruması Faz 8'de çözüldü**: yoğunluğa bağlı
> seçilim (`rules.crowding`) seçilim süpürgesini 5 seed'in 4'ünde durdurdu,
> koloniyi çökertmeden. Ayrıntı: **[faz8/yogunluk.md](faz8/yogunluk.md)**.
> Raporun geri kalanındaki hiçbir bulgu bundan etkilenmez.
Ayrıntılı faz raporları: [docs/faz1](faz1/) … [docs/faz7](faz7/).
Yöntem kuralları ve mimari: [CLAUDE.md](../CLAUDE.md).

---

## 1. Proje sorusu ve yaklaşım

### Ne aradık

İki soru, sırayla:

1. **Bu minimal dünyada evrim gerçekten işliyor mu?** Yani rastgele sinir
   ağlarından, kimse söylemeden, işe yarar bir davranış çıkıyor mu?
2. **İşbirliği ve düşmanlık gibi sosyal davranışlar kendiliğinden çıkıyor mu?**
   Akrabalık, karşılıklılık ve partner seçimi — literatürün üç ana mekanizması —
   bu tezgâhta işbirliğini kurabiliyor mu?

### Temel metodoloji

Dört kural, her fazda uygulandı:

- **Davranış kodlanmaz.** "İşbirlikçi ol", "akrabanı kayır", "avcı gelince
  gruplaş", "iyi partneri seç" diye bir kural hiçbir yerde yoktur. Yalnızca
  koşullar kurulur (sensör kanalı, motor, maliyet/ödül) ve davranış çıkarsa
  çıkar. Kaynak testleri bunu denetler (`test_choice_policy_is_not_hardcoded`,
  `test_no_caste_is_hardcoded`, `test_memory_is_information_not_rule`).
- **Sosyal davranış ödüllendirilmez.** `evolution.fitness` içinde paylaşım ya
  da saldırı terimi yoktur; `given`/`received`/`attacks_made` yalnızca ölçüm
  içindir. Ödüllendirilseydi her bulgu değersiz olurdu.
- **Her oran kendi eşleşmiş kontrolüne karşı okunur**, sıfıra karşı değil.
  Kontroller **bilgiyi** siler, **örneklemi** değil.
- **Ölçüt koşumdan önce yazılır ve commit edilir.** (`docs/faz*/olcut*.md`;
  git geçmişi tanıktır.) Aksi hâlde parametre, istenen sonucu verene kadar
  ayarlanmış olur.

### Dünya

240×150 toroidal ızgara, 24 gaussian yemek yaması, alan tabanlı koku algısı.
Ajan: 21 sensör → küçük sızıntılı recurrent ağ (~473 ağırlık) → 5 motor
(`turn, thrust, eat, share, attack`). Genom = adlandırılmış parametreler +
serbest ağırlıklar + soyisim; gaussian mutasyon. Tüm rastgelelik tek bir
`default_rng(seed)` üzerinden; `state_hash` ile determinizm test edilir.

---

## 2. Ana bulgular

Kanıt düzeyi her bulgunun yanında: kaç seed, kaç koşul, kontrol var mı.

### 2.0 ✅ Tezgâh çalışıyor (Faz 1 taban çizgisi)

**[POZİTİF — sağlam]** · seed 42, 3000 adım, tam kör kontrol grubu var ·
[docs/faz1/](faz1/)

Klonlarla kurulan taban: `behavior_diversity = 0.0` (aynı girdi → aynı çıktı),
algı-motor döngüsü çalışıyor (kör kontrole karşı ajan başına besin alımı
**×1.15**, yamalar seyrekleştikçe **×1.32**), **kodlanmamış** boom–bust
salınımı ~300'de sönümleniyor ve `crowd_bias = 0` olmasına rağmen kaynak
yamalarına kümelenme çıkıyor. Yani ölçüm zemini, evrim eklenmeden önce
doğrulandı.

### 2.1 ✅ Evrim gerçek: kemotaksis sıfırdan evrimleşti

**[POZİTİF — sağlam]** · seed 42, 8000 adım = 32 nesil, seçilimsiz kontrol grubu
var · [docs/faz2/](faz2/)

Rastgele ağırlıklı acemi koloni vs evrimleşmiş koloni, **aynı dünyada, üreme ve
seçilim kapalı**: koku gradyanıyla hizalanma **0.013 → 0.424 (×32.6)**, hayatta
kalma ×2.0, yemek ×2.0. Ortalama fitness 356 → 815, ajan başına yenen yemek
16.3 → 61.6 (×3.8).

Faz 1'in *elle yazılmış* refleks devresi 0.66 hizalanma sağlıyordu — evrim,
kimse söylemeden, o çözümün ~2/3'ünü kendi buldu.

⚠ **Kontrol neden şart:** seçilimsiz (sürüklenen) kolonide de yemek 16.3 → 27.9
çıkıyor. Bu uyum değil, ağırlık büyüklüğünün rastgele yürüyüşle artması
(doymuş `tanh` = daha kararlı hareket). **"Bir şeyler iyileşti" tek başına evrim
kanıtı değildir.**

Aynı fazın ikinci dersi: **ödüllendirilmeyen davranış evrimleşmiyor.**
Tehlikeden kaçınma *kötüleşti* (tehlikede geçen zaman ×1.40), çünkü fitness'ta
tehlike terimi yok.

### 2.2 ❌ İşbirliğinin üç ana mekanizması da işbirliğini KURMADI

**[NEGATİF — sağlam]** Üçünün de önkoşulları **ölçülerek** kuruldu; üçü de
geçerli çeşitlilik zemininde (Faz 7 denetimi) ayakta kaldı. "Koşul yoktu"
mazereti hiçbirinde geçerli değil.

| mekanizma | önkoşul (ölçülerek sağlandı) | sonuç | kanıt düzeyi |
|---|---|---|---|
| **Akrabalık** (Hamilton `r·b>c`) | `genetic_r` genomdan okundu; `b` ve `c` **yavru cinsinden** ölçüldü (varsayılmadı) | `r·b/c` ∈ [0.475, 0.989], **1'i geçen 0/15** | 15 dürüst koşul, enerji korunumu 15/15 tam · [faz46](faz46/hamilton_arayisi.md) |
| **Karşılıklılık** (Axelrod) | tekrarlı karşılaşma (%50.6 ajan ≥3 **ayrı** buluşma), tanıma (2 sensör), hafıza (defter) | ayrışma **0/5** (eski zemin), **1/5** (geçerli zemin) | 5 seed × 2 kol, her seed kendi `shuffle_ledger` kontrolüyle · [faz5](faz5/karsiliklilik.md), [faz7](faz7/cesitlilik.md) |
| **Partner seçimi** | aday havuzu ≥2.0 ve kararların ≥%50'si çok adaylı | taban bandından çıkma **0/5** (eski), **1/5** (geçerli zemin) | 5 seed × 3 kol (seçim/seçimsiz/rastgele) · [faz6](faz6/partner_secimi.md), [faz7](faz7/cesitlilik.md) |

Üç mekanizmanın ortak sonucu: **paylaşım oranı %0.4–2.4 bandından çıkmıyor.**

**Akrabalığın neden tıkandığı yapısal olarak biliniyor:**
- `b/c` kolu **yapısal** tıkalı: `c = amount + overhead`, `b ≤ amount` ⇒
  korunumlu aktarımda enerji `b/c ≤ 1`.
- `r` kolu **ekolojik** tıkalı: 0.89'un üstüne çıkmak için hareketi kısmak
  gerekiyor, o da koloniyi çökertiyor (`max_speed` 0.02 → N = 17).
- İkisi **ters hareket ediyor**: korelasyon(`r`, `b/c`) = −0.51. Akrabaları
  sıkıştırmak `r`'yi ×2.09 artırırken `b/c`'yi 1.48 → 0.98'e düşürüyor.

**Partner seçiminde yetenek kullanıldı ama politika işbirliği üretmedi.**
Bireysel dışlama %12.3–36.6 (rastgele seçimde %6.4–7.4, **5/5 seed**): ajanlar
karşılaştıkları partnerlerin ~üçte birini hiç seçmiyor. Ama bu dışlama "iyi
vericiyi seç" biçiminde değil (defter oranı medyan 1.06, rastgelede 1.24), ve
işbirliğinin yükseldiği yerde **rastgele seçim de aynısını yapıyor** (3–4/5
seed) — yani artışın kaynağı evrimleşen politika değil, **havuzun varlığı**.

### 2.3 ✅ Asimetri: düşmanlık ayrım gözetir, fedakârlık gözetmez

**[POZİTİF örüntü — 3 ayrı fazda, farklı koşullarda tekrarlandı]**

| faz | koşul | ölçüm |
|---|---|---|
| Faz 4.5 | temiz ekoloji, 5 seed | saldırı yabancıya yöneliyor: `atk_t` **4/5** seed'de −2'nin altında |
| Faz 4.6 | korunumlu zemin, 5 seed | `atk_t` **5/5** seed'de −6.7…−14.7 |
| Faz 6 | aday havuzu eklendiğinde, 5 seed | havuz paylaşımı medyan ×1.23, saldırıyı medyan **×2.31** büyütüyor (4/5 seed) |

Aynı üç fazda in-grup fedakârlık ayrımcılığı kontrolden **ayrışmadı**.
Kısaca: **kötülük ucuz ve koşulsuz, iyilik pahalı ve koşullu.**

⚠ Sınır: bu bir *örüntü*, tek bir deneyin sonucu değil; ama üçü de aynı temel
ekolojide ölçüldü. Farklı bir ekolojide tersine dönüp dönmediği bilinmiyor.

### 2.4 ⚠ Yapısal gerilim: güçlü seçilim soy çeşitliliğini siler

**[AÇIK SORUN — ölçüldü, çözülmedi]** · [docs/faz7](faz7/cesitlilik.md)

Soy (etiket) çeşitliliği, "grup-içi vs grup-dışı" ölçümünün ön şartıdır. Ama:

- Başlangıçtaki **genom** çeşitliliği ne kadar yüksekse **soy** çeşitliliği o
  kadar hızlı çöküyor (3 nokta: taban 0.2553 → 13.95 etkin soy; ekoloji 0.3683
  → 2.56; taze/rastgele en geniş → 1.33).
- Mekanizma bir **seçilim süpürgesi**: taze kolda en büyük soy ilk 500 adımda
  %32'ye, 12000'de %99'a çıkıyor.
- Denenen düzeltme (`evolution.immigration_rate` — doğumların bir kısmı taze
  kurucu genomla doğar) **0/6 koşulda** ölçütü geçti; doğumların onda biri taze
  kurucu olsa bile etkin soy 1.71'de kalıyor. Yeni soy **açılıyor** ama
  **tutunamıyor**.

Yani "hem çok soy hem çok genetik varyans" bu tasarımda bir ayar noktası değil,
bir **gerilim**. Ölçülebilir soy çeşitliliği şu an yalnızca belirli bir tohum
popülasyonuyla (`docs/faz4tani/population_taban.npz`) sağlanıyor.

### 2.5 Evrimleşmeyen şeylerin listesi (hepsi denendi, hiçbiri çıkmadı)

| aranan | koşul | sonuç |
|---|---|---|
| akrabaya fedakârlık | temiz ekoloji, 5 seed, kontrollü | 0/5 |
| grup-dışı düşmanlık (parochial) | dış-grup bolluğu 6 koşul × 2 seed | H1 reddedildi (r = −0.133) |
| kıtlığın saldırıyı artırması | kişi başı kaynakta 16× aralık | H2 reddedildi; saldırı taban rejimin **altında** kaldı |
| avcı altında sürü işbirliği | 3 seed × 2×2 | çıkmadı |
| avcının düşmanlık üretmesi | 3 seed × 2×2 | çıkmadı; saldırı yabancıya *daha az* yöneldi |
| karşılıklılık | 5 seed × 2 kol, iki farklı zemin | 0/5 ve 1/5 |
| misilleme | aynı | 1/5 ve 2/5 (ölçüt ≥4/5) |
| partner seçimiyle işbirliği | 5 seed × 3 kol, iki farklı zemin | 0/5 ve 1/5 |

---

## 3. Yol boyunca yakalanan artefaktlar

**Bu bölüm raporun en değerli kısmıdır.** Her madde: ne sanıyorduk, gerçek
neydi, nasıl yakalandı, hangi sonucu düzeltti.

### 3.1 ⚠⚠ Enerji korunumu ihlali — "fedakârlık evrimleşti" bulgusunu yok etti

- **Ne sanıyorduk:** Faz 3 adım 2'de grup-içi fedakârlık evrimleşmişti.
  Düzeltilmiş ayrımcılık +28…+57 puan, kontrolde +0.3…+1.1 (≈50× fark),
  5/5 seed'de kontrolden ayrıştı. Ölçüm doğruydu, kontrol doğruydu.
- **Gerçek:** `rules.share.need_bonus` "alıcının dönüşüm verimi" diye
  belgelenmişti ama alıcıya vericinin kaybettiğinden **4 kata kadar fazla
  gerçek enerji** veriyordu. Paylaşım **korunumlu değildi**; her transfer
  koloniye net enerji **ekliyordu**. %90 işbirliği olan bir koşumda üretilen
  enerji yenen yemeğin %96'sı, %97'de **%321'i**.
- **Nasıl yakalandı:** popülasyonun neden hep tavanda olduğu araştırılırken
  enerji defteri tutuldu (`energy_created` sayacı eklendi).
- **Ne düzeltti:** `need_mode: fitness` (korunumlu) eklendi. Faz 3'ün ana
  bulgusu temiz zeminde **tekrarlanmadı: 5/5 → 0/5.** Ayrıca eski kurulumda
  yaş *ve* servet kontrol edildiğinde bile **vermek kârlıydı** (+0.114) —
  "paylaşım ödüllendirilmez" kuralı kodda değil ama **sonuçta** ihlal oluyormuş;
  korunumlu kurulumda bu −0.080'e döndü.
- **Kalıcı savunma:** `test_sharing_conserves_energy_by_default`; enerji aktaran
  her yeni kural için korunum testi zorunlu.

### 3.2 ⚠ `agents.max_count = 700` — gizli taşıma kapasitesi

- **Ne sanıyorduk:** popülasyonu çevre (yemek arzı) sınırlıyor.
- **Gerçek:** koşumların **%99.4'ü tavanda** geçiyordu, ~72. adımdan itibaren.
  Tavan 3000'e çıkarılınca koloni 3000'i de dolduruyordu. `max_count` config'e
  "bellek/hız emniyeti" diye konmuştu; fiilen **Faz 3 ve Faz 4'ün her
  deneyinde taşıma kapasitesi o olmuş**.
- **Nasıl yakalandı:** `at_cap` ve `repro_blocked` metrikleri eklenip
  ölçüldüğünde: adım başına ~456 üreme hakkı yanıyordu.
- **Ne düzeltti:** üreme bir **slot kuyruğu** olduğu için enerji fitness'a
  zayıf dönüşüyordu — yaş kontrollü "yemek → yavru" bağı **+0.047**'ydi;
  tavan kalkınca **+0.738** oldu. Bu, **enerji biriminde ölçülen `b/c`'nin o
  koşullarda seçilim ölçütü olmadığı** anlamına geliyor: `r·b/c` 12 koşumun
  hepsinde 1'in altındayken işbirliği %92'ye çıkabiliyordu.
- **Kalıcı savunma:** "popülasyon tavana yapışıyorsa seçilim kırıktır" kuralı;
  `at_cap`/`repro_blocked` her koşumda raporlanır.

### 3.3 Ölçüm konfoundları (dördü de gerçek bir sonucu yanlış gösteriyordu)

**`kin_bias` ham metriği — tokluk konfoundu.** Akrabalar uzamsal kümelenir →
kümeler zengin yamalardadır → oradaki sinekler toktur → **paylaşacak bütçesi
olan tok sinektir**. Ölçüldü: akrabalık sensörünü **okuyamayan** refleks
beyinle (ayrımcılık matematiksel olarak imkânsız) ham `kin_bias` **+3.80 puan**
çıkıyor. Düzeltme: verici enerjisine göre 5 katman + Mantel–Haenszel ağırlığı
(`kin_bias_adj`, aynı yapay kurulumda +3.80 → +0.36) ve ajanları hiç
çalıştırmayan nedensel sonda (`tools/kin_probe.py`).

**`food_fill` oran tuzağı.** Kıtlık ölçerken kullanıldı; ama bir orandır
(`mevcut/kapasite`) ve kapasite koşula göre değişir. En kıt koşul (yamalar
24→14) en **yüksek** doluluğu (%59.4) gösterdi. Doğru değişken **kişi başı
kaynak girdisi**. Kalıcı savunma: `forage_per_capita` / `share_per_capita`
mutlak, kişi başı metrikler olarak eklendi.

**`shuffle_identity` — örneklemi yok eden kontrol.** Faz 5'in ilk kontrolü
tanıma kimliklerini karıştırıyordu. Ölçüldüğünde defteri pozitif fırsat
**17 751 → 417** (43× küçük): bilgi mi örnek mi kayboldu ayırt edilemez.
Yerine `shuffle_ledger`: değerler ajanın **kendi** partnerleri arasında
karıştırılır — aynı sayıda partner, aynı değerler, yalnızca eşleşme bozulur.
Kalıcı savunma: **kontrol ÖRNEKLEMİ değil BİLGİYİ silmelidir**; yeni bir
kontrol yazarken iki kolda da örneklem büyüklüğü ölçülüp karşılaştırılır.

**Soyisim ≠ genetik benzerlik.** Hamilton'un `r`'si `kin_assortment` (soyisim
eşitliği) ile ölçülüyordu; ama aynı soyisim mutasyonla ayrışır ve `split_rate`
ile ayrılan soy, ayrılma anında ebeveyniyle **genetik olarak aynıdır**. Yeni
metrik `genetic_r`: aktör ile komşusunun **genom** benzerliği (regresyon
tanımı). Hamilton eşitsizliği ikincisiyle çalışır.

### 3.4 Bir katsayıyı muhasebeye koyup onunla kanıt üretmek

- **Ne sanıyorduk:** `need_bonus` çarpanlı `b/c` = 2.0–2.9, yani Hamilton
  eşiği aşılmış.
- **Gerçek:** bu kendi varsayımını ölçmektir. `b` ve `c` simülasyonun kendi
  para biriminde — **yavru** cinsinden — ölçüldüğünde (yaş + yemek kontrollü
  regresyon) **0.64–1.48** çıktı. Varsayım gerçek faydayı **2–3 kat fazla**
  tahmin ediyormuş.
- **Kalıcı savunma:** `bc_ratio` (enerji, ölçüm) ile `bc_ratio_fit` (çarpanlı
  **tahmin**) ayrıldı; asıl ölçüm `tools/hamilton_probe.py`.

### 3.5 Kaldıraçların beklentinin TERSİNE çalışması (iki kez)

- `min_donor_energy` 10 → 100 ("yalnız tok olan versin, maliyet düşsün"):
  `ĉ` düşmedi, **`b̂` düştü** (0.0126 → 0.0083) ve `b/c` 0.98 → 0.64'e indi.
  Paylaşım fırsatları zaten iyi durumdaki çiftlere daraldığı için.
- `split_rate`'i düşürmek dış-grup payını **yükseltti** (beklentinin tersi).

**Ölçülmeseydi ikisi de ters raporlanacaktı.** Kalıcı savunma:
"kaldıracınızın ne yaptığını ÖLÇÜN" — tarama koşullarında niyetlenen
değişkenin yanında yan etkiler de kaydedilir.

### 3.6 Sessizce ölü mekanik: partner seçimi hiç devreye girmemişti

- **Ne sanıyorduk:** Faz 6'nın ilk partisi "partner seçimi işbirliği kurmadı"
  diyordu.
- **Gerçek:** seçim kolu, seçimsiz kolla **birebir aynı `state_hash`**'i
  veriyordu. İki bağımsız neden: (a) `load_population` genoma sonradan eklenen
  `pick_*` parametrelerini yüklemiyordu, `mutate` de mevcut anahtarlar üzerinde
  gezdiği için **asla mutasyona uğramadılar**; (b) aday havuzu ortalama 1.35
  kişiydi — **seçenek yoksa seçim de yoktur**.
- **Nasıl yakalandı:** iki kolun `state_hash`'i karşılaştırıldı.
- **Ne düzeltti:** üç koşum boşa gitmişti; parametre taşıması eklendi (ve artık
  `meta["migrated"]["new_params"]` ile **raporlanıyor**), önkoşul ilan edildi
  (`pool_multi` sütunu), menzil ölçütü geçen en küçük değerde sabitlendi.

### 3.7 Aracın ölçütün yarısını atlaması

- **Ne sanıyorduk:** Faz 6 raporu "2/3 seed GEÇTİ → PARTNER SEÇİMİ İŞBİRLİĞİNİ
  KURDU" yazıyordu.
- **Gerçek:** ölçüt dosyası **iki şey** istiyordu — kontrolden yukarı ayrışma
  **ve** taban bandından (%0.6–2.4) çıkma. Seviye %0.89'du, yani tabanın
  içinde. Araç yalnızca Welch t'ye bakıyordu.
- **Kalıcı savunma:** ölçütün her yarısı koda kondu (`BASELINE_HIGH`) ve bir
  test aracı ölçüt dosyasıyla karşılaştırıyor. **"Kontrolden yukarı ayrıştı"
  ile "kurdu" aynı şey değildir.**

### 3.8 Kullanıcı hipotezi de ölçüldü ve çürüdü: "taze başlangıç"

- **Hipotez (Faz 7 brief'i):** her faz bir öncekinin kazananlarını tohumladı;
  bu çeşitliliği kademe kademe daralttı, taze bir 0. nesil bunu onarır.
- **Gerçek:** **tam tersi.** Tohumlu kol etkin soy 13.95/8.92 ve dış-grup payı
  %53.6/%42.9 verirken taze kol 1.33/1.02 ve %2.6/%0.5. Ayrıca kaydedilmiş
  popülasyonların genom çeşitliliği zincir boyunca **azalmıyor**
  (0.2553 → 0.3683 → 0.2806 → 0.2896). 2×2 tasarım (tohum × hafıza) nedeni
  ayrıştırdı: belirleyen **tohum popülasyonu**, mekanik değil.
- **Ne düzeltti:** Faz 5 ve Faz 6'nın gerçekten ölçülemez bir zeminde
  (etkin soy ~1, dış-grup payı %0.1–4.6) ölçüldüğü ortaya çıktı ve **ikisi de
  geçerli zeminde tekrarlandı** — sonuçlar değişmedi. Akrabalık testinin ise
  **zaten** geçerli zeminde (4/5 koşum, dış-grup %40–58) yapıldığı görüldü.

---

## 4. Metodolojik dersler

Bunların her biri bir hatadan doğdu; gerekçeleriyle birlikte
[CLAUDE.md §8](../CLAUDE.md) içinde kural olarak duruyor.

1. **"Kontrolden ayrıştı" ≠ "kuruldu."** İstatistiksel ayrışma, etkinin
   anlamlı büyüklükte olduğunu göstermez. Ölçütün her yarısı koda konur.
2. **Makul anlatı ≠ doğru anlatı.** "Paylaşım toplamayı eziyor", "düşük
   assortment düşmanlık üretir", "taze başlangıç çeşitlilik verir",
   "`min_donor_energy` maliyeti düşürür" — dördü de makuldü, dördü de yanlıştı.
   Kullanıcının hipotezi de aynı sınavdan geçer.
3. **Tek seed sonuç değildir.** Faz 3'te yön 5/5 tuttu ama büyüklükler 3–5×
   aralıkta oynadı. Faz 5'te yalnızca seed 42'ye bakılsaydı "kanal okunuyor"
   denecekti; Faz 6'da yalnızca seed 42'ye bakılsaydı "karşılıklı seçim
   evrimleşti" denecekti.
4. **Tek rejim de sonuç değildir.** "Saldırı akrabalığa kör" bulgusu 5 seed'de
   tekrarlandı — ama rejim biraz oynatılınca 10/12 koşumda tersine döndü.
   Ölçüm yanlış değildi, **genelleme fazla genişti.**
5. **Bir düzeltme başka yerde ölçümü bozabilir.** Faz 4.5'te seçilim zincirini
   onardık (+0.047 → +0.738); bu, Faz 5/6 zemininde soy çeşitliliğinin
   çökmesinin muhtemel nedeni. Zemini değiştiren her düzeltmeden sonra yalnızca
   ana bulgular değil **ölçülebilirlik** de yeniden denetlenir.
6. **Bir bulgu, üretildiği dünyanın özelliği olabilir.** Faz 3'ün ana sonucu
   kendi kontrolüne karşı 5/5 ayrışıyordu ve ölçüm doğruydu — ama o dünyada
   paylaşım enerji üretiyordu.
7. **Önkoşulu önce garanti et.** Karşılıklılık için tekrarlı karşılaşma +
   tanıma + hafıza; partner seçimi için gerçek bir aday havuzu. Üçü olmadan
   "reddedildi" denemez; doğru cümle "koşul yoktu"dur.
8. **Kalibrasyonu deneyin TAM UFKUNDA yap.** Avcı gücü 1500 adımda sağlıklı
   görünüp 12000 adımda karıştırma kontrolünü tüketti (700 → 0). Kısa
   kalibrasyon eksik değil, **yanıltıcıdır**.
9. **Ölçüt koşumdan önce ilan edilir ve commit edilir.** Aksi hâlde parametre,
   istenen sonucu verene kadar ayarlanmış olur.
10. **Enerji defterini tut.** Enerji aktaran her yeni kural için korunumu
    doğrulayan bir test yazılır (`energy_created` sayacı bunun için var).

---

## 5. Açık sorular ve denenmemişler

**Bu bölüm spekülasyondur; yukarıdaki hiçbir bulgu buna dayanmaz.**

### Çözülmemiş yapısal sorun

- **Çeşitlilik koruması yok.** Göçmen mekaniği 0/6 koşulda ölçütü geçemedi.
  Denenmemiş kaldıraçlar: daha geniş dünya / daha çok yama (CLAUDE.md'de
  160×100 → 240×150 geçişinin ~13 etkin soy verdiği yazılı), uzamsal
  sığınaklar, yoğunluğa bağlı seçilim.
- **Seçim mekaniğinin kendisi çeşitliliği düşürüyor** (etkin soy 2.4–5.2 vs
  seçimsiz kolda 9.0–13.4). Dışlama süpürgeyi hızlandırıyor; ayrıca
  incelenmedi.

### Denenmemiş işbirliği mekanizmaları

- **Grup seçilimi / gruplar arası rekabet.** Faz 4'ün avcısı ortak bir
  tehditti ama **kaynak paylaşmıyordu**: bir soyun kazancı diğerinin kaybı
  değildi. Literatürde parochial düşmanlık genelde o baskı altında çıkar.
- **İtibar** (üçüncü taraf gözlemi): hiç denenmedi.
- **Melez soyisim / kısmi akrabalık**: `Genome.surname` hâlâ tek tam sayı ve
  yalnızca **eşitlik** üzerinden kullanılıyor; sürekli bir akrabalık oranı
  denenmedi.
- **Paylaşımı ödüllendirmeden dışarıdan yükseltmek.** Hipotez (ölçülmedi):
  karşılıklılık ve partner seçimi, **üzerine kurulacağı işbirliği olmadığı
  için** başlayamıyor olabilir — seçilecek "iyi verici" sınıfı fiilen yok
  (defteri pozitif aday payı %2.7–17.8).

### Planda ama sırada değil

- **Connectome doğrulaması**: gerçek meyve sineği bağlantı haritasıyla (FlyWire)
  kıyas. Beyin arayüzü (`sinek/brains/base.py` kayıt defteri) bunun için hazır
  — yeni bir `Brain` sınıfı + `config.yaml → brain.type` yeterli; simülasyonun
  geri kalanına dokunmak gerekmiyor.

---

## 6. Tek cümlelik özet

Bu tezgâhta **evrim gerçekten işliyor** (kemotaksis sıfırdan, ×32.6 hizalanma),
ama **işbirliğinin üç ana mekanizması da işbirliği kurmuyor** — ve bu negatifin
değeri, ona giden yolda yakalanan artefaktların (§3) **her birinin**
düzeltilmiş olmasında: yalnız birincisi (enerji korunumu) düzeltilmeseydi bu
rapor "fedakârlık evrimleşti" diyor olacaktı.
