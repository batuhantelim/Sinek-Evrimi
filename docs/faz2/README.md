# Faz 2 sonuçları — mutasyon + seçilim + evrimleşebilir sinir ağı

seed 42, 8000 adım = **32 nesil**, `brain.type: rnn` (12 nöron, 364 ağırlık),
`evolution.mode: generational`.

Ağırlıklar 0. nesilde **tamamen rastgele**. Kodda tek bir davranış katsayısı yok.

## 1. Evrim gerçekleşti mi?

| | 0. nesil | 31. nesil |
|---|---|---|
| Ortalama fitness | 356 | **815** (+129%) |
| Ajan başına yenen yemek | 16.3 | **61.6** (×3.8) |
| Nesli tamamlayan (120 üzerinden) | 63 | **118** |
| Ağırlık çeşitliliği | 0.598 | 0.304 |

## 2. Bu evrim mi, yoksa sürüklenme mi? (kontrol grubu)

`experiments/faz2_kontrol_secilimsiz.yaml` — tüm fitness ağırlıkları 0,
elitizm kapalı. Mutasyon ve nesil döngüsü aynen çalışıyor, **sadece seçilim yok**.

| 31. nesil | Seçilim açık | Seçilimsiz (sürüklenme) |
|---|---|---|
| Ajan başına yemek | **61.6** | 27.9 |
| Koşum boyunca toplam ölüm | **261** | 1598 |
| Kümelenme indeksi | **0.601** | 0.130 |
| Ağırlık çeşitliliği | 0.304 | 0.598 (yakınsama yok) |

Sürüklenen kolonide de yemek 16.3 → 27.9 çıkıyor. Bu **uyum değil**: mutasyon
ağırlıkların mutlak büyüklüğünü rastgele yürüyüşle artırıyor, büyük ağırlık
= doymuş `tanh` = daha kararlı (daha az titrek) hareket. Yani "biraz iyileşme"
seçilim olmadan da olur; asıl fark ×2.2'lik açıklıkta.

## 3. Ne öğrendiler? (evrimleşmiş vs acemi, aynı dünyada)

`tools/benchmark_genomes.py` — üreme ve seçilim kapalı, saf davranış ölçümü,
500 adım × 3 farklı dünya:

| Ölçüt | Evrimleşmiş | Acemi (rastgele ağ) | Oran |
|---|---|---|---|
| Hayatta kalan oranı | 0.931 | 0.461 | **×2.02** |
| Ajan başına yemek | 113.9 | 57.7 | **×1.98** |
| **Koku gradyanıyla hizalanma** | **0.424** | 0.013 | **×32.6** |
| Yemek üzerinde geçen zaman | 0.461 | 0.440 | ×1.05 |
| Tehlike içinde geçen zaman | 0.064 | 0.046 | ×1.40 |

**Kemotaksis evrimleşti.** Rastgele ağlarda gradyanla hizalanma sıfıra yakın
(0.013); 32 nesil sonra 0.424. Karşılaştırma için: Faz 1'in **elle yazılmış**
refleks devresi 0.66 hizalanma sağlıyordu. Evrim, kimse söylemeden, elle
tasarlanmış çözümün yaklaşık üçte ikisini kendi buldu.

**Yemek üzerinde geçen zaman neredeyse aynı (×1.05).** Kazanç "daha çok
oturmak"tan değil, **taze yemeği daha iyi bulmaktan** geliyor.

**Tehlikeden kaçınma evrimleşmedi — tersine kötüleşti (×1.40).** Dürüst
sonuç: `evolution.fitness` içinde tehlike terimi yok ve 32 nesilde tehlike
kaynaklı ölüm yalnızca 155. Ödüllendirilmeyen davranış evrimleşmiyor.
Risk/ödül gerilimi istiyorsanız `world.hazard.avoid_food_patches: false`
yapın — tehlike yemeğin üstüne oturur.

## 4. Genom kayması

`rnn` beyni isimli parametrelerden yalnızca `wander`'ı okur; geri kalan 9
parametre davranışa etki etmez ve **yerleşik bir nötr sürüklenme referansı**
oluşturur.

- İşlevsel: `wander` 0.322 → **0.469** — daha fazla keşif gürültüsü seçildi.
- Nötr: 9 parametre rastgele kaydı (en çok `panic_speed` +0.427). Bunları
  "evrimleşti" diye okumak hata olur; `summary.txt` ikisini ayrı raporlar.

## 5. Görseller

| Dosya | İçerik |
|---|---|
| `evrim_vs_suruklenme.png` | Seçilim açık (turuncu) vs seçilimsiz (yeşil), nesil bazlı |
| `nesil_egrileri.png` | Ana koşumun tüm nesil metrikleri |
| `kare_nesil00.png` | 0. nesil, adım 200: 120'den 67'si hayatta, yemeğe dokunulmamış, rastgele ağlar yerinde dönüyor |
| `kare_nesil31.png` | 31. nesil, adım 7800: 119 hayatta, uzun süpüren otlama izleri, hepsi yüksek enerjide |
| `generations.csv` | Nesil bazlı ham veri |

## 6. Yeniden üretmek

```bash
python run.py --name faz2 --viz frames --set viz.every=50
python run.py --config experiments/faz2_kontrol_secilimsiz.yaml --viz none
python tools/plot_metrics.py runs/faz2 runs/faz2_kontrol_secilimsiz --generations \
    --cols mean_fitness,mean_food_eaten,survivors,weight_diversity
python tools/benchmark_genomes.py runs/faz2/population.npz --steps 500 --repeats 3
```

Evrimleşmiş koloni `runs/faz2/population.npz` içinde; `--load-genomes` ile
yeni bir koşuma tohum yapılabilir (Faz 3 bununla başlayacak).
