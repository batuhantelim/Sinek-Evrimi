# Faz 5 — karşılıklılık

Faz 4.6 işbirliğinin **birinci** mekanizmasını (akrabalık) eledi. Bu faz
**ikinci** mekanizmayı test eder: karşılıklılık (Axelrod).

**Tam rapor: [karsiliklilik.md](karsiliklilik.md)**

## Kısa cevap

| | sonuç |
|---|---|
| **Önkoşul 1** tekrarlı karşılaşma | ✅ var: ajanların **%50.6**'sı aynı bireyle ≥3 **ayrı** buluşma (ölçüt %30). Dönüş aralığı medyan 16 adım, ömür 900. |
| **Önkoşul 2** tanıma | ✅ eklendi: `partner_known`, `partner_ledger` sensörleri |
| **Önkoşul 3** hafıza | ✅ RNN iç durumu zaten kalıcı + dışsal defter |
| **Karşılıklılık** | ❌ **0/5 seed** kontrolden ayrıştı (`t` = −0.94 ± 1.56) |
| **Misilleme** | ❌ **1/5** (ölçüt ≥4/5). Görünen +4…+8 puan tamamen konfound: kontrol de aynısını veriyor |
| **Kanal okunuyor mu** | ❌ tutarlı değil: sonda +0.038 (3/5 pozitif), kontrol +0.030 (4/5) |
| **Korunum** | ✅ 10/10 koşumda tam |

## ⚠ Kontrol tasarımı dersi

İlk kontrolüm (`shuffle_identity`) örneklemi yok ediyordu: defteri pozitif
fırsat 17 751 → **417**. Asıl kontrol `shuffle_ledger` — değerler ajanın
**kendi** partnerleri arasında karıştırılır, örneklem korunur, yalnızca bilgi
gider.

## Çalıştırma

```bash
python tools/encounter_probe.py --steps 4000          # önkoşul 1
python run.py --config experiments/faz5_hafiza.yaml \
  --load-genomes docs/faz45/population_ekoloji.npz --seed 42
python run.py --config experiments/faz5_hafiza.yaml --set rules.memory.control=shuffle_ledger ...
python tools/kin_probe.py runs/<kol>/population.npz --channel partner_ledger \
  --set rules.memory.enabled=true
```

## Dosyalar

| dosya | içerik |
|---|---|
| `karsiliklilik.md` | tam rapor: üç önkoşul, kontrol hatası ve düzeltmesi, 5 seed, sınırlar |
| `olcut.md` | ölçüt — **koşumlardan önce** commit edildi |
| `onkosul1_*.txt` | tekrarlı karşılaşma sondası (dört koşul) |
| `defter_sondasi.txt` | nedensel sonda: yalnızca defter işareti çevrilince motor farkı |
| `karsiliklilik.png` | dönem eğrileri: hafızalı / defter-kontrol / hafızasız |
| `generations_*.csv`, `ozet_*.txt` | seed 42'nin çıktıları |
| `population_hafiza.npz` | hafızalı kolun son popülasyonu |
