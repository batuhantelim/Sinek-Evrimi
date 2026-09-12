# Bölüm B ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Faz 4 adım 1 dersi: "ölçütü sonucu görmeden ilan edin". Bu dosya B koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Aranan şey

Faz 4'ün geri kalanının üstüne kurulacağı **tek kararlı, ölçülebilir** bir taban
rejim. Bölüm A'nın gösterdiği sorun "iki eşit havza" değil, **işbirliğinin
tavana dayanması**: 12 seed'in medyanı %60.6, üçü %85'in üstünde. In ve dış
hücreler birlikte doyunca ayrımcılık ölçülemez hale geliyor.

## Bir rejimin "kullanılabilir taban" sayılması için (5 seed üzerinde)

1. Hiçbir seed'de tükenme yok, popülasyon kararlı.
2. Son çeyrek işbirliği oranının **medyanı [0.05, 0.50] aralığında**.
   Üst sınır tavan etkisini, alt sınır "ölçecek paylaşım kalmadı"yı engeller.
3. Seed'ler arası yayılım **max − min işbirliği ≤ 0.40**: koşumlar ayrı
   rejimlere bölünmüyor.
4. Son çeyrek **dış-grup fırsat payı ≥ %10** (Faz 4 adım 1'den devralınan
   ölçülebilirlik şartı).
5. Kişi başı toplama hızı taban rejimin **%70'inin altına düşmemiş** —
   koloni açlıktan değil, tercih ederek paylaşıyor olmalı.

Birden fazla rejim geçerse: işbirliği medyanı bandın ortasına en yakın **ve**
seed'ler arası yayılımı en küçük olan seçilir.

## Süpürülecek kaldıraçlar (ayrı ayrı — hangisinin sürdüğü ayırt edilebilsin)

| kol | anahtar | seviyeler | ne yapması bekleniyor |
|---|---|---|---|
| B1 | `rules.share.overhead` | 1.2 (taban) / 3.0 / 6.0 | verenin ölü yükü ↑ → paylaşım cazibesi ↓ |
| B2 | `rules.share.need_bonus` | 3.0 (taban) / 1.0 / 0.0 | alıcının dönüşüm verimi ↓ → `b/c` ↓ |

Seed'ler: 1, 7, 42, 123, 777 (Bölüm A'da 42 en seyrek, 777 en yoğun uçtaydı).
Avcı kapalı, başka hiçbir şey değişmiyor.

## Her koşulda ayrıca ÖLÇÜLECEK yan etkiler

`kin_assortment`, `lineage_effective`, dış-grup payı, kişi başı toplama,
açlıktan ölüm payı. ("Kaldıracınızın ne yaptığını ÖLÇÜN" kuralı.)
