# Faz 4.5 — ekoloji borcu

Tanı, popülasyonu çevrenin değil `agents.max_count`'un sınırladığını
göstermişti. Bu faz zinciri onarır: **enerji → üreme → seçilim**.

**Tam rapor: [ekoloji_borcu.md](ekoloji_borcu.md)**

## Kısa cevap

| | sonuç |
|---|---|
| **Asıl bulgu** | `need_bonus` alıcıya vericinin kaybettiğinden 4 kata kadar **fazla enerji** veriyordu: paylaşım korunumlu değildi, koloniye net enerji **ekliyordu**. %90 işbirliğinde üretilen enerji yenen yemeğe eşit, %97'de 3 katı. |
| **Bölüm 1** | Pompa kalkınca **yemek arzını değiştirmeye gerek kalmadı**: koloni kendiliğinden N ≈ 750'de dengeleniyor. Tavana değme %99.4 → **%0.0**, yanan üreme hakkı ~456/adım → **0**. 5/5 seed. |
| **Bölüm 2** | Seçilim zinciri onarıldı: yaş kontrollü "yemek → yavru" bağı **+0.047 → +0.738**. Eski kurulumda yetişkinlerin %67'si hiç üremiyordu. Ve **vermek kârlıydı** (+0.114); artık maliyetli (−0.080). |
| **Bölüm 3** | Faz 3'ün ana bulgusu **tekrarlanmadı**: in-grup fedakârlık 5/5 → **0/5** seed'de kontrolden ayrışıyor. Sonuç **(c)**. |

## Yeni taban

```bash
python run.py --config experiments/faz45_ekoloji.yaml \
  --load-genomes docs/faz4tani/population_taban.npz --seed 42
python tools/selection_probe.py --steps 8000
```

## Dosyalar

| dosya | içerik |
|---|---|
| `ekoloji_borcu.md` | tam rapor: pompa, üç bölüm, etkilenen eski sonuçlar, sınırlar |
| `olcut_BOLUM1.md` | Bölüm 1 ölçütü — **koşumlardan önce** commit edildi |
| `secilim_sondasi.txt` | seçilim zinciri sondasının ham çıktısı |
| `populasyon_karsilastirma.png` | eski (tavanda düz) vs yeni (sönümlenen boom–bust) |
| `generations_*.csv`, `ozet_*.txt` | seed 42'nin çıktıları |
| `population_ekoloji.npz` | temiz ekolojinin son popülasyonu |
