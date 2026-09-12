# Faz 4 — adım 1: doğal avcı

Ortak, dışsal ve **gruptan bağımsız** bir tehdit. Faz 3'ün üç negatifi bu
adımın taban çizgisidir; melez soyisim ve soy-arası ilişki matrisi henüz yok
(altyapı uyumlu ama kapalı).

**Tam rapor: [adim1_avci.md](adim1_avci.md)**

## Kısa cevap

| soru | cevap |
|---|---|
| Avcı dış-grup düşmanlığı üretiyor mu? | **Hayır** — `atk_t` avcılı −3.55, avcısız −5.52 (3 seed) |
| In-grup işbirliğini güçlendiriyor mu? | **Hayır** — paylaşımı patlatıyor ama **ayrım gözetmeyen** paylaşıma çeviriyor (`share_t` +4.46 vs +7.35) |
| Fedakârlık ve düşmanlık birlikte mi geliyor? | **Hayır** — dönemler arası r: avcılı −0.24, avcısız +0.01 |

Ayrıca: koloni **iki kararlı rejim** arasında salınıyor ("seyrek toplayıcı" /
"yoğun paylaşım yumağı") ve koşumlar arası büyüklük farkının çoğunu avcı değil
bu havza seçimi açıklıyor.

## Dosyalar

| dosya | içerik |
|---|---|
| `adim1_avci.md` | tam rapor: 2×2 tasarım, kalibrasyon, üç soru, sınırlar |
| `adim1_karsilastirma.png` | dönem eğrileri: avcı / avcısız / avcı-kontrol |
| `kare_avci.png` | 3000. adım: soya göre renklenmiş sinekler + avcılar (küçük parlak kırmızı; büyük koyu bordo diskler sabit tehlike) |
| `seed_taramasi.txt` / `.jsonl` | 3 seed × 4 koşumun ham özeti |
| `kin_sonda.txt` | nedensel sonda: yalnızca akrabalık kanalı çevrilince motor farkı |
| `ozet_*.txt`, `generations_*.csv` | seed 42'nin dört kolunun çıktıları |
| `ozet_p20_kontrol_TUKENDI.txt` | 20 avcılı ilk partide tükenen kontrol (kalibrasyon dersi) |
| `population.npz` | seed 42 avcılı kolun son popülasyonu |

## Yeniden üretmek

```bash
for k in avci avci_kontrol avcisiz avcisiz_kontrol; do
  python run.py --config experiments/faz4_$k.yaml \
    --load-genomes docs/faz2/population.npz --seed 42 --viz none
done
python tools/predator_sweep.py --from-runs \
  runs/faz4_avci runs/faz4_avci_kontrol runs/faz4_avcisiz runs/faz4_avcisiz_kontrol \
  --seed-label 42
```

Çok seed (tek komut, ama seri koşar — yukarıdaki döngü paralelleşebilir):

```bash
python tools/predator_sweep.py --seeds 42 7 123 --out runs/faz4/seed_taramasi.jsonl
python tools/predator_sweep.py --summary runs/faz4/seed_taramasi.jsonl
```
