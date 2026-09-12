# Faz 4 tanı — rejim çatalı

Avcı kapalı (çatal avcısız da var, avcı bu tanıda gürültü). Faz 3 adım 2 /
Faz 4 rejimi. **Yeni davranış mekaniği yok**; A ve C'de hiçbir parametre
değişmiyor, B'de yalnızca üç kaldıraç süpürülüyor.

Toplam 51 koşum × 12000 adım.

---

## Bölüm A — havza haritalama: 12 seed, yalnızca seed değişiyor

Sınıflandırma eşiği uydurulmadı, **veriden türetildi**: sıralı değerlerdeki en
büyük boşluk. Boşluk ikincisine yakınsa "bimodal değil" denir
(`tools/basin_map.py`, `tests/test_tools.py::TestBasinMap`).

| eksen | aralık | en büyük boşluk / ikincisi | bölünme | karar |
|---|---|---|---|---|
| kişi başı toplama | 0.0285–0.0440 (**1.5×**) | 1.54× | 3 / 9 | **bimodal değil** |
| işbirliği oranı | %4.4–%91.9 (20.7×) | 2.87× | 1 / 11 | tek aykırı değer |
| kümelenme | 0.452–0.996 (2.2×) | **10.24×** | 2 / 10 | ayrışık, ama 2 nokta |
| kişi başı paylaşım | 0.14–5.89 (**41.5×**) | 1.64× | 1 / 11 | bimodal değil |

### A1. "İki eşit havza" ifadesi fazla güçlüydü — düzeltme

Faz 4 adım 1'de üç seed'e bakıp "koloni iki kararlı rejim arasında salınıyor"
demiştim. 12 seed'de görünen şu: **yoğun paylaşım durumu baskın çekim havzası**
(12'nin 11'i %42–92 arasında), seyrek toplayıcı durum ise **nadir** (1, en
fazla 2 koşum). Adım 1'in üç seed'inden biri (42) tam da o nadir koşumdu ve
tablonun yarısını o temsil ediyor gibi görünmüştü.

Bu, adım 1'in avcı sonuçlarını geçersiz kılmaz — her kol kendi kontrolüne
karşı okunmuştu — ama "bistabilite" nitelemesini daraltır.

### A2. Paylaşım toplamayı EZMİYOR — S1 hipotezinin güçlü hâli reddedildi

Toplama ile paylaşım arasındaki korelasyon r = **−0.827**, yani yön doğru.
Ama büyüklük yok: paylaşım **41 kat** değişirken toplama yalnızca **1.5 kat**
değişiyor (varyasyon katsayısı %13). Koloni paylaşmak için toplamayı
bırakmıyor; enerjiyi topladığının **üstüne** dolaştırıyor.

Tek istisna 20 avcılı partide tükenen kontrol: orada kişi başı toplama
**0.0001** (400× çöküş). Yani "toplamayı bırakma" gerçek bir durum, ama
avcısız rejimde ortaya çıkmıyor — o, avlanma baskısının uç hâli.

### A3. Çatal GEÇ oluyor ve erken dinamikten okunamıyor

12 koşumun hepsi ~%35 işbirliğiyle başlıyor, 4.–8. dönemde %7–40'a düşüyor
(Faz 3 adım 1'deki eleme), sonra 11'i geri tırmanıyor. Erken dönem ile son
çeyrek arasındaki korelasyon 7. döneme (4000. adım) kadar **r ≤ +0.42**.
Ayrışma 4000.–8000. adımlar arasında.

### A4. İşbirliğiyle birlikte hareket eden şey akrabalık assortment'i

Koşum içinde dönem-dönem `cooperation_rate` × `kin_assortment` korelasyonu
ortalama **+0.847** (12/12 pozitif, en zayıfı +0.457). Koşumlar arası +0.765.

Yön testi zayıf: assortment önde giderken r +0.833, işbirliği önde giderken
+0.788 (fark +0.045). **Nedensellik iddia edilemez**; ikisi eşzamanlı hareket
ediyor. Pozitif geri besleme (paylaşım → kümelenme → assortment → paylaşım)
bu tabloyla tutarlı ama bu veriden kanıtlanamaz.

### A5. Hamilton ölçütü hiçbir koşumda sağlanmıyor — işbirliği yine de doyuyor

`r·b/c` 12 koşumda **0.37–0.91**, hepsi 1'in altında; %92 işbirliğine ulaşan
koşumda bile 0.85. Yani projenin kendi enerji muhasebesine göre paylaşım
elenmeli — elenmiyor.

Açıklama A6'da: enerji muhasebesi burada fitness muhasebesi değil.

### A6. ⚠ Popülasyonu sınırlayan şey çevre değil, `agents.max_count`

| gözlem | sayı |
|---|---|
| adımların tavanda (N=700) geçen payı | **%99.4** |
| tavana ilk varış | ~72. adım |
| tavan 3000'e çıkarılınca | koloni 3000'i de dolduruyor (1500. adıma kadar) |
| yenilenme 16.7× kısılınca (0.010 → 0.0006) | popülasyon yine 700, açlık ölümü payı %33 |
| son çeyrek doğum | ~1 / adım (700 aday için) |

`max_count: 700` config'e "bellek/hız emniyeti" diye konmuştu. Fiilen **Faz 3
ve Faz 4'ün her deneyinde taşıma kapasitesi o olmuş**. Sonuçları:

- Üreme bir **slot kuyruğu**: enerji ancak boşalan slotu kapma ihtimalini
  artırdığı ölçüde fitness'a dönüşüyor.
- Bu yüzden enerji biriminde ölçülen `b/c` seçilim ölçütü değil — A5'in
  çelişkisi buradan geliyor.
- Eksen B'nin "kıtlık" koşulları popülasyonu hiç değiştirmemişti; bireyleri
  fakirleştirdi, koloniyi küçültmedi. O yorum bu ışıkta okunmalı.

### A7. Paylaşım "bedava fazlalık" da değil

Fazla-enerji sondası (`tools/surplus_probe.py`): kaçak koşumda (777) verici
**her** enerji katmanında %83–90 olasılıkla paylaşıyor — 32–64 aralığında
bile, ki üreme eşiği 130. Düşük koşumda (42) olasılık enerji arttıkça
*düşüyor* (%10 → %1.6). Yani yüksek durumda paylaşım gerçekten maliyetli;
sadece o maliyet zayıf seçiliyor.

---

## Bölüm B — çatalı tetikleyen parametre

Kabul ölçütü koşumlardan **önce** yazıldı: [olcut_BOLUM_B.md](olcut_BOLUM_B.md).
Her koşul 5 seed (1, 7, 42, 123, 777).

| koşul | işbirliği medyan | min–max | yayılım (puan) | toplama | dış pay | `r` | etkin soy | ölçüt |
|---|---|---|---|---|---|---|---|---|
| `need_bonus=0` | %1.3 | 1.0–2.3 | **1.3** | 0.0411 | %46.1 | 0.367 | 6.8 | kaldı (ölü) |
| `need_bonus=1` | %2.1 | 1.8–2.6 | **0.8** | 0.0403 | %60.5 | 0.341 | 12.2 | kaldı (ölü) |
| `need_bonus=2` | %15.1 | 2.6–92.2 | **89.6** | 0.0401 | %31.1 | 0.366 | 5.8 | kaldı (yayılım) |
| **taban** (`need_bonus=3`) | %59.4 | 4.4–90.0 | 85.5 | 0.0392 | %23.4 | 0.685 | 3.9 | kaldı |
| `overhead=3.0` | %53.1 | 6.7–94.9 | 88.3 | 0.0399 | %31.5 | 0.462 | 5.8 | kaldı |
| `overhead=6.0` | %1.8 | 1.4–69.9 | 68.5 | 0.0400 | %53.2 | 0.397 | 8.4 | kaldı |
| karışma 0.45 | %47.8 | 27.9–81.7 | 53.7 | 0.0383 | **%9.1** | 0.618 | 2.0 | kaldı (dış pay) |
| karışma 0.85 | %50.2 | 1.2–78.4 | 77.2 | 0.0715 | %13.7 | 0.511 | 2.6 | kaldı |

### B1. Ara rejim YOK — sistem ya ölü ya kaçak

`need_bonus` ekseninde geçiş 1.0 ile 2.0 arasında. Eşiğin altında sonuç
**son derece tekrarlanabilir** (yayılım 0.8–1.3 puan), üstünde seed'e teslim
(85–90 puan). **Eşikte (2.0) yayılım en yüksek değerine çıkıyor** — kritik
noktanın klasik imzası.

`overhead` daha zayıf bir kaldıraç: 1.2 → 3.0 hemen hiçbir şeyi değiştirmiyor,
6.0 ise 5 seed'in 4'ünü söndürüp birini (%69.9) bırakıyor.

Karışma (`max_speed`/`spawn_radius`) medyanı bandın içine çekiyor (%47.8) ama
yayılımı kapatmıyor ve **dış-grup fırsat payını %9.1'e düşürüyor** — Faz 4
adım 1'de öğrenilen ölçülebilirlik şartını çiğniyor. Yan etki: `karışma 0.85`
kişi başı toplamayı 1.8× artırıyor (kaldıraç yemek dengesini de oynatıyor —
beklenen, ölçüldü).

**Sonuç: "iki davranışın da yaşayabildiği" bir parametre ayarı bu üç kaldıraçta
yok.** Düşük yayılımlı tek ayarlar, paylaşımın söndüğü ayarlar.

### B2. `need_bonus=1` yine de yapısal olarak açık

`b/c` = 1.192 > 1, yani Faz 3 adım 1.5'in tavanı aşılmış durumda: paylaşım
**bastırılmış, yasaklanmış değil**. (`need_bonus=0`'da `b/c` = 0.799 < 1 —
orada yükselmesi yapısal olarak imkânsız.)

---

## Bölüm C — havzayı ne belirliyor?

### C1. Başlangıç genomları belirliyor; seed belirlemiyor

2×2 takas (12000 adım):

| koşum | işbirliği | kümelenme | `r` | etkin soy |
|---|---|---|---|---|
| seed 42 + Faz 2 tohumu | %4.4 | 0.474 | 0.286 | 9.5 |
| seed 777 + Faz 2 tohumu | %90.0 | 0.993 | 0.739 | 2.7 |
| **seed 42 + 777'nin genomları** | **%97.3** | 0.987 | 0.719 | 4.1 |
| **seed 777 + 42'nin genomları** | **%17.3** | 0.382 | 0.266 | 10.8 |

Takas sonucu **her iki yönde de** çeviriyor. Dünya düzeni ve rastgelelik akışı
(seed) havzayı belirlemiyor; **popülasyonun kendisi belirliyor**.

Not: takasta kullanılan genomlar o koşumların **bitiş** durumlarıdır. Yani bu
test "başlangıç kurucuları ne belirler"i değil, **iki durumun da kendi kendini
sürdürüp sürdürmediğini** ölçer. Cevap: ikisi de sürdürüyor — gerçek bir
çatal. Havzalar ise eşit değil (Bölüm A: ortak başlangıçtan 11/12 yüksek
duruma gidiyor).

### C2. Rastgele kurucularla ikisi de kaçıyor

Tohumsuz (kurucular rastgele) koşumlarda seed 42 → %89.2, seed 777 → %91.8.
Yani düşük durumu üreten şey Faz 2 tohumunun **belirli** bir özelliği; rastgele
başlangıç doğrudan yüksek havzaya gidiyor.

### C3. Dışarıdan kontrol edilebiliyor — ama düğme, kadran değil

`need_bonus ≤ 1.0` bütün seed'leri %2'ye sabitliyor (yayılım 0.8 puan).
Kontrol var; ara ayar yok.

---

## Karar: yeni taban parametre değil, BAŞLANGIÇ DURUMU

Bölüm C iki durumun da kararlı olduğunu gösterdiğine göre, ölçüm yapılabilen
durumda **başlamak** yeterli. Düşük havzadaki popülasyon
(`docs/faz4tani/population_dusuk_havza.npz`, seed 42'nin bitiş popülasyonu)
tohum olarak verilip **hiçbir parametre değiştirilmeden** 5 seed koşuldu:

| koşul | medyan | min–max | yayılım | toplama | dış pay | `r` | etkin soy | ölçüt |
|---|---|---|---|---|---|---|---|---|
| **`D_dusuk_havza`** | **%11.6** | 10.0–22.7 | **12.7** | 0.0400 | **%51.3** | 0.279 | 7.2 | **5/5 GEÇTİ** |

seed bazında: %11.5 / %11.6 / %10.0 / %22.7 / %17.3.

Önceden ilan edilmiş beş ölçütün hepsini geçen tek koşul bu. Üstelik:

- **Ödeme parametrelerine dokunulmadı** — üç kural (rol kodlanmaz, paylaşım
  ödüllendirilmez, in/out ayrı ölçülür) aynen duruyor; rejim Faz 3 adım 2 ile
  birebir aynı.
- İşbirliği %12 civarında, yani **yukarı doğru yeri var**: bir müdahalenin
  (avcı, gruplar arası rekabet, melez soyisim) etkisi tavanda kaybolmaz.
- Dış-grup fırsat payı %51 ve etkin soy 7.2 — in/out ayrımı ölçülebilir.

```bash
python run.py --config experiments/faz4_taban.yaml \
  --load-genomes docs/faz4tani/population_taban.npz --seed 42
```

---

## Sınırlar — ne DEMİYORUZ

- **"Çatalın nedeni şudur" demiyoruz.** A4'teki assortment birlikteliği güçlü
  ama yön testi zayıf; pozitif geri besleme hipotezi bu veriyle kanıtlanmadı.
- **"Taban her müdahale altında kararlı" demiyoruz.** 5 seed'de, müdahalesiz,
  12000 adım kararlı. Bir müdahale eklenince ölçüt **yeniden** denetlenmeli.
- **"`max_count` kaldırılırsa sorun biter" demiyoruz.** Tavan 3000'e
  çıkarıldığında koloni onu da doldurdu; çevrenin bağlayıcı olması için yemek
  arzının çok daha altına inmek gerekiyor ve o da rejimi baştan değiştirir.
  Bu, Faz 5 için açık bir yapısal iş.
- Bölüm B üç kaldıraç taradı. Başka kaldıraçlar (`amount`, `threshold`,
  `kinship.radius`, dünya boyutu) taranmadı; "ara rejim yok" iddiası **bu üç
  kaldıraç için** geçerlidir.
