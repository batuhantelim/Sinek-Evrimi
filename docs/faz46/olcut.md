# Faz 4.6 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya Faz 4.6 koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Soru

Korunum yasasını **ihlal etmeden** (`need_mode: fitness`, `energy_created ≈ 0`),
akraba fedakârlığının evrimleşmesi için gereken `r·b > c` sağlanabilir mi?

Faz 4.5: Faz 3'ün pozitif sonucu, paylaşımın enerji ürettiği bir dünyanın
artefaktıydı. Temiz zeminde fedakârlık 0/5 seed'de evrimleşti.

## Hamilton'un r'si ETİKETTEN değil GENOMDAN okunur

`kin_assortment` soyisim eşitliğini ölçer — genetik özdeşliği değil. Aynı
soyisim mutasyonla ayrışır; `split_rate` ile ayrılan iki soy ayrılma anında
genetik olarak **aynıdır**. Bu yüzden yeni bir metrik eklendi:

```
genetic_r = Σ_k Cov(x_k^aktör, x_k^en yakın komşu) / Σ_k Var(x_k^aktör)
```

k genom **ağırlık** boyutları üzerinde gezer. Rastgele eşleşmede 0, klonlarda 1
(birim testiyle doğrulandı). Hamilton eşitsizliğinin `r` kolu budur.

## Kaldıraçlar (ayrı eksenler)

| eksen | anahtar | niyet |
|---|---|---|
| **R** | `agents.motors.max_speed` + `agents.reproduction.spawn_radius` ↓ | akrabaları uzamsal olarak sıkılaştır → `genetic_r` ↑ |
| **B/C** | `rules.share.overhead` ↓ | verenin işlem maliyeti ↓ → `b/c` ↑ (aktarım korunumlu kalır) |

Her seviyede **kaldıracın gerçekten ne yaptığı ölçülür**: `genetic_r`,
`kin_assortment`, `lineage_effective`, dış-grup fırsat payı, kişi başı toplama,
popülasyon, yemek doluluğu.

## GEÇERLİLİK ŞARTI (artefakta geri düşmeyi önler)

Her koşumda `energy_created` toplamı, aktarılan toplam enerjinin
**milyonda birinden küçük** olmalı. Değilse **koşum geçersizdir**: raporlanır
ve atılır. (`tests/test_phase3.py::test_sharing_conserves_energy_by_default`
bunu ayrıca zorluyor.)

## "Fedakârlık evrimleşti" sayılma ölçütü

Bir koşul, en az 3 seed'de:

1. Korunum şartı sağlanmış (yukarıdaki).
2. Tükenme yok.
3. **Ölçülebilir**: son çeyrekte dış-grup fırsat payı ≥ %10 **ve** işbirliği
   oranı ≥ %1 (ölçülecek bir şey olmalı).
4. **Ayrışma**: `kin_bias_adj` kendi soyisim-karıştırma kontrolünden
   Welch t > 2 ile ve doğru yönde ayrışıyor — seed'lerin **en az 2/3'ünde**.
   (Faz 3'ün `share_separates` ölçütüyle aynı.)

## Her koşulda ayrıca raporlanacak

Gerçekleşen **`r·b/c`** = `genetic_r` × `bc_ratio`. Teori, fedakârlığın
çıktığı yerde bunun **> 1** olmasını gerektirir. Bu sefer ölçüm anlamlıdır:
enerji korunumlu (Faz 4.5) ve popülasyon tavanı bağlayıcı değil.

## Negatif de sonuçtur

Hiçbir dürüst bölgede fedakârlık çıkmazsa, sonuç şudur: *bu minimal korunumlu
sistemde `r·b > c` ulaşılamıyor.* Hangi kolun (r mi, b/c mi) tavana çarptığı
sayılarla gösterilir.
