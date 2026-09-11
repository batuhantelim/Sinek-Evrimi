# Faz 3 — adım 1 sonuçları: akrabalık ve paylaşma

seed 42, 12000 adım = **24 dönem**, 240×150 dünya, `steady_state` evrim,
Faz 2'nin kazananlarıyla tohumlanmış (`docs/faz2/population.npz`).

**Sonuç: akrabalığa yönelik fedakârlık 24 dönemde evrimleşmedi.**
Bu bir başarısızlık değil, ölçülmüş bir negatif sonuç — ve asıl değeri,
kontrolsüz okunsaydı *yanlış bir pozitif* rapor edilecek olmasında.

---

## 1. Paylaşma seçilimle eleniyor

| | 0. dönem | 23. dönem |
|---|---|---|
| Paylaşım oranı (fırsat başına) | %28.2 | **%1.0** |
| Dönem başına paylaşım olayı | 30 072 | 906 |

Beklenen davranış: paylaşımın **net maliyeti** var (aktarılan enerji +
`overhead`) ve `evolution.fitness` içinde paylaşım terimi **yok**. Dolaylı
getirisi maliyeti karşılamadığı sürece seçilim onu eler. Elemiş.

## 2. "Akrabaya daha çok paylaşıldı" — ama kontrol de öyle diyor

Son 12 dönemin ortalaması:

| Koşum | soy / etkin | `opp_kin` | ham `kin_bias` | **düzeltilmiş** |
|---|---|---|---|---|
| **faz3** (asıl) | 14 / 4.9 | 30 648 | +0.370 puan | **+0.326 puan** |
| `shuffle_surnames` kontrolü | 30 / 16.7 | 3 920 | +0.628 puan | **+0.624 puan** |

Karıştırma kontrolünde soyisimler **her adım** permüte edilir; etiket tanımı
gereği hiçbir bilgi taşımaz, dolayısıyla ayrımcılık imkânsızdır. Yine de bias
asıl koşumdan **daha yüksek** çıkıyor. Asıl koşumun +0.33'ü bir bulgu değil.

## 3. Nedensel sonda: beyin akrabalık kanalını okuyor mu?

`tools/kin_probe.py` ajanları hiç çalıştırmaz. Aynı sensör vektörünü beyne iki
kez verir, **sadece** akrabalık kanalını değiştirir (+1 / −1) ve paylaşım
motorundaki farkı ölçer. Uzamsal etki, enerji, yoğunluk sabittir.

| Kayıt | fark | akrabayı kayıran genom |
|---|---|---|
| **faz3** (asıl) | +0.029 | %53.8 |
| `shuffle_surnames` kontrolü | +0.104 | %82.4 |
| faz2 tohumu (referans) | +0.000 | %0.0 |

faz2 tohumunun tam olarak 0 çıkması, genom taşımasının (`migrate_weights`)
yeni sensör sütununu gerçekten sıfırladığının doğrulamasıdır.

Asıl koşum %50'lik sıfır çizgisinin hemen üstünde; anlamsız etiketli kontrol
ondan çok daha yüksek. **Ayrımcılık evrimleşmedi.**

## 4. Ham metrik neden yanıltıyor?

Akrabalar uzamsal kümelenir → kümeler zengin yemek yamalarındadır → oradaki
sinekler toktur → **paylaşacak bütçesi olan tok sinektir.** Yani "akrabaya
daha çok paylaşıldı" sonucu, hiçbir ayrımcılık olmadan da çıkar.

Bunu doğrudan ölçtük. Akrabalık sensörünü **okuyamayan** refleks beyinle
(`share_urge` sabit, ayrımcılık matematiksel olarak imkânsız):

| Kurulum | ham `kin_bias` | düzeltilmiş |
|---|---|---|
| Etiket anlamlı | **+3.803 puan** | +0.357 |
| Etiket karıştırılmış | +0.518 | +0.767 |

Ham fark, ayrımcılık sıfırken **+3.8 puan** — evrimleşmiş koşumda görülen
+0.37'nin on katı. `kin_bias_adj` (verici enerjisine göre 5 katman,
Mantel–Haenszel ağırlığı) konfoundu 10 kat azaltıyor ama sıfırlamıyor.

**Bu yüzden her iki metrik de mutlak değil, eşleşmiş bir kontrole karşı okunur.**

## 5. Sınırlar (dürüstlük notları)

- **Hiçbir kontrol soy büyüklüğü dağılımını birebir eşleştiremiyor.**
  Karıştırma kontrolünde etiketler her adım yeniden dağıldığı için soy sayıları
  birikmiyor (etkin 16.7 vs asıl koşumda 4.9). Bu yüzden **birincil kanıt
  sondadır**, in-sim oranlar değil.
- **Soy çeşitliliği yine de düşüyor**: 300 kurucu → 24. dönemde 14 soy
  (etkin 4.9, en büyüğü %49). Ölçüm için yeterli (`opp_kin` 30 648,
  `opp_nonkin` 22 405) ama daha uzun koşumlarda izlenmeli.
- **24 dönem az olabilir.** Akrabalık seçilimi için Hamilton kuralı
  (`r·b > c`) gerekir; `overhead` düşürülerek ya da kıtlık artırılarak
  `b/c` oranı yükseltilebilir. Denenmedi.
- Akrabalar ekranda **kümelenmiyor** (`kare_adim6100.png`): baskın soy tüm
  haritaya yayılmış. Uzamsal akrabalık yapısı zayıfsa, akrabalık seçiliminin
  başlıca mekanizması da zayıf demektir.

## 6. Görseller

| Dosya | İçerik |
|---|---|
| `karsilastirma.png` | Asıl koşum (turuncu) vs karıştırma kontrolü (yeşil), dönem bazlı |
| `donem_egrileri.png` | Asıl koşumun tüm dönem metrikleri |
| `kare_adim0500.png` | Adım 500: 91 soy, %25 paylaşım, soluk paylaşım çizgileri görünür |
| `kare_adim6100.png` | Adım 6100: 8 soy, %2.1 paylaşım, baskın soy (kırmızı) her yerde |
| `kin_sonda.txt` | Nedensel sonda çıktısı |
| `generations*.csv` | Ham dönem verisi |
| `population.npz` | Son popülasyon — Faz 3 adım 2'nin tohumu |

## 7. Yeniden üretmek

```bash
python run.py --name faz3 --viz frames --load-genomes docs/faz2/population.npz
python run.py --config experiments/faz3_kontrol_karistir.yaml --viz none \
    --load-genomes docs/faz2/population.npz
python tools/kin_probe.py runs/faz3/population.npz runs/faz3_kontrol_karistir/population.npz
python tools/plot_metrics.py runs/faz3 runs/faz3_kontrol_karistir --generations \
    --cols kin_bias_adj,coop_in_group,coop_out_group,lineage_effective,cooperation_rate
```
