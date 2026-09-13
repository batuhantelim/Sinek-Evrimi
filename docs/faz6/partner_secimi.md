# Faz 6 — partner seçimi: işbirliğinin üçüncü mekanizması

Ölçüt dosyası koşumlardan önce yazıldı: **[olcut.md](olcut.md)** (git geçmişi
tanıktır). Bu rapor o ölçütlerin karşılığını verir.

İki mekanizma elenmişti: akrabalık (Faz 4.6, `r·b/c` ≤ 0.989, 0/15 koşul) ve
karşılıklılık (Faz 5, 0/5 seed). Üçüncüsü yapısal olarak farklıydı: partner
seçimi `r·b > c` eşitsizliğini *aşmaya* çalışmaz, eşitsizliğin **kimin
arasında** kurulduğunu değiştirir.

**Sonuç: partner seçimi de işbirliğini kurmadı** — ama bir *dışlama* politikası
gerçekten evrimleşti, ve yükselen şey işbirliğinden çok düşmanlık oldu.

---

## 0. ⚠ İlk parti hiç ölçüm yapmamıştı — iki ayrı sessiz arıza

İlk üç kol × üç seed koştuğunda seçim kolu, seçimsiz kolla **birebir aynı**
`state_hash`'i verdi. İki bağımsız neden vardı ve ikisi de sessizdi:

1. **Kayıtlı genomlarda `pick_*` parametreleri yoktu.** `load_population`
   yalnızca dosyada yazılı isimleri yüklüyor, `mutate` de mevcut anahtarlar
   üzerinde geziyordu; dolayısıyla beş yeni parametre ne yüklendi ne mutasyona
   uğradı. Ağırlık taşıması (`migrate_weights`) Faz 2'den beri vardı, ama
   **parametre** taşıması yoktu. Eklendi ve artık
   `meta["migrated"]["new_params"]` ile **raporlanıyor** — sessizce genom
   değiştirmek tam olarak gizlenmemesi gereken şeydir.
2. **Aday havuzu ortalama 1.35 kişi.** `kinship.radius = 2.5` ile çoğu ajanın
   menzilinde tek komşu var. Seçenek yoksa "seçim" diye bir şey de yoktur.

Bu, Faz 5'in "üç önkoşul" disiplininin aynısı: **seçim, seçenek olmadan
ölçülemez.** Önkoşul ilan edildi (havuz ≥ 2.0 **ve** kararların ≥ %50'si çok
adaylı), menzil tarandı ve ölçütü geçen **en küçük** değer (`radius = 5.0`)
**üç kola da aynı** uygulandı. Yan etkiler ([olcut.md](olcut.md) eki):
popülasyon 644 → 668, kişi başı toplama 0.0447 → 0.0454, `genetic_r` sabit,
enerji üretimi 0.0.

Yeni `pool_multi` sütunu bunu bir daha sessiz bırakmaz: ortalama havuz tek
başına yetmez, 1 ve 4 adaylı kararların karışımı da 2.5 ortalama verir.

---

## 1. Önkoşul sağlandı, korunum tam

5 seed × 3 kol = 15 koşum, 12000 adım, hepsi `docs/faz5/population_hafiza.npz`
tohumundan.

| ölçü | seçim kolu | rastgele kol |
|---|---|---|
| ortalama aday havuzu | 2.57–2.91 | 2.43–2.60 |
| çok adaylı karar | %74.8–83.3 | %71.6–75.2 |
| en-yakın-değil seçim | %16.1–64.5 | %45.6–49.1 |
| `energy_created` | **0.0 (15/15)** | 0.0 |

Önkoşul 10/10 kolda geçti. Enerji korunumu 15/15 koşumda tam — ölçüt 1 sağlandı.

### ⚠ Ölçüt 2 GEÇMEDİ: akrabalık kanadı bu zeminde okunamaz

Dış-grup fırsat payı **%0.1–2.0** (ölçüt ≥ %10 istiyordu) ve etkin soy sayısı
**~1.0**. Faz 5 tohumu tek soya inmiş bir koloni: herkes akraba. Dolayısıyla
`pick_kin_sel` iki sıfırın farkıdır ve Welch t'si büyük çıkabilir (seed 42'de
+14.73!) — rapor o hücreyi **OKUNMAZ** diye bayraklar ve özete katmaz.
Bu, ana soruyu (işbirliği tabanın üstüne çıktı mı) etkilemez; yalnızca
"akrabaya mı veriyor" sorusu bu zeminde sorulamaz.

---

## 2. ASIL ÖLÇÜT (3): işbirliği taban bandından ÇIKMADI

Son çeyrek paylaşım oranı, her seed kendi **seçimsiz** kontrolüne karşı:

| seed | seçim | seçimsiz | fark | Welch t | rastgele | t(seçim−rastgele) |
|---|---|---|---|---|---|---|
| 42 | 0.89% | 0.44% | +0.45 | **+13.64** | 0.92% | −0.80 |
| 7 | 0.71% | 0.98% | −0.27 | −4.31 | 0.55% | +2.65 |
| 123 | 0.86% | 0.57% | +0.29 | **+6.11** | 0.78% | +1.58 |
| 1 | 0.45% | 0.98% | −0.53 | −14.16 | 1.18% | −11.08 |
| 777 | 0.93% | 0.78% | +0.15 | **+3.61** | 0.95% | −0.29 |

- **Kontrolden yukarı ayrışma: 3/5 seed.**
- **Taban bandından (%0.6–2.4) çıkma: 0/5 seed.** En yüksek değer %0.93.
- Ölçüt ikisini **birlikte** istiyordu → **KURMADI**.

Ölçüt dosyasındaki cümle şuydu: *"Faz 4.5/4.6/5'te taban %0.6–2.4 bandındaydı;
'kurdu' demek için bu banttan çıkması gerekir."* Aracın ilk sürümü yalnızca
Welch t'ye bakıyor ve "2/3 GEÇTİ → PARTNER SEÇİMİ İŞBİRLİĞİNİ KURDU" yazıyordu.
İkinci şart koda eklendi (`BASELINE_HIGH`) ve test artık aracı ölçüt dosyasıyla
karşılaştırıyor. **"Kontrolden yukarı ayrıştı" ile "işbirliğini kurdu" aynı şey
değildir.**

### Ve ayrışan yerlerde bile kaynağı politika değil

Rastgele-seçim kontrolü tam bunun için ilan edilmişti: "seçme yeteneği mi,
seçimin akıllı kullanımı mı". **4/5 seed'de seçim kolu rastgeleden yukarı
ayrışmıyor**; seed 42'de rastgele kol daha yüksek (%0.92 vs %0.89), seed 1'de
belirgin biçimde daha yüksek (%1.18 vs %0.45).

Yani 0.44% → 0.89% yükselişini yapan şey **havuzun varlığı**, evrimleşen
politika değil. Hedefin artık hep en yakın olmaması sosyal etkileşimin
dağılımını değiştiriyor; kimin seçildiğine karar veren ağırlıklar bunu
iyileştirmiyor.

---

## 3. Havuz işbirliğini değil DÜŞMANLIĞI büyütüyor

Aynı karşılaştırma saldırı oranında (seçimsiz → rastgele seçim, ×kat):

| seed | paylaşım | saldırı |
|---|---|---|
| 42 | ×2.09 | **×4.92** |
| 7 | ×0.56 | ×1.24 |
| 123 | ×1.37 | **×2.91** |
| 1 | ×1.21 | ×0.65 |
| 777 | ×1.23 | **×2.31** |
| medyan | ×1.23 | **×2.31** |

4/5 seed'de saldırı paylaşımdan daha çok büyüyor. Faz 4.5 ve 4.6'nın yan
bulgusu (**korunumlu zeminde düşmanlık ayrım gözetir, fedakârlık gözetmez**)
burada üçüncü bir biçimde tekrarlandı: partner seçimi eklendiğinde de kârlı
hale gelen şey vermek değil, almak.

---

## 4. ÖLÇÜT (4): bir dışlama politikası GERÇEKTEN evrimleşti

`tools/exclusion_probe.py` simülasyonu değiştirmez (`_note_pick` sarılır; test
`state_hash` eşitliğini sabitler) ve iki dışlamayı ayırır:

- **YAPISAL**: her kararda bir kişi seçildiği için havuz 2.9 iken %65'i
  seçilmez. Bilgi değil, aritmetik.
- **BİREYSEL**: bir ajanın **karşılaştığı** farklı partnerlerin kaçı ona hiç
  seçilmedi.

Evrimleşmiş seçim popülasyonu, aynı genomlarla iki kez koşuldu — bir kez kendi
politikasıyla, bir kez rastgele seçimle:

| seed | bireysel dışlama (politika) | bireysel dışlama (rastgele) | kat |
|---|---|---|---|
| 42 | 31.8% | 7.4% | ×4.3 |
| 7 | 12.3% | 6.7% | ×1.8 |
| 123 | 26.6% | 6.4% | ×4.2 |
| 1 | 36.6% | 6.5% | ×5.6 |
| 777 | 29.4% | 6.6% | ×4.5 |

**5/5 seed'de politika rastgeleden belirgin biçimde daha dışlayıcı.** Rastgele
kolun %6.4–7.4 bandı neredeyse sabit — beklendiği gibi, çünkü rastgele seçim
zamanla herkesi bir kez seçer. Yani seçim yeteneği kullanıldı ve **sistematik**
kullanıldı: karşılaşılan partnerlerin yaklaşık üçte biri hiç hedef olmuyor.

### Ama dışlama "kötü verici"yi dışlamıyor

Seçilen ve seçilmeyen adayların defteri pozitif olma oranı (aynı sonda):

| seed | politika: seçilen / seçilmeyen | oran | rastgele: seçilen / seçilmeyen | oran |
|---|---|---|---|---|
| 42 | 11.19% / 5.07% | **2.21** | 17.82% / 14.42% | 1.24 |
| 7 | 3.13% / 3.64% | 0.86 | 7.04% / 5.18% | 1.36 |
| 123 | 7.50% / 6.39% | 1.17 | 8.46% / 6.52% | 1.30 |
| 1 | 2.65% / 2.66% | 1.00 | 5.09% / 4.40% | 1.16 |
| 777 | 6.81% / 6.42% | 1.06 | 10.80% / 9.33% | 1.16 |

Politika kolunun oranı (medyan 1.06) rastgele kolun oranından (medyan 1.24)
**yüksek değil**; 4/5 seed'de daha düşük. Yani dışlama var ama "bana verene
veririm" biçiminde değil.

⚠ **Yalnızca seed 42'ye bakılsaydı** (2.21 vs 1.24) "karşılıklı seçim
evrimleşti" denecekti. Faz 5'te de aynı tuzak seed 42'de kurulmuştu.

### ⚠ Aynı sonda, referansa göre ZIT işaret veriyor

`pick_ledger_sel` (seçilen − **en yakın**) 5 seed'de çoğunlukla **negatif**
(−0.0085…−0.0262): politika defteri pozitif partnerden **uzaklaşıyor**.
Sondanın "seçilen vs **seçilmeyen**" karşılaştırması ise seed 42'de **pozitif**.
İkisi çelişmiyor — farklı sorulara cevap veriyorlar: en yakın komşu, tekrarlı
bitişiklik yüzünden havuz ortalamasından **daha sık** defteri pozitiftir.
Politika yoksa seçilecek olan en yakındır, dolayısıyla **politikanın kendi
katkısı ancak en yakına karşı** izole edilir (bu, `pick_kin_sel` referansının
neden havuz değil en yakın olduğunun aynı gerekçesi; kod yorumunda ve testte
sabitlenmiştir).

### Evrimin yönü: tek tutarlı işaret `pick_ledger`

| seed | kin | ledger | need | energy | dist |
|---|---|---|---|---|---|
| 42 | −0.177 | −0.087 | +0.079 | +0.036 | +0.139 |
| 7 | +0.061 | **−0.406** | −0.270 | +0.051 | −0.184 |
| 123 | −0.130 | −0.027 | +0.164 | +0.081 | +0.104 |
| 1 | −0.034 | −0.124 | +0.081 | −0.073 | +0.190 |
| 777 | +0.056 | −0.072 | +0.039 | −0.047 | +0.075 |

`pick_ledger` **5/5 seed'de negatif** (hepsi 0.0'dan başladı); `pick_dist` 4/5
pozitif, diğer üçünün işareti dönüyor. İşaret testi zayıf bir sinyal
(tek yönlü p ≈ 0.03) ama **davranışa tutarlı biçimde yansımıyor**: ölçüt 4'ün
okunabilir kanadı (`pick_ledger_sel` vs rastgele) yalnızca 3/5 seed'de ayrıştı
ve **işareti bile sabit değil** (seed 42 ve 7'de rastgeleden daha negatif, seed
1'de daha pozitif). Parametre sürüklenmesi davranış kanıtı değildir.

---

## 5. Sonuç

| soru | cevap |
|---|---|
| Önkoşul (seçilecek bir şey var mı) | ✅ havuz 2.57–2.91, çok adaylı %75–83 |
| Ölçüt 1 — korunum | ✅ `energy_created` = 0, 15/15 koşum |
| Ölçüt 2 — ölçülebilirlik | ❌ dış-grup payı %0.1–2.0 → **akrabalık kanadı okunmaz** |
| **Ölçüt 3 — işbirliği tabanı aştı** | ❌ ayrışma 3/5 ama banttan çıkma **0/5**; 4/5 seed'de rastgele seçim de aynısını yapıyor |
| Ölçüt 4 — politika evrimleşti | ⚠ **kısmen**: dışlama 5/5 seed'de rastgeleden ayrıştı, ama "iyi vericiyi seç" biçiminde değil |
| Yan bulgu | havuz düşmanlığı paylaşımdan daha çok büyütüyor (medyan ×2.31 vs ×1.23) |

**İşbirliğinin üç büyük mekanizması da bu minimal dünyada çalışmadı:**
akrabalık (Faz 4.6), karşılıklılık (Faz 5), partner seçimi (Faz 6). Üçü de
kendi önkoşulları **ölçülerek** sağlandıktan sonra reddedildi — "koşul yoktu"
mazereti hiçbirinde geçerli değil. Faz 6'da ayrıca seçim yeteneğinin
**kullanıldığı** gösterildi (dışlama 5/5), yani negatif "mekanik ölü kaldı"
değil, "mekanik çalıştı ve işbirliği üretmedi".

### Hipotez (ölçülmedi)

Faz 5'in sonunda yazdığımız hipotez güçlendi: paylaşımın taban oranı ~%1 ve
partner seçimi bunu değiştirmiyor. Karşılıklılık gibi partner seçimi de
**üzerine kurulacağı işbirliği** olmadığı için başlayamıyor olabilir —
seçilecek "iyi verici" sınıfı fiilen yok (defteri pozitif aday payı %2.7–17.8
ve çoğu seed'de %10'un altında). Faz 4.6 bu kıtlığın nedenini gösterdi
(`r·b/c < 1`). Sınamak için paylaşımı **ödüllendirmeden** dışarıdan yükseltip
(örneğin bir kısmını zorunlu kılıp) seçimin o zaman ayrım yapmaya başlayıp
başlamadığına bakmak gerekir.

---

## 6. Sınırlar — ne DEMİYORUZ

- **"Partner seçimi işbirliği kurmaz" demiyoruz.** Bu dünyada, bu ekolojide,
  bu 15 koşumda kurmadı. Dış-grup payı %2 ve etkin soy 1 olan bir zeminde
  ölçüldü; soy çeşitliliği olan bir zeminde sonuç farklı olabilir.
- **Dışlamanın *neyi* hedeflediğini bilmiyoruz.** Seçim, paylaşımı **ve**
  saldırıyı aynı partnere yöneltir (ikisi birbirini dışlar), dolayısıyla
  "kimi seçtim" tek başına "kime vermeyi seçtim" demez. Eylem bazlı seçicilik
  ölçümü (paylaşılan hedefler vs saldırılan hedefler ayrı) yapılmadı.
- **`k = 4` sabit tutuldu.** Daha büyük havuzun (daha çok seçenek) sonucu
  değiştirip değiştirmediği taranmadı.
- **Sonda 3000 adım** (korunum sondada da tam: `energy_created` = 0.0), ana koşumlar 12000. Dışlama oranı ufka göre değişebilir;
  kalibrasyonu tam ufukta yapma kuralı (Faz 4) sonda için denetlenmedi.
