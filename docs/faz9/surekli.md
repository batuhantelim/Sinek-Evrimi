# Faz 9 (revize) — sürekli akrabalık: kısmen düzeltti, ölçütü geçmedi

Ölçüt: **[docs/faz9/olcut_surekli.md](olcut_surekli.md)** — koşumlardan **önce**
commit edildi (`58e579d`). Bileşen 1'in raporu: [melez.md](melez.md).

**Tek cümlelik sonuç:** Akrabalığı ikili eşikten sürekli orana çevirmek melez
zeminini **kısmen** onardı (ölçülebilirlik 2/5 → 3/5, referans zemin 4/5) ama
ilan edilmiş ölçüt (3/3, sonra 5/5) **geçilmedi** — bileşen 2 ve 3 bu zemine
kurulmuyor.

---

## 1. Ne değişti

Akrabalık artık `{-1,+1}` değil, **paylaşılan bileşen oranı**:

```
jaccard: |kesişim| / |birleşim|      {A,B} vs {B,C} = 1/3
mean   : |kesişim| / ort. etiket boyu {A,B} vs {B,C} = 1/2
```

Sensöre **ham** girer (`2r − 1`). Hiçbir yerde `r > x ise paylaş` biçiminde bir
eşik yoktur; kaynak testi (`test_threshold_never_enters_a_behaviour_branch`)
bunu denetler. Analizde kullanılan **dış-grup eşiği `r < 0.5`** yalnızca
in/out **sınıflandırması** içindir ve koşumdan önce sabitlendi.

### Geriye dönük uyum kanıtlandı (ölçüt A)

- Saf (tek bileşenli) etiketlerde iki formül de eski ikili değeri verir →
  `binary` ve `ratio` kolları **birebir aynı `state_hash`** (test).
- `ikili` kolu (melez açık, `kin_mode: binary`) bileşen 1'in sayılarını
  **birebir** tekrarladı: dış-grup payı %31.0 / %1.8 / %6.6 — bileşen 1
  raporundaki değerlerin aynısı.
- `energy_created` = 0, **15/15** koşumda (oran bir ölçüdür, enerji taşımaz).

---

## 2. Formül ölçülerek seçildi: `jaccard` (3/3)

Seçim kuralı koşumlardan önce yazıldı: **çift bazında genom benzerliğiyle daha
yüksek Pearson korelasyonu** veren formül. Kalibrasyon **tarafsız zeminde**
(`kin_mode: binary` koşumu) yapıldı — aday formülün kendi ürettiği popülasyonda
ölçmek kendi varsayımını ölçmek olurdu.

| seed | çift | melezli çift | **jaccard r** | mean r |
|---|---|---|---|---|
| 42 | 23 978 | 16 075 | **0.639** | 0.620 |
| 7 | 17 330 | 12 372 | **0.651** | 0.596 |
| 123 | 19 298 | 15 331 | **0.331** | 0.295 |

`jaccard` 3/3 seed'de önde. Fark küçük (0.02–0.06) ama işaret tutarlı.
Örneklem ölçüt dosyasındaki asgari 2000'in 8–12 katı.

---

## 3. ⚠ Melez oranı yeniden kalibre edilmek zorunda kaldı

İlk parti (`rate = 0.005`, bileşen 1'in oranı) sürekli kolda **melez payını
çökertti**: seed 7'de %1.1, seed 123'te %0.1. Sebep: sürekli kolda soy
çeşitliliği erken daraldı, melezleşme için gereken "menzilde **farklı saf
soydan** komşu" koşulu kalmadı. Yani melez önkoşulu (pay ≥ %5) **geçmedi**,
o kollardan hiçbir şey okunamazdı.

Ölçüt dosyasının önceden yazılmış kuralı: *"sağlanmazsa `rate` yükseltilir ve
**ölçütü geçen en küçük** değer pinlenir"*. Kalibrasyon (seed 7, sürekli kol):

| `rate` | melez payı | `opp_hybrid` | dış-grup payı | etkin soy |
|---|---|---|---|---|
| 0.005 | %1.1 | — | %8.6 | 2.99 |
| **0.02** | **%44.4** | **23 656** | %7.8 | 3.40 |
| 0.05 | %64.4 | 50 563 | **%27.2** | **9.64** |
| 0.10 | %26.6 | 14 321 | %2.2 | 2.95 |

**0.02 pinlendi** — önkoşulu geçen en küçük değer, üç kola da aynı uygulandı.

⚠ **0.05 asıl ölçütü (B) de geçiyordu ve seçilmedi.** Seçilseydi bu, parametreyi
*istenen sonucu verene kadar* ayarlamak olurdu; proje kuralı bunu açıkça
yasaklıyor ("ölçütü sonucu görmeden ilan edin"). Bu satır raporda duruyor ki
ileride birisi 0.05'i denemek isterse **neden seçilmediğini** bilsin.
⚠ Aralık **tek düze değil** (Faz 8'in `cost` kalibrasyonundaki gibi) ve tek
seed'de ölçüldü; "eşik eğrisi" diye okunmamalı.

---

## 4. ASIL SONUÇ — ölçüt B: 3/5 seed (ölçüt 5/5 istiyordu)

Son çeyrek, `rate = 0.02`, 5 seed × 3 kol:

| seed | kol | dış-grup | etkin soy | `genetic_r` | N | topla/kişi | melez payı | ölçüt |
|---|---|---|---|---|---|---|---|---|
| 42 | melez-yok | %49.7 | 10.24 | 0.42 (1.00×) | 634 | 0.0456 | %0 | GEÇTİ |
| 42 | ikili | %19.8 | 11.89 | 0.42 (1.00×) | 668 | 0.0431 | %50.9 | GEÇTİ |
| 42 | **sürekli** | %24.5 | 7.91 | 0.67 (1.61×) | 606 | 0.0487 | %53.5 | **GEÇTİ** |
| 7 | melez-yok | %11.9 | 4.43 | 0.80 | 571 | 0.0534 | %0 | geçmedi |
| 7 | ikili | %45.5 | 17.94 | 0.28 (0.35×) | 705 | 0.0416 | %46.6 | geçmedi |
| 7 | **sürekli** | %7.8 | 3.40 | 0.75 (0.95×) | 561 | 0.0544 | %44.4 | **geçmedi** |
| 123 | melez-yok | %16.2 | 5.64 | 0.74 | 613 | 0.0501 | %0 | GEÇTİ |
| 123 | ikili | %4.3 | 8.14 | 0.70 | 637 | 0.0479 | %61.1 | geçmedi |
| 123 | **sürekli** | %4.4 | 5.61 | 0.84 (1.14×) | 624 | 0.0487 | %45.4 | **geçmedi** |
| 1 | melez-yok | %45.8 | 15.11 | 0.67 | 594 | 0.0498 | %0 | GEÇTİ |
| 1 | ikili | %20.5 | 14.04 | 0.49 (0.74×) | 613 | 0.0475 | %59.4 | GEÇTİ |
| 1 | **sürekli** | %54.9 | 12.86 | 0.38 (0.58×) | 616 | 0.0468 | %92.6 | **GEÇTİ** |
| 777 | melez-yok | %49.8 | 10.93 | 0.44 | 632 | 0.0467 | %0 | GEÇTİ |
| 777 | ikili | %6.7 | 9.01 | 0.42 | 634 | 0.0459 | %75.1 | geçmedi |
| 777 | **sürekli** | %12.3 | 5.99 | 0.75 (1.71×) | 562 | 0.0534 | %51.4 | **GEÇTİ** |

**Özet:** sürekli **3/5**, ikili **2/5**, melez-yok (referans zemin) **4/5**.

- **Yön doğru, büyüklük yetmiyor.** Sürekli ölçü ikili ölçüden iyi (3/5 vs 2/5)
  ama zemin ölçütünü karşılamıyor.
- **Seed'ler arası fark kol farkından büyük.** Dış-grup payı sürekli−ikili:
  +4.7, **−37.7**, +0.1, +34.4, +5.6 puan. seed 7'de ikili kol sürekliden
  *çok* daha iyi, seed 1'de tam tersi. Beş nokta üzerinde bu **varyans**,
  ölçünün sistematik etkisi değil.
- **Koloni sağlığı korundu** (N %89–105, kişi başı toplama %95–107) ve
  `genetic_r` hiçbir seed'de yarıya inmedi (0.58×–1.71×) — ölçüt 3 ve 4
  5/5 geçti. Tökezleyen tek şart **dış-grup payı / etkin soy**.

Karar: **bileşen 2 (soy-arası matris) ve bileşen 3 (Faz 8'in işbirliği
gözleminin kontrollü sınaması) BU ZEMİNE KURULMAZ.** 2/5 seed'de okunamaz bir
zemin üzerinde matris okumak Faz 5/6'nın hatası olurdu.

---

## 5. Ölçüt C — iki sayı artık AYNI yönde

Bileşen 1'in rahatsız edici bulgusu: `lineage_effective` artarken dış-grup payı
düşüyordu (10.24 → 21.60 iken %49.7 → %31.0).

15 nokta (5 seed × 3 kol): **corr(etkin soy, dış-grup payı) = +0.699**.

Yani sürekli ölçüde "kaç farklı etiket var" ile "yabancı bulabiliyor muyum"
artık aynı yöne bakıyor. **Bu bir ölçüt değil, rapor edilen gözlemdir** (ölçüt
dosyası böyle yazıyor) — ama etiket enflasyonunun ölçümü kandırma kanalını
kapattığını gösteriyor: melez etiket artık `lineage_effective`'i şişirirken
dış-grup payını eritmiyor.

---

## 6. Ölçüt D — mandal duruyor (GÖZLEM)

Melez payı ilk çeyrek → son çeyrek, `rate = 0.02`:

| seed | ikili | sürekli |
|---|---|---|
| 42 | %16.5 → %50.9 | %10.7 → %53.5 |
| 7 | %13.9 → %46.6 | %9.7 → %44.4 |
| 123 | %9.8 → %61.1 | %6.8 → %45.4 |
| 1 | %5.4 → %59.4 | %45.5 → **%92.6** |
| 777 | %16.5 → %75.1 | %5.6 → %51.4 |

Sürekli akrabalık mandalı **çözmüyor** (kural aynı: melez saf döller); tek
yaptığı, mandalın ölçüm zeminine verdiği zararı **kısmen** tolere etmek.
Ölçüt B geçseydi "mandalı ayrıca çözmeye gerek yok" diyecektik; geçmediği için
**mandal hâlâ açık bir iş**.

---

## 7. Yan okuma — melez ayrımcılığı sürekli ölçüde de YOK (4/5)

Bileşen 1'in asıl sorusu 5 seed'de, sürekli akrabalıkla, kendi karıştırma
kontrolüne karşı yeniden okundu:

| karar | sonuç |
|---|---|
| **FARK YOK** | **4/5** |
| KÖPRÜ | 1/5 (seed 123) |
| DIŞLAMA | **0/5** |

Melez önkoşulu 5/5 geçti (pay %44–93, `opp_hybrid` 23 656–100 867). Bileşen
1'in "melez ayrımcılığa uğramıyor" sonucu, **farklı bir akrabalık ölçüsüyle ve
daha fazla seed'le** tekrarlandı.

### ⚠ Asimetri beşinci kez tekrarlandı

| seed | P(saldır \| yabancı) asıl | kontrol | P(saldır \| saf akraba) asıl |
|---|---|---|---|
| 42 | %16.6 | %1.8 | %3.6 |
| 7 | %46.0 | %2.3 | %9.9 |
| 123 | %49.2 | %4.3 | %4.7 |
| 1 | %6.6 | %5.5 | %4.2 |
| 777 | %41.4 | %2.2 | %9.5 |

Yabancıya saldırı, etiketin bilgisiz olduğu kontrolün **10–20 katı** (4/5
seed); akrabaya saldırı kontrol seviyesinde. Paylaşımda böyle bir ayrım yok
(%0.3–4.8, kontrol %0.3–0.8). **Korunumlu zeminde düşmanlık ayrım gözetiyor,
fedakârlık gözetmiyor** — Faz 4.5, 4.6, 6 ve 9/bileşen 1'den sonra beşinci
tekrar, bu kez *sürekli* akrabalık tanımıyla.

---

## 8. Yol boyunca yakalanan iki artefakt

1. **`population.npz` melez etiketi kaybediyordu.** `surname2` kayda hiç
   yazılmıyordu; kaydedilmiş bir melez koloni geri yüklendiğinde **saf**
   görünüyordu — yani "melez tohum" diye bir şey olamazdı. Faz 6'da
   parametrelerin taşınmaması mekaniği sessizce öldürmüştü; aynı tuzağın
   etiket versiyonu. Düzeltildi, iki testle sabitlendi (eski kayıtlar hâlâ
   yükleniyor: alan yoksa hepsi saf sayılır).
2. **İlk parti ölçümsüzdü ve bunu önkoşul yakaladı.** `rate = 0.005`'te
   sürekli kolun melez payı %0.1'e düştü; önkoşul (pay ≥ %5) olmasaydı "sürekli
   akrabalık dış-grup payını korudu" diye **yanlış pozitif** raporlanacaktı —
   oysa orada okunacak melez yoktu.

---

## 9. Denenmemiş kalanlar

Ölçüt B'yi geçen bir zemin için sıradaki adaylar (hiçbiri koşulmadı):

1. **Melez saf döllemesin** — etiket bir nesil sonra kaybolsun. Mandalın
   kaynağı bu kuraldı; kaldırmak doyumu kökten keser.
2. **Melezleşme menzilini daraltmak** — ⚠ Faz 4.6: hareketi kısmak koloniyi
   çökertiyor; yan etkisi ölçülmeli.
3. **Faz 8'in denenmemiş iki kaldıracı**: geniş dünya ve uzamsal sığınaklar.
   Melez-yok kolu 4/5 ile zaten en iyi zemin; onu **yukarı** çekmek, melezin
   yediği payı tolere edilebilir kılabilir.

## Yeniden üretim

```bash
# formul kalibrasyonu (TARAFSIZ zemin: binary kosum)
python tools/kin_ratio_probe.py --seeds 42 7 123

# uc kol (+ karistirma kontrolu), pinlenmis rate 0.02
for s in 42 7 123 1 777; do
  python run.py --config experiments/faz9_surekli.yaml --seed $s --viz none \
    --set rules.hybrid.enabled=false --name f9d_melezyok_s$s
  python run.py --config experiments/faz9_melez.yaml --seed $s --viz none \
    --set rules.hybrid.rate=0.02 --name f9d_ikili_s$s
  python run.py --config experiments/faz9_surekli.yaml --seed $s --viz none \
    --set rules.hybrid.rate=0.02 --name f9d_surekli_s$s
  python run.py --config experiments/faz9_surekli.yaml --seed $s --viz none \
    --set rules.hybrid.rate=0.02 --set rules.kinship.control=shuffle_surnames \
    --name f9d_karistirma_s$s
done
python tools/continuous_kin_report.py --prefix f9d --seeds 42 7 123 1 777
python tools/hybrid_report.py --prefix f9d --main surekli --seeds 42 7 123 1 777
```

Kaydedilmiş sürekli-akrabalık kolonisi: `docs/faz9/population_surekli.npz`
(seed 42; artık melez etiketi de taşıyor).
