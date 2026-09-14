# Faz 7 — çeşitlilik altyapısı ve taze-zemin sınaması

Ölçüt koşumlardan önce yazıldı: **[olcut.md](olcut.md)**.

Bu faz yeni bir sosyal mekanizma aramıyor; son üç negatifin (akrabalık,
karşılıklılık, partner seçimi) **ölçülemez bir zeminin artefaktı** olup
olmadığını sınıyor.

**Kısa sonuç: hipotez kısmen doğrulandı ama nedeni beklediğimiz değildi.**
Zincirin kendisi suçlu değil; suçlu **seçilim süpürgesi**. Ve taze başlangıç
sorunu çözmüyor — **büyütüyor**.

---

## 1. ⚠ Premis yanlış çıktı: taze başlangıç çeşitliliği KORUMUYOR

Aynı rejim (Faz 4.5 temiz ekolojisi), aynı seed, tek fark tohum:

| koşum | etkin soy | soy sayısı | dış-grup payı | ağırlık çeşitliliği | topla/kişi |
|---|---|---|---|---|---|
| tohumlu (taban) / s42 | **13.95** | 37.0 | **53.6%** | 0.3915 | 0.0389 |
| **taze** / s42 | 1.33 | 6.2 | 2.6% | 0.3449 | 0.0465 |
| tohumlu (taban) / s7 | **8.92** | 30.5 | **42.9%** | 0.4010 | 0.0401 |
| **taze** / s7 | 1.02 | 3.2 | 0.5% | 0.3234 | 0.0388 |

Beklenti "taze kol daha çeşitli olur"du. Ölçüm tersini söylüyor: taze kolda
soylar **12000 adım boyunca değil, ilk 500 adımda** çöküyor.

Soy çöküşünün şekli sürüklenme değil, **süpürge**:

| dönem | 0 | 1 | 2 | 4 | 7 | 11 | 15 | 19 | 23 |
|---|---|---|---|---|---|---|---|---|---|
| taban, en büyük soy % | 2.3 | 4.2 | 5.6 | 8.6 | 10.1 | 13.3 | 17.8 | 26.0 | 20.5 |
| ekoloji, en büyük soy % | 1.5 | 2.1 | 4.3 | 6.8 | 15.5 | 44.3 | **59.9** | **81.9** | 56.6 |
| taze, en büyük soy % | **31.6** | 36.4 | 48.7 | 65.8 | 72.2 | 66.3 | 69.5 | 89.2 | **98.8** |

Taze koloni rastgele ağlarla başlar; içlerinden birkaçı çalışan bir kemotaksis
devresine sahiptir ve **hepsini alır**. Bu, Faz 2'nin bulgusunun (kemotaksis
sıfırdan evrimleşiyor) doğrudan sonucu: sıfırdan evrim **güçlü yönlü
seçilimdir**, güçlü yönlü seçilim ise soy çeşitliliğini siler.

## 2. Çöküşün nedeni tohumlama değil: 2×2 ayrıştırdı

`tohum (taban / ekoloji)` × `hafıza (kapalı / açık)`, aynı rejim, seed 42:

| | hafıza kapalı | hafıza açık |
|---|---|---|
| **taban** tohumu | etkin soy **13.95**, dış %53.6 ✅ | **9.47**, %53.2 ✅ |
| **ekoloji** tohumu | 2.56, %10.4 ❌ | 2.96, %8.5 ❌ |

Hafıza (Faz 5 mekaniği) neredeyse hiçbir şey yapmıyor. Belirleyen **tohum
popülasyonu**. Yani "her tohumlama çeşitliliği bir kademe daralttı" ifadesi de
yanlış: daralma kademeli değil, **belirli bir tohumla** oluyor.

Kaydedilmiş popülasyonların genom çeşitliliği zincir boyunca **azalmıyor**:

| popülasyon | ağırlık çeşitliliği | o tohumla koşulan rejimde etkin soy |
|---|---|---|
| `faz4tani/population_taban.npz` | **0.2553** (en dar) | **13.95** (en çeşitli) |
| `faz45/population_ekoloji.npz` | **0.3683** (en geniş) | **2.56** |
| taze (rastgele 0. nesil) | en geniş (bağımsız ağlar) | **1.33** (en çökük) |
| `faz5/population_hafiza.npz` | 0.2806 | — |
| `faz6/population_secim.npz` | 0.2896 | — |

**Sıralama ters**: başlangıçta genom çeşitliliği ne kadar yüksekse, soy
çeşitliliği o kadar hızlı çöküyor. Mekanizma tutarlı (seçilimin üzerinde
çalışacağı varyans ne kadar çoksa süpürge o kadar güçlü), ama bu **üç nokta**;
örüntü iddiası değil, hipotez.

⚠ Bunun rahatsız edici sonucu: bu tasarımda **etiket çeşitliliği ile genom
çeşitliliği birbirini iter**. "Hem çok soy hem çok genetik varyans" bir ayar
noktası değil, bir gerilim.

## 3. Göçmen mekaniği: gerçek genetik çeşitlilik, ama süpürgeyi durdurmuyor

`evolution.immigration_rate`: doğumların bu oranında yavrunun genomu
ebeveynden **değil** taze bir kurucudan gelir ve yeni bir soy açar.

- **Enerji defteri temiz**: göçmen bir **doğumun yerine geçer** — ebeveyn aynı
  maliyeti öder, yavru aynı enerjiyle başlar. Koloniye enerji eklemez; test
  üreme öncesi/sonrası enerji farkının iki kolda **birebir aynı** olduğunu
  sabitler. (Faz 4.5'in dersi: enerji aktaran her yeni kural önce defterde
  sınanır.)
- **0.0'da hiçbir rastgele çekim yapılmaz** → Faz 1–6'nın bütün `state_hash`
  değerleri birebir korunur (test).
- `split_rate`'ten farkı: o yalnızca **etiket** üretir (bölünen soy bölündüğü
  anda ebeveyniyle genetik olarak aynıdır), göçmen **genom** üretir.

Taze zeminde altı oran, 12000 adım, seed 42:

| `immigration_rate` | etkin soy | soy sayısı | dış-grup payı | topla/kişi | işbirliği | E_yaratılan |
|---|---|---|---|---|---|---|
| 0.0 | 1.33 | 6.2 | 2.6% | 0.0465 | 1.59% | 0 |
| 0.005 | 1.18 | 11.3 | 4.5% | 0.0354 | 0.12% | 0 |
| 0.01 | 1.09 | 7.7 | 1.9% | — | — | 0 |
| 0.02 | 1.68 | 15.2 | **12.7%** | 0.0365 | 0.22% | 0 |
| 0.05 | 1.29 | 13.7 | 4.2% | — | — | 0 |
| 0.10 | 1.71 | 13.3 | 4.1% | — | — | 0 |

**0/6 koşul ölçütü geçti.** Doğumların **onda biri** taze kurucu olsa bile
etkin soy 1.71'de kalıyor: göçmen acemi doğar ve süpürge onu anında eliyor.
Yeni soy **açılıyor** (soy sayısı 6.2 → 15.2) ama **tutunamıyor**.

Tek yan kazanç: `0.02`'de dış-grup fırsat payı %12.7'ye çıkıyor — ölçütün
**ölçülebilirlik** yarısı geçiyor, etkin soy yarısı geçmiyor. İkisini birlikte
istediğimiz için koşul "GEÇMEDİ" sayılır; goalpost taşınmaz.

**Bedel ölçüldü**: kişi başı toplama 0.0465 → 0.0354 (−24%). Göçmen oranı
yetkinliği düşürüyor ve bunu çeşitlilik kazancı karşılamıyor.

## 4. Denetim: hangi faz hangi zeminde ölçüldü?

Ölçüt 1B (etkin soy ≥ 5.0 **ve** dış-grup payı ≥ %10) geçmişe uygulandığında:

| koşum | etkin soy | dış-grup payı | durum |
|---|---|---|---|
| **Faz 4.5 akrabalık testi** (taban tohumu, 5 seed) | 1.86 / 5.99 / 9.79 / 11.00 / 12.15 | 9.5–57.7% | **4/5 GEÇTİ** |
| Faz 4.5 karıştırma kontrolü (s42 / s7) | 26.93 / 33.26 | 95.4% / 95.9% | GEÇTİ |
| **Faz 4.6 kontrollü evrim** (BC6, s42 / s7) | 11.18 / 13.17 | 14.5% / 18.7% | GEÇTİ |
| Faz 4.6 `BC10` kolu (s42) | 5.94 | 3.0% | GEÇMEDİ |
| **Faz 5 hafızalı** (s42) | 1.03 | 0.4% | **GEÇMEDİ** |
| Faz 5 defter kontrolü (s42) | 1.43 | 4.6% | GEÇMEDİ |
| **Faz 6 seçim** (s42) | 1.00 | 0.1% | **GEÇMEDİ** |
| Faz 6 seçimsiz (s42) | 1.04 | 0.5% | GEÇMEDİ |

**Akrabalık negatifi çeşitlilik artefaktı DEĞİL.** Faz 4.5'in "in-grup
fedakârlık 0/5 seed'de kontrolden ayrıştı" bulgusu, 4/5 koşumda etkin soy
5.99–12.15 ve dış-grup payı %40–58 olan bir zeminde ölçülmüş. Faz 4.6'nın
kontrollü evrim testi de ölçütü geçiyor. Bu iki negatif **sağlam**.

**Karşılıklılık (Faz 5) ve partner seçimi (Faz 6) negatifleri ise ölçülemez
zeminde üretildi**: etkin soy ~1, dış-grup payı %0.1–4.6. Faz 6'nın raporu bunu
zaten "AKRABALIK KANADI OKUNMAZ" diye bayraklamıştı; şimdi aynı sorunun Faz 5'i
de kapsadığı ölçülmüş oldu.

⚠ Bu, "o negatifler yanlıştı" demek değildir — "o zeminde okunamazdı" demektir.
Karşılıklılık ölçüsü (`recip_bias_adj`) akrabalık etiketine bakmaz, dolayısıyla
soy çöküşünden doğrudan etkilenmez; ama koloni tek bir soya indiğinde genetik
çeşitlilik de, davranış çeşitliliği de dar olur ve "veren/vermeyen" sınıfları
ayrışmaz. Bu yüzden Faz 5 **geçerli zeminde tekrarlanır** (Bölüm 5).

## 5. Onarım: taze değil, DOĞRU TOHUM

Ölçüt 1B'yi geçen zemin elimizde zaten vardı: **`docs/faz4tani/population_taban.npz`
+ Faz 4.5 temiz ekolojisi**. 2×2 bunun hafıza açıkken de geçerli olduğunu
gösterdi (etkin soy 9.47, dış-grup %53.2).

Yani Faz 5 ve Faz 6 için doğru düzeltme "taze başlamak" değil, **zinciri bir
halka geriye alıp `taban` tohumundan başlamak**. Faz 7'nin somut çıktısı budur.

---

## 6. Bölüm 3 — akrabalık: negatif GERÇEK, tekrar koşum gerekmedi

Ölçüt dosyasındaki plan "akrabalığı taze zeminde yeniden test et"ti. Ölçüm
planı değiştirdi ve **daha iyi bir cevap** verdi:

1. Taze zemin, akrabalık ölçümü için **daha kötü** bir zemindir (etkin soy 1.3,
   dış-grup %2.6). Orada tekrar etmek, ölçülebilirliği düşürmek olurdu.
2. Faz 4.5'in akrabalık testi **zaten ölçütü geçen bir zeminde** yapılmış:
   4/5 koşumda etkin soy 5.99–12.15, dış-grup payı %40–58; karıştırma
   kontrolleri %95. Faz 4.6'nın kontrollü evrim testi de geçiyor (11.18/13.17).

Dolayısıyla **akrabalık negatifi çeşitlilik artefaktı değil**: `r·b/c` ≤ 0.989
ve "in-grup fedakârlık 0/5 seed'de kontrolden ayrıştı" sonuçları, bol soylu ve
bol dış-grup fırsatlı bir zeminde üretilmiş. Ölçüt dosyasındaki karar kuralının
birinci satırı: *negatif gerçekmiş, sağlamlaştı.*

## 7. Karşılıklılık (Faz 5) geçerli zeminde TEKRARLANDI — sonuç değişmedi

Faz 5'in kendi zemini ölçütü geçmiyordu (etkin soy 1.03, dış-grup %0.4), bu
yüzden onu geçerli zeminde (aynı rejim, `taban` tohumu) 5 seed tekrar ettik.
Her seed kendi `shuffle_ledger` kontrolüyle:

| seed | karşılıklılık `t` | misilleme `t` | paylaşım | etkin soy | dış-grup payı | defter+ fırsat | E_yaratılan |
|---|---|---|---|---|---|---|---|
| 42 | −0.00 | −3.08 | 0.66% | 9.47 | 53.2% | 10 351 | 0 |
| 7 | −3.79 | +6.27 | 0.93% | 4.45 | 24.6% | 8 168 | 0 |
| 123 | **+4.43** | −1.74 | 1.33% | 10.29 | 54.2% | 16 401 | 0 |
| 1 | +1.39 | **+2.21** | 0.96% | 9.73 | 51.0% | 11 486 | 0 |
| 777 | −0.80 | −2.12 | 2.17% | 2.97 | 14.9% | 14 600 | 0 |

| ölçü | eski zemin (Faz 5) | geçerli zemin (Faz 7) |
|---|---|---|
| karşılıklılık ayrıştı | 0/5 (`t` = −0.94 ± 1.56) | **1/5** (`t` = +0.25 ± 3.01) |
| misilleme ayrıştı | 1/5 | **2/5** (ölçüt ≥4/5) |
| etkin soy | 1.03–1.19 | **2.97–10.29** |
| dış-grup payı | %0.4–1.6 | **%14.9–54.2** |
| enerji korunumu | tam | tam (10/10) |

**Karşılıklılık yine evrimleşmedi.** Soy çeşitliliği 8×, dış-grup fırsat payı
34× arttığı hâlde işaret hâlâ tutarsız (üç seed'de negatif, biri kontrol lehine
−3.79) ve ortalama `t` sıfırdan ayırt edilemiyor. Paylaşımın taban oranı da
değişmedi (%0.66–2.17, eski bandın içinde).

⚠ Yan not: iki seed (7 ve 777) ölçütün **etkin soy** yarısını geçemedi (4.45 ve
2.97) ama **dış-grup payı** yarısını geçti. Bu iki seed'in `t` değerleri
diğerlerinden sistematik biçimde farklı değil — yani sonuç, ölçütün sıkı
okunuşunda (3/5 koşum tam geçerli) da gevşek okunuşunda (5/5) da aynı.

## 8. Partner seçimi (Faz 6) da geçerli zeminde tekrarlandı — verdict aynı, ama ölçüm artık OKUNUYOR

Faz 6'nın zemini en kötüsüydü (etkin soy 1.00, dış-grup %0.1). Aynı rejim,
`taban` tohumu, 5 seed × 3 kol:

| seed | seçim | seçimsiz | Welch t | rastgele | t(seçim−rastgele) |
|---|---|---|---|---|---|
| 42 | **3.02%** | 0.68% | +8.95 | 0.53% | **+9.74** |
| 7 | 0.43% | 0.72% | −7.45 | 0.60% | −5.95 |
| 123 | 0.97% | 0.52% | +8.91 | 0.96% | +0.22 |
| 1 | 0.77% | 0.62% | +1.55 | 1.02% | −2.29 |
| 777 | 0.96% | 0.64% | +6.67 | 0.80% | +2.11 |

- Kontrolden ayrışma **3/5** (eskiden 3/5) — aynı.
- Taban bandından çıkma **1/5** (eskiden 0/5). Ölçüt ≥4/5 istiyor → **KURMADI**.
- Rastgele seçim 3/5 seed'de aynısını yapıyor → artışın kaynağı yine mekanik.

**Değişen şey verdict değil, ÖLÇÜLEBİLİRLİK.** Dış-grup fırsat payı seçim
kolunda %0.1 → **%17.0–40.9**. Bu sayede Faz 6'da "OKUNMAZ" diye bayrakladığımız
akrabalık kanadı artık okunuyor:

| seed | `pick_kin_sel` seçim | rastgele | t |
|---|---|---|---|
| 42 | −0.0312 | −0.0533 | +1.72 |
| 7 | −0.0203 | −0.0633 | **+16.98** |
| 123 | −0.0534 | −0.0634 | +2.08 |
| 1 | −0.0188 | −0.0609 | **+12.21** |
| 777 | −0.0786 | −0.0629 | −1.15 |

Evrimleşen politika, **rastgele seçimden daha sık akraba seçiyor** (4/5 seed),
ama yine de **en yakın komşudan daha az** (hepsi negatif). Yani seçim akrabaya
doğru değil, akrabadan **daha az uzağa** kayıyor. Bu ayrım ancak soy
çeşitliliği varken görülebilirdi.

⚠ Yan bulgu: seçim mekaniğinin **kendisi** soy çeşitliliğini düşürüyor —
etkin soy seçim kolunda 2.41–5.23, seçimsiz kolda 8.97–13.42, rastgelede
8.35–14.21. Politika belirli partnerleri sistematik olarak dışlıyor (Faz 6'nın
dışlama sondası) ve bu, süpürgeyi hızlandırıyor.

## 9. Sonuç

| soru | cevap |
|---|---|
| Taze başlangıç çeşitliliği korur mu | ❌ **hayır** — ilk 500 adımda süpürge, 12000'de etkin soy 1.0–1.3 |
| Göçmen (genetik) mekaniği kurtarır mı | ❌ **hayır** — doğumların %10'u bile yetmiyor (etkin soy ≤1.71), bedeli −24% toplama |
| Çöküşün nedeni zincirleme mi | ❌ **hayır** — 2×2: tohum popülasyonu belirliyor, mekanik değil |
| Akrabalık negatifi artefakt mı | ❌ **hayır** — Faz 4.5/4.6 zaten ölçütü geçen zeminde ölçülmüş (4/5, dış-grup %40–58) |
| Karşılıklılık negatifi artefakt mı | ❌ **hayır** — geçerli zeminde tekrarlandı: 1/5 (eski 0/5), yön hâlâ tutarsız |
| Partner seçimi negatifi artefakt mı | ❌ verdict aynı (banttan çıkma 1/5), ama **ölçüm artık okunuyor** |

**Üç negatif de ayakta.** Faz 7'nin kazancı sonucu değiştirmek değil, sonucun
**neye dayandığını** ölçmek oldu: iki negatif zaten geçerli zemindeydi, üçüncüsü
geçerli zeminde tekrarlandı, ve gelecekteki her koşum için bir ölçüt + araç
(`tools/diversity_report.py`) var.

### Ne öğrendik (mekanizma)

Bu tasarımda **soy çeşitliliği ile genetik çeşitlilik birbirini iter.** Seçilim
üzerinde çalışacak varyans ne kadar çoksa süpürge o kadar hızlı; süpürge ne
kadar hızlıysa etkin soy o kadar az. Faz 4.5'te seçilim zincirini **onarmamız**
(yemek → yavru bağı +0.047 → +0.738), Faz 5 ve 6'nın zeminindeki soy çöküşünün
muhtemel nedeni. İyi bir düzeltme, başka bir yerde ölçümü bozmuş.

### Sınırlar — ne DEMİYORUZ

- **"Göçmen işe yaramaz" demiyoruz.** Altı orandan hiçbiri ölçütü geçmedi ama
  hepsi tek seed (42). Etkisi seed'e göre oynayabilir.
- **Çeşitliliği koruyan başka kaldıraçlar denenmedi**: daha geniş dünya / daha
  çok yama (CLAUDE.md'de ~13 etkin soy verdiği yazılı), uzamsal sığınaklar,
  yoğunluğa bağlı seçilim. Faz 7 yalnızca göçmeni denedi.
- **Faz 4.6'nın bütün koşulları denetlenmedi**: kontrollü evrim testinin ana
  koşulu (BC6) ölçütü geçiyor, ama `BC10` kolu geçmiyor (dış-grup %3.0).
  O koldan okunan hiçbir oran güvenilir değil.
