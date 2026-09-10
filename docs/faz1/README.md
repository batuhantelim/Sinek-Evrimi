# Faz 1 sonuçları (seed 42, 3000 adım)

Bu klasör Faz 1 koşumunun özet çıktılarını taşır. Ham veri (`metrics.csv`,
150 kare) `runs/` altında üretilir ve depoya konmaz — yeniden üretmek için:

```bash
python run.py --name faz1 --viz frames
python run.py --name kontrol_kor --viz none \
  --set genome.params.food_attraction=0.0 --set genome.params.hunger_gain=0.0 \
  --set genome.params.graze_slowdown=0.0  --set genome.params.hunger_speed=0.0
python tools/plot_metrics.py runs/faz1 runs/kontrol_kor \
  --cols population,mean_energy,food_fill,clustering --out runs/karsilastirma.png
```

| Dosya | İçerik |
|---|---|
| `karsilastirma.png` | Koklayan koloni (turuncu) vs tam kör kontrol (yeşil) |
| `metrikler.png` | Faz 1 koşumunun tüm metrik panelleri |
| `kare_adim0520.png` | Çöküş sonrası toparlanma, sinekler yamalarda |
| `kare_adim2820.png` | Denge durumu, dünya ağır otlanmış |
| `ozet_faz1.txt`, `ozet_kontrol_kor.txt` | Terminal özetleri |

## Sayılarla

| | Faz 1 (koklayan) | Kontrol (tam kör) |
|---|---|---|
| Son popülasyon | 350 | 352 |
| Açlıktan ölüm | 2052 | 2633 |
| Yaşlılıktan ölüm | 385 | 222 |
| Ortalama enerji (son yarı) | 69.0 | 63.3 |
| Kalan yemek stoğu | %14.1 | %26.0 |
| Kümelenme indeksi | 0.368 | 0.194 |

Taşıma kapasitesini kaynak üretimi belirlediği için iki koloni de benzer
popülasyona oturuyor; fark **nasıl** yaşadıklarında: koklayan sinekler stoğu
daha çok tüketiyor, daha az açlıktan ölüyor, daha çok yaşlanıyor ve kaynak
yamalarında belirgin şekilde kümeleniyor.
