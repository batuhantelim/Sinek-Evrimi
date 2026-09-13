# Faz 5 — karşılıklılık: işbirliğinin ikinci mekanizması

Faz 4.6 **birinci** mekanizmayı (akrabalık / Hamilton) eledi: korunumlu zeminde
`r·b/c` 1'i geçemiyor, 15/15 koşul. Bu faz **ikinci** mekanizmayı test eder:
karşılıklılık. Matematiği farklı (tekrarlı oyunlar, Axelrod), dolayısıyla
sonuç da farklı olabilirdi.

Ölçüt koşumlardan önce yazıldı: [olcut.md](olcut.md).

---

## 0. Üç önkoşul — önce garanti, sonra ölçüm

Bunlar sağlanmadan "karşılıklılık reddedildi" denemez; doğru cümle
"koşul yoktu" olur.

### Önkoşul 1: tekrarlı karşılaşma — ÖLÇÜLDÜ, mevcut ekolojide var

⚠ **Kritik ayrım:** bir sinek 100 adım aynı komşunun yanında durursa bu **tek**
bir karşılaşmadır. Axelrod'un tekrarlı oyunu araya başka partnerlerin girdiği
**ayrı buluşmalar** ister. Sonda ikisini ayırıyor:

| koşul | ajan/partner | **epizot-tekrarı** | adım-tekrarı (şişirilmiş) | **≥3 ayrı buluşma** | dönüş aralığı (medyan) |
|---|---|---|---|---|---|
| **taban** | 11.0 | %29.1 | %95.0 | **%50.6** | 16 adım |
| sıkışık mekân | 4.6 | %30.6 | %98.5 | %28.4 | 17 |
| geniş menzil | 12.6 | %31.2 | %95.7 | %54.3 | 16 |
| uzun ömür | 11.2 | %28.4 | %94.9 | %45.4 | 16 |

Ölçüt %30 istiyordu; taban ekolojide **%50.6**. Zemin var, ekolojiyi
değiştirmeye gerek kalmadı.

Yan bulgu: mekânı sıkıştırmak zemini **düşürüyor** (%28.4). Sıkışık dünyada
sinekler aynı komşunun yanında uzun süre duruyor (adım-tekrarı %98.5) ama
*ayrı* buluşma sayısı azalıyor. Adım-tekrarına bakılsaydı tam ters okunurdu.

### Önkoşul 2: tanıma — eklendi

Ajanların kalıcı bireysel kimliği zaten vardı; sensöre iki kanal eklendi
(sözleşmenin **sonuna**, 19 → 21):

- `partner_known` — bu **bireyle** daha önce etkileşim oldu mu (0/1)
- `partner_ledger` — onunla geçmişin net işareti (−1…+1)

### Önkoşul 3: hafıza — zaten vardı, ayrıca dışsallaştırıldı

RNN'in iç durumu adımlar arası **korunuyordu** (`reset()` yalnızca sondada
çağrılıyor). Ama sızıntı 0.5 olduğu için etkin ufuk ~2 adım — onlarca adım
sonra dönen bir partneri taşıyamaz. Bu yüzden **dışsal defter** eklendi:

`Agent.ledger`: partner kimliği → geçmişin net işareti. **Alıcı** kaydeder:
birinden enerji aldıysa `+`, biri saldırdıysa `−`. Kapasite sınırlı (16),
tahliye deterministik (en zayıf kayıt).

**"Karşılık ver" diye bir kural YOK.** `tests/test_phase5.py::test_memory_is_information_not_rule`
kaynakta defter bayraklarının (`owes`/`grudge`) yalnızca **ölçüm sayaçlarına**
gittiğini, hiçbir karar dalına girmediğini denetler.

---

## 1. ⚠ İlk kontrolüm kusurluydu — örneklemi yok ediyordu

İlk tasarımda kontrol `shuffle_identity` idi: tanıma kimlikleri her adım
karıştırılıyor, defter yanlış bireyi gösteriyordu. Ölçüldüğünde:

| kol | defteri pozitif fırsat | pay |
|---|---|---|
| hafızalı | 17 751 | %10.8 |
| `shuffle_identity` | **417** | **%0.28** |

Kimlikleri karıştırmak, defterde kayıtlı birine **rastlama olasılığını** da
yok ediyor — örneklem 43× küçülüyor. O zaman "bilgi gittiği için mi, örnek
kalmadığı için mi" ayırt edilemez. Bu, Faz 3'te `random_surname_at_birth`'ün
ilk sürümünde yapılan hatanın aynısı.

**Asıl kontrol** `shuffle_ledger`: her ajanın defterindeki **değerler kendi
partnerleri arasında** karıştırılır. Aynı sayıda partner tanınır, aynı değerler
durur; yalnızca *hangi partnerin hangi değere sahip olduğu* bilgisizleşir.
`partner_known` değişmez, yalnızca `partner_ledger` anlamsızlaşır. Örneklem
korunuyor: defteri pozitif fırsat payı %6.4–10.5 (hafızalı kolda %4.3–10.8).

---

## 2. Sonuç: karşılıklılık evrimleşmedi (0/5)

5 seed, her biri kendi **eşleşmiş** kontrolüyle. Değerler yüzde puan.

| seed | hafızalı: işbirliği / defter+ / **karşılıklılık** / misilleme | kontrol: aynı sıra | `t` karşılıklılık | `t` misilleme |
|---|---|---|---|---|
| 1 | %1.19 / %9.0 / **+0.28** / +7.95 | %0.89 / %6.4 / +0.98 / +4.27 | **−2.68** | +8.04 |
| 7 | %0.61 / %4.3 / **+1.93** / +4.29 | %2.18 / %10.5 / +1.80 / +4.82 | +0.94 | −1.08 |
| 42 | %1.28 / %10.8 / **−0.03** / +4.75 | %1.96 / %10.5 / −0.00 / +6.18 | −0.09 | −2.24 |
| 123 | %0.88 / %7.5 / **−0.00** / +6.77 | %1.08 / %7.5 / +0.14 / +6.69 | −0.46 | +0.07 |
| 777 | %1.21 / %9.1 / **+1.94** / +7.97 | %0.80 / %5.4 / +3.19 / +6.87 | −2.43 | +1.46 |

- **Karşılıklılık: 0/5 seed ayrıştı.** `t` = −0.94 ± 1.56 (en iyisi +0.94).
  İki seed'de kontrol asıl koldan **daha yüksek**.
- **Misilleme: 1/5.** Ölçüt ≥2/3 (yani ≥4/5) istiyordu. `t` = +1.25 ± 4.04.
- **Enerji korunumu 10/10 koşumda tam** (yaratılan enerji = 0).

### Misilleme görüntüsü tamamen konfound

Hafızalı kolda `retal_bias_adj` +4.3…+8.0 puan — yani "bana saldırana
saldırıyorum" gibi görünüyor. Ama kontrolde de **+4.3…+6.9**. Defter
karıştırıldığında, yani "kime kızgın olduğum" bilgisi yok edildiğinde aynı
rakam çıkıyor. Sıfıra karşı okunsaydı burada **yanlış bir pozitif** rapor
edilecekti — `kin_bias` dersinin bir kez daha tekrarı.

---

## 3. Kanal okunuyor mu? Tutarlı biçimde hayır

Nedensel sonda (`tools/kin_probe.py --channel partner_ledger`) ajanları hiç
çalıştırmaz: aynı sensör vektörünü beyne iki kez verir, **yalnızca** defterin
işaretini çevirir.

| seed | hafızalı (PAYLAŞ farkı / kayıran) | kontrol |
|---|---|---|
| 1 | **+0.1001** / %88.4 | +0.0818 / %82.4 |
| 7 | **−0.0172** / %33.3 | +0.0259 / %63.4 |
| 42 | **+0.0830** / %76.2 | +0.0326 / %66.2 |
| 123 | **−0.0321** / %36.2 | −0.0157 / %43.8 |
| 777 | **+0.0554** / %71.4 | +0.0261 / %64.6 |

Ortalama: hafızalı **+0.0378** (3/5 pozitif), kontrol **+0.0301** (4/5).
İşaret seed'den seed'e dönüyor ve kontrol aynı büyüklükte. **Beyin defter
kanalını kontrolden farklı bir şekilde okumuyor.**

⚠ Yalnızca seed 42'ye bakılsaydı (+0.083 vs +0.033, %76 vs %66) "kanal
okunuyor" denecekti. Beş seed bunu çürüttü — "tek seed sonuç değildir"in
bir örneği daha.

---

## 4. İşbirliği seviyesi de değişmedi

Hafızalı kol vs hafızasız kontrol, işbirliği oranı: `t` = +3.65 / −1.76 / +3.33
(3 seed). İşaret tutarsız ve büyüklükler küçük (%1.28 vs %1.14). Hafıza kanalı
işbirliğinin **seviyesini** de yükseltmiyor.

---

## 5. Sonuç

Üç önkoşul da **ölçülerek** sağlandı — tekrarlı karşılaşma (%50.6 ajan, ≥3 ayrı
buluşma), tanıma (iki sensör, testli), hafıza (RNN iç durumu + dışsal defter).
Buna rağmen:

> **Bu minimal dünyada karşılıklılık evrimleşmiyor.** Ne pozitif karşılıklılık
> (0/5), ne misilleme (1/5), ne de genel işbirliği seviyesinde bir artış.

Faz 4.6 ile birlikte: işbirliğinin **iki** büyük mekanizması da — akrabalık ve
karşılıklılık — bu kurulumda çalışmıyor. Birincisi **yapısal** bir nedenle
(`b/c ≤ 1` korunumlu aktarımda, `r` ekolojik tavana çarpıyor); ikincisi için
yapısal bir engel gösteremiyoruz: önkoşullar sağlandı, kanal açık, yine de
seçilim onu kullanmadı.

### Olası açıklama (hipotez, ölçülmedi)

Paylaşımın taban oranı %1 civarında. Karşılıklılığın evrimleşmesi için önce
**paylaşımın kendisinin** yeterince sık olması gerekir ki "bana veren" diye bir
sınıf oluşsun ve ona karşılık vermek seçilebilir bir fark yaratsın. Faz 4.6
paylaşımın neden bu kadar nadir olduğunu gösterdi (`r·b/c < 1`). Yani iki
negatif bağımsız değil olabilir: **karşılıklılık, üzerine kurulacağı işbirliği
olmadığı için başlayamıyor.** Bunu sınamak, paylaşımı dışarıdan yükseltip
(ödüllendirmeden) karşılıklılığın o zaman çıkıp çıkmadığına bakmayı gerektirir.

---

## 6. Sınırlar — ne DEMİYORUZ

- **"Karşılıklılık imkânsız" demiyoruz.** Tek rejim, 5 seed, tek hafıza tasarımı
  (net işaretli defter, kapasite 16, unutma yok). Ayrı "verdi" ve "saldırdı"
  kanalları, itibar (üçüncü tarafın gözlemi), ya da partner **seçimi** (kime
  yaklaşacağını seçmek) denenmedi.
- **Hafıza ufku sınanmadı.** `rnn_leak = 0.5` iç belleği ~2 adımla sınırlıyor;
  defter bu yüzden dışsal. Sızıntıyı genoma bağlamak (evrimleşebilir bellek
  ufku) denenmedi.
- **Partner hedefi sabit.** Ajan her zaman **en yakın** komşuyla etkileşir;
  "kiminle oynayacağını seçme" yok. Axelrod'un turnuvasında eşleşme dışsaldır,
  ama gerçek karşılıklılıkta ortak seçimi güçlü bir kaldıraçtır.
- Önkoşul 1 tek seed'de (42) ölçüldü; dört farklı koşulda tutarlı çıktı ama
  çok seed'de tekrarlanmadı.
