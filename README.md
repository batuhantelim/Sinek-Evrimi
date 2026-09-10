# Evrimleşen Sinek Kolonisi 🪰

Ajan tabanlı yapay yaşam (ALife) simülasyonu. Basit sinekler, yenilenen kaynaklar,
tehlikeler — ve **kodlanmamış**, kendiliğinden ortaya çıkan davranış.

> Ayrıntılı mimari ve geliştirme notları: **[CLAUDE.md](CLAUDE.md)**
> Faz 1 sonuçları ve görseller: **[docs/faz1/](docs/faz1/)**

## Kurulum

```bash
pip install -r requirements.txt     # numpy + PyYAML
pip install pygame                  # opsiyonel: canlı pencere
```

## Çalıştırma

```bash
python run.py                       # config.yaml ile koş, PNG kare kaydet
python run.py --viz pygame          # canlı pencere (SPACE duraklat, Q çık)
python run.py --steps 1000 --viz none
python run.py --check-determinism
python -m unittest discover -s tests
python tools/plot_metrics.py runs/faz1
```

Çıktılar `runs/<name>/`: `metrics.csv`, `summary.txt`, `frames/*.png`,
`config_used.yaml`.

## Kod değiştirmeden deney

```bash
python run.py --set world.food.regrowth_rate=0.003 --name kitlik
python run.py --set genome.params.crowd_bias=1.2   --name suru
python run.py --config deneylerim/kendi_dunyam.yaml
```

## Durum

| Faz | İçerik | Durum |
|---|---|---|
| 1 | Klon ajan + ortam + hareket + yemek + üreme/ölüm | ✅ |
| 2 | Mutasyon + seçilim + evrimleşebilir sinir ağı | ⏳ |
| 3 | Sosyal kurallar: paylaşma / saldırma | ⏳ |
