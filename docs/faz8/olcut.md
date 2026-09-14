# Faz 8 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya Faz 8 koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Soru

Faz 7 ölçtü: bu tasarımda güçlü yönlü seçilim soy çeşitliliğini **siliyor**
(seçilim süpürgesi; taze zeminde en büyük soy ilk 500 adımda %32'ye, 12000'de
%99'a çıkıyor) ve göçmen enjeksiyonu bunu **çözmedi** (0/6 koşul, doğumların
%10'u taze kurucu olsa bile etkin soy 1.71).

Sosyal mekanikler (melez soylar, soy-arası ilişkiler, grup seçilimi) çeşitlilik
**olmadan ölçülemez**. Bu faz sosyal bir mekanik aramıyor; **ekolojik/uzamsal**
bir çeşitlilik koruması arıyor.

**Hipotez:** süpürge tek ve homojen bir dünyada olur, çünkü en iyi soy her yere
yayılabilir. Dünya parçalanırsa (soylar coğrafi olarak ayrılabilirse) farklı
bölgelerde farklı soylar tutunur. Biyolojideki allopatrik çeşitlilik
korumasının analoğu.

## Üç kaldıraç (ayrı eksenler, önce tek tek)

| # | kaldıraç | mekanizma | ölçülecek |
|---|---|---|---|
| 1 | **geniş dünya** | harita büyür, ajan yoğunluğu düşer | soy çeşitliliği dünya boyutuyla ölçekleniyor mu |
| 2 | **uzamsal sığınaklar** | ayrık kaynak bölgeleri / geçilmesi zor koridorlar | farklı bölgelerde farklı soylar mı baskın (coğrafi ayrışma) |
| 3 | **yoğunluğa bağlı seçilim** | yerel olarak kalabalıklaşan soy dezavantaj görür (negatif frekans bağımlılığı: nadir olan avantajlı) | baskın soy büyüdükçe uygunluğu düşüyor mu |

Sıra: önce **3** (teorik olarak en güçlüsü), 2–3 seed. Sonra 1, 2 ve umut veren
kombinasyonlar.

## BAŞARI ÖLÇÜTÜ

Bir kaldıraç "çeşitliliği korudu" sayılır ancak **dördü birden** son çeyrekte
sağlanırsa:

1. **etkin soy ≥ 5.0**
2. **dış-grup fırsat payı ≥ %10**
3. **süpürge yok: en büyük soy < %80**
4. **koloni sağlıklı**: tükenme yok, popülasyon kontrolün ≥ %50'si **ve** kişi
   başı toplama (`forage_per_capita`) kontrolün ≥ %70'i.

En az **2/3 seed** (umut verirse 5). Ölçüt 4 olmadan ilk üçü anlamsızdır:
**çeşitliliği koloniyi çökerterek "korumak" geçersizdir** (Faz 3/4 dersi —
`r·b/c` 0.989'a çıkan koşul koloniyi ölçülemez hale getirmişti).

## ⚠ Bu kaldıracın kendine özgü tuzağı: DÖNGÜSELLİK

Kaldıraç 3 doğrudan **soyisim etiketine** bakarak ceza verir. Etiket
çeşitliliğinin yükselmesi kısmen **tanım gereğidir**. Bu yüzden "çeşitlilik
korundu" demek için ölçüt 1–4 yetmez; ayrıca:

- **`weight_diversity` düşmemeli** — etiket çeşitliliği genom çeşitliliği
  demek değildir (Faz 7 §3.12 kuralı).
- **`genetic_r` kontrolün yarısının altına inmemeli.** Kaldıraç akraba
  kümelenmesini cezalandırdığı için akrabalık yapısını **yok edebilir**;
  o zaman in/out ölçülebilir hale gelir ama ölçülecek akrabalık kalmaz.
  Bu, kaldıracı geçersiz kılar.

## Kontroller (ŞART)

| kol | ne yapar | beklenen |
|---|---|---|
| **taban** | kaldıraç kapalı, Faz 7 zemini | süpürge olur, etkin soy ~1 |
| **kaldıraç** | `rules.crowding.enabled: true` | ölçüt 1–4 |
| **karıştırma kontrolü** | ceza **karıştırılmış** etiketlerden hesaplanır: aynı büyüklükte enerji gideri, sıfır bilgi | çeşitliliği KORUMAMALI |

Karıştırma kontrolü kritik: kaldıraç yalnızca fazladan bir enerji gideri
eklediği için mi işe yarıyor, yoksa **etiket bilgisi** üzerinden mi? Kontrol de
aynı çeşitliliği veriyorsa mekanizma frekans bağımlılığı değil, sadece
seçilim baskısının zayıflatılmasıdır ve öyle raporlanır.

## Ayrıca raporlanacak yan etkiler

`kin_assortment`, `genetic_r`, `weight_diversity`, `cooperation_rate`,
`hostility_rate`, `population`, `forage_per_capita`, ve **yeni enerji gideri**
(`crowding_drain`) ayrı bir sütun olarak. Paylaşımın korunumu
(`energy_created` = 0) bozulmamalı — kaldıraç bir **gider**tir, kaynak değil.

## Değişmeyen kurallar

Korunumlu enerji; rol/kast kodlanmaz; paylaşım/saldırı ödüllendirilmez;
in/out ayrı; determinizm; kişi başı birim; kontrole karşı okunur; kaldıracın
yan etkisi ölçülür.

Ek olarak bu kaldıraç için: **hiçbir soy adıyla hedeflenmez.** Ceza yalnızca
*yerel frekansa* bakar; bütün soyisimler tutarlı biçimde yeniden
adlandırıldığında ceza dağılımı **birebir aynı** kalmalıdır (test bunu zorlar).

## Karar kuralı (önceden yazıldı)

- **Bir kaldıraç (ya da kombinasyon) ölçütü geçerse:** melez soylar / soy-arası
  ilişkiler / grup seçilimi artık ölçülebilir bir zemine oturur; sonraki faz o
  olur.
- **Hiçbiri geçmezse:** bu tasarımda çeşitlilik ile güçlü seçilim **yapısal
  olarak uzlaşmaz.** Bu da bir bulgudur ve "zengin, çok soylu teraryum"
  vizyonunun temelden yeniden düşünülmesi gerektiğini söyler.
