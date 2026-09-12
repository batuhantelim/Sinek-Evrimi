# Evrimleşen Sinek Kolonisi 🪰

Ajan tabanlı yapay yaşam (ALife) simülasyonu. Basit sinekler, yenilenen kaynaklar,
tehlikeler — ve **kodlanmamış**, kendiliğinden ortaya çıkan davranış.

> Ayrıntılı mimari ve geliştirme notları: **[CLAUDE.md](CLAUDE.md)**

## Kurulum

```bash
pip install -r requirements.txt     # numpy + PyYAML
pip install pygame                  # opsiyonel: canlı pencere
```

## Çalıştırma

```bash
python run.py                       # config.yaml (Faz 3) ile koş, PNG kare kaydet
python run.py --viz pygame          # canlı pencere (SPACE duraklat, Q çık)
python run.py --steps 1000 --viz none
python run.py --check-determinism
python -m unittest discover -s tests
python tools/plot_metrics.py runs/faz3 --generations
python tools/kin_probe.py runs/faz3/population.npz
```

Çıktılar `runs/<name>/`: `metrics.csv`, `summary.txt`, `frames/*.png`,
`config_used.yaml`.

## Kod değiştirmeden deney

```bash
python run.py --config experiments/faz1_klonlar.yaml            # Faz 1 taban çizgisi
python run.py --config experiments/faz2_kontrol_secilimsiz.yaml # seçilimsiz kontrol
python run.py --set evolution.fitness.distance=2.0 --name gezgin
python run.py --set brain.hidden=24 --name buyuk_beyin
```

Hazır deneyler: [experiments/README.md](experiments/README.md)

## Durum

| Faz | İçerik | Durum |
|---|---|---|
| 1 | Klon ajan + ortam + hareket + yemek + üreme/ölüm | ✅ |
| 2 | Mutasyon + seçilim + evrimleşebilir recurrent sinir ağı | ✅ |
| 3 — adım 1 | Soyisim + akrabalık sensörü + paylaşma + kontrol grupları | ✅ |
| 3 — adım 2 | `attack` + dört hücreli in/out analizi | ✅ |
| 4 | Doğal avcı, melez soyisim, soy-arası ilişki matrisi | ⏳ |

Sonuçlar: [docs/faz1/](docs/faz1/) · [docs/faz2/](docs/faz2/) · [docs/faz3/](docs/faz3/)
