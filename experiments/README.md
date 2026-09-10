# Hazir deney konfigurasyonlari

Her dosya `config.yaml` uzerine bindirilir; sadece degistirdigi anahtarlari
icerir. Calistirmak icin:

```bash
python run.py --config experiments/<dosya>.yaml
```

| Dosya | Soru |
|---|---|
| `faz1_klonlar.yaml` | Taban cizgisi: klon refleks ajanlar, mutasyon yok |
| `faz2_kontrol_secilimsiz.yaml` | **Kontrol:** secilim kapali, sadece suruklenme. Asil kosum bunu asmali |
| `faz2_surekli.yaml` | Nesil sinirsiz, surekli/aseksuel evrim (Faz 1 ekolojisi + mutasyon) |
| `faz2_kitlik.yaml` | Kit dunyada farkli bir davranis mi evrimlesiyor? |

Tek seferlik degisiklikler icin dosya acmaya gerek yok:

```bash
python run.py --set evolution.fitness.food_eaten=0.0 --set evolution.fitness.age=5.0 --name uzun_yasa
```
