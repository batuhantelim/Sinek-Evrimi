# Faz 4.5 Bölüm 1 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya Bölüm 1 koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Düzeltme: tanıdaki "yemek 16.7× kısıldı" ifadesi yanlıştı

Yenilenme iki terimden gelir:

```
logistic:  food += regrowth_rate · food · (1 − food/cap)
           food += seed_rate · cap          ← taban, her adım, koşulsuz
```

Tanı sondasında yalnızca `regrowth_rate` 0.010 → 0.0006 yapılmıştı;
`seed_rate = 0.0006` yerinde kaldığı için **gerçek girdi 62.1 → 15.0
birim/adım**, yani 16.7× değil **4.1×** düştü. Ve 15.0 birim/adım ≈ 330
enerji/adım hâlâ ~517 sineği (çıplak metabolizmayla) besliyor — o yüzden
koloni 700'de kaldı. Bulgunun yönü doğruydu (tavan bağlayıcı), büyüklüğü
yanlıştı. Bu fazda yemek arzı **iki terim birlikte** ölçeklenecek.

Ölçülen değerler (kapasite toplamı 20046 birim, %50 doluluk):

| `regrowth_rate` | `seed_rate` | girdi (birim/adım) | ≈ enerji/adım | çıplak metabolizmayla kaç sinek |
|---|---|---|---|---|
| 0.010 (varsayılan) | 0.0006 | 62.1 | 1367 | ~2136 |
| 0.0006 | 0.0006 | 15.0 | 331 | ~517 |
| 0.0006 | 0 | 3.0 | 66 | ~103 |

Varsayılan dünya, `max_count = 700`'ün **~3 katını** besliyor. Tavanın
bağlayıcı olmasının sebebi bu.

## Kaldıraç

Tek bir **yemek arzı ölçeği** `s`: `regrowth_rate = 0.010·s` **ve**
`seed_rate = 0.0006·s`. Ayrıca `agents.max_count = 5000` (bağlayıcı olmasın).
Başka hiçbir şey değişmez.

## "Çevresel olarak sınırlı" sayılma ölçütü

12000 adım, en az 3 seed:

1. **`at_cap` payı ≤ %5** (eski kurulumda %99.4).
2. **Adım başına `repro_blocked` ≤ 5** (eski kurulumda ~456 — yani koloninin
   ~%65'i her adım üreme eşiğinin üstünde ama tavan yüzünden bölünemiyor).
3. Tükenme yok; son yarı ortalama popülasyon **≥ 150**.
4. Son yarı ortalama popülasyon **≤ 1500** (koşum süresi ve dünyanın
   karşılaştırılabilir kalması için).
5. Popülasyon gerçekten dinamik: son yarı **varyasyon katsayısı ≥ %2** —
   yani başka bir sabite yapışmış olmasın.

Geçenler arasından, eski yoğunluğa (N≈700) **en yakın** denge popülasyonu
veren seviye seçilir; Bölüm 3'ün yeniden-doğrulaması ancak böyle
yoğunluk-karşılaştırılabilir olur.

## Her koşulda ayrıca ölçülecek

`kin_assortment`, `lineage_effective`, kişi başı toplama (`forage_per_capita`),
açlık/yaşlılık ölüm payları, dış-grup fırsat payı.
