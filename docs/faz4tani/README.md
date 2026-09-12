# Faz 4 tanı — rejim çatalı: gerçek mi, patoloji mi?

Faz 4 adım 1'de asıl bulgu avcı değildi: koşumlar birbirinden çok farklı
işbirliği düzeylerine yerleşiyordu ve bu salınım avcının etkisinden büyüktü.
Melez soyisim eklemeden önce zeminin ölçülebilir olması gerekiyordu.

**Tam rapor: [tani_bistabilite.md](tani_bistabilite.md)**

## Kısa cevap

| soru | cevap |
|---|---|
| **S1** Gerçek çatal mı, mekanik patoloji mi? | **İkisi de.** İki durum da kendi kendini sürdürüyor (gerçek çatal), ama havzalar eşit değil ve yüksek durum ölçümü imkânsız kılıyor. Önerdiğim mekanizma ("paylaşım toplamayı eziyor") **yanlıştı** — toplama neredeyse sabit. |
| **S2** Havzayı ne belirliyor? | Başlangıç durumu (popülasyonun kendisi) — seed değil, erken dinamik değil. Dışarıdan kontrol edilebiliyor. |
| **Karar** | Yeni taban: **parametre değişmiyor, başlangıç popülasyonu değişiyor.** Önceden ilan edilmiş beş ölçütün hepsini geçen tek koşul. |

## En önemli üç sayı

- Kişi başı toplama 12 seed'de yalnızca **1.5×** aralıkta (VK %13) oynarken
  paylaşım **41×** oynuyor → paylaşım toplamayı ezmiyor.
- Popülasyon her koşumun **%99.4'ünde tavanda** (N=700). Tavan 3000'e
  çıkarıldığında koloni 3000'i dolduruyor; yemek 16.7× kısıldığında yine 700.
  **Sınırlayan şey çevre değil, `agents.max_count`.**
- `need_bonus` 1.0 → 2.0 → 3.0: işbirliği %2.1 → %15.1 → %59.4, ama seed'ler
  arası yayılım 0.8 → **89.6** → 85.5 puan. Eşikte varyans patlıyor.

## Yeni taban

```bash
python run.py --config experiments/faz4_taban.yaml \
  --load-genomes docs/faz4tani/population_taban.npz --seed 42
```

5 seed'de işbirliği %10.0–22.7 (yayılım 12.7 puan), dış-grup fırsat payı %51,
etkin soy 7.2, toplama taban seviyesinde, tükenme yok.

## Dosyalar

| dosya | içerik |
|---|---|
| `tani_bistabilite.md` | tam rapor: A/B/C bölümleri, ölçüt denetimi, sınırlar |
| `olcut_BOLUM_B.md` | kabul ölçütü — **koşumlar başlamadan önce** commit edildi |
| `A_havza_haritasi.txt` | 12 seed'in havza tablosu, veriden türetilmiş eşikle |
| `havza_egrileri.png` | üç koşumun dönem eğrileri (kaçak / düşük / yeni taban) |
| `fazla_enerji_sondasi.txt` | paylaşımın verici enerji katmanına göre dağılımı |
| `A.jsonl` / `B.jsonl` / `C.jsonl` | ham tarama kayıtları |
| `population_taban.npz` | **yeni tabanın tohum popülasyonu** |
| `population_dusuk_havza.npz` | düşük havzayı üreten kaynak popülasyon (seed 42) |
