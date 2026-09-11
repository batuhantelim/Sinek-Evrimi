# Faz 3 — adım 1.5: Hamilton kuralı b/c taraması

**Soru:** adım 1'de kin altruizmi çıkmadı. Sebep (A) "kin altruizmi doğası
gereği zor evrimleşir" mi, yoksa (B) "kurulumumuz `r·b > c`'yi yapısal olarak
sağlanamaz kıldı" mı?

**Cevap: (B), ve bu artık bir gözlem değil ispat.**

---

## 1. İspat

Paylaşım muhasebesi (`simulation._apply_social_rules`):

```
c (verenin kaybı)   = amount + overhead
b (alıcının kazancı) = min(amount, energy_max - alıcı_enerjisi)   ≤ amount
```

Dolayısıyla ham enerjide

```
b/c ≤ amount / (amount + overhead) ≤ 1
```

`overhead = 0` olsa bile **b/c ≤ 1**. Assortment tanımı gereği `r ≤ 1`.
Hamilton kuralı `r·b/c > 1` ister. İkisi birden sağlanamaz:

> **Doğrusal enerji aktarımıyla Hamilton kuralı bu tasarımda matematiksel
> olarak sağlanamaz.**

Tek kaçış yolu, enerjinin fitness'a dönüşümünün **doğrusal olmadığı** yer:
ölmek üzere olan bir alıcıya verilen enerji, tok bir vericinin kaybettiğinden
çok daha değerlidir. Ölçüldü: paylaşımların yalnızca **%2.9–6.6**'sı böyle bir
alıcıya gidiyor.

## 2. Tarama — `neighbor_need` sensörü YOKken (9 rejim)

seed 42, 6000 adım, Faz 2 tohumu, her rejim soyisim-karıştırma kontrolüyle.

| rejim | paylaşım | r (assort) | soy | kin_adj | kontrol | t | karar |
|---|---|---|---|---|---|---|---|
| taban | 2.09% | 0.049 | 2.5 | +1.019 | +0.857 | +1.09 | yok |
| c_sifir (overhead 0) | 2.33% | 0.068 | 3.4 | +0.578 | +1.017 | −1.24 | yok |
| b_kitlik | 3.27% | 0.119 | 9.7 | +0.196 | +0.727 | −1.69 | yok |
| r_yavas | 2.33% | 0.229 | 12.6 | +0.668 | +1.391 | −4.23 | yok |
| r_cok_bagli | 2.81% | 0.256 | 23.1 | +0.369 | +0.512 | −1.04 | yok |
| rbc (üçü birden) | 2.61% | 0.248 | 12.5 | +0.535 | +1.113 | −4.46 | yok |

6 rejimin **6'sında da** yok; 5'inde kontrol asıl koşumdan **yüksek**.

**r kolu enstrüman olarak çalışıyor** (0.049 → 0.256, ×5; soy çeşitliliği
2.5 → 23.1). Yani müdahale etkili, sonuç yine de negatif — bu tam olarak
aradığımız ayrım.

## 3. Eksik bilgi kanalı: `neighbor_need`

Beyin, komşusunun **ne kadar aç olduğunu göremiyordu**. `b > c` yalnızca ölmek
üzere olan birine verildiğinde mümkün olduğu için, o anı **hedefleyemiyordu**.
Yeni sensör (16. kanal) bu bilgiyi verir — ödül değil, bilgi.

| rejim | paylaşım | r | b/c | **r·b/c** | kurtarma | kin_adj | kontrol | t | karar |
|---|---|---|---|---|---|---|---|---|---|
| r_cok_bagli | 3.27% | 0.259 | 0.700 | 0.181 | 3.0% | +0.692 | +0.701 | −0.04 | yok |
| rbc | 2.41% | 0.295 | **1.000** | 0.295 | 2.9% | +0.261 | +0.210 | +0.18 | yok |
| rbc_uc (en uç) | 2.40% | **0.520** | 0.999 | **0.519** | 3.5% | +0.036 | +0.169 | −0.64 | yok |

En uç rejimde bile `r·b/c = 0.52` — gereken 1.0'ın yarısı. `b/c` tavana
(1.000) dayandı, `r` 0.52'ye çıktı; ikisinin çarpımı tanım gereği 1'i
geçemez. **İspat sayılarla doğrulandı.**

## 4. Önerilen kural: azalan verim (`rules.share.need_bonus`)

Tavanı kaldırmanın tek dürüst yolu, `b`'yi `c`'den büyük yapabilmek:

```
aktarılan = amount × (1 + need_bonus × alıcının_açlığı)
```

- Verene **hiçbir şey kazandırmaz** — hâlâ `amount + overhead` öder.
  Üç kuraldan ikincisi (paylaşım ödüllendirilmez) ihlal edilmez.
- Alıcının **dönüşüm verimini** modeller: aynı kalori aç bir hayvana daha
  değerlidir. Azalan marjinal fayda zaten bunun tanımıdır.
- `need_bonus: 0.0` varsayılan — adım 1 davranışı birebir korunur.

## 5. Kural uygulandı: paylaşma hayatta kaldı ve akrabaya yöneldi

`need_bonus: 3.0` + mekânsal bağ (`max_speed 0.20`, `spawn_radius 0.3`):

| rejim | paylaşım | r | b/c | kin_adj | kontrol | t | karar |
|---|---|---|---|---|---|---|---|
| r_azalan | 6.02% | 0.221 | **1.156** | +2.848 | +1.198 | **+2.48** | **VAR** |
| rbc_azalan | 90.60% | 0.305 | **1.106** | +14.466 | +0.569 | **+6.96** | **VAR** |

`b/c` ilk kez **1'in üstüne** çıktı — yapısal tavan kalktı. Taramadaki
9 rejimin hiçbirinde ulaşılamayan ayrışma iki rejimde birden geldi.

### Nedensel sonda (beyin düzeyinde)

| Kayıt | fark | akrabayı kayıran |
|---|---|---|
| `faz3_azalan` | +0.042 | %61.7 |
| `faz3_azalan` karıştırma kontrolü | +0.021 | %59.9 |
| `faz3` (adım 1) | +0.022 | %51.9 |
| faz2 tohumu | +0.000 | %0.0 |

**Dürüst okuma:** sonda farkı 61.7% vs 59.9% — tutarlı ama **mütevazı**.
Simülasyon içi ayrışma (t = +2.48) sondanın gösterdiğinden güçlü. Yani:

- **Paylaşımın hayatta kalması kesin** (%2.09 → %6.02, `b/c` 0.73 → 1.16).
  Aranan asıl kanıt buydu: sistem çalışıyor, eşiğin altındaydık.
- **Akrabaya yönelmesi kuvvetli ama nihai değil.** İki ölçü aynı yöne işaret
  ediyor, büyüklükleri farklı.

### Uyarılar

- `rbc_azalan`'ın %90.6'sı **doygunluğa yakın**: `overhead = 0` + `need_bonus = 3`
  ile paylaşım neredeyse bedava. Oranlar tavana dayandığında `kin_adj`
  büyüklüğü abartılı okunabilir. `r_azalan` (%6) daha temiz bir vaka.
- Karıştırma kontrolünde ölçülen `r = -0.003`: etiket karışınca assortment
  gerçekten sıfırlanıyor. Yani kontrol yalnızca "etiket bilgisi"ni değil
  "mekânsal akrabalık"ı da siliyor — karşılaştırma bu ikisini ayırmıyor.

## 6. Değişmeyen üç kural

1. **Rol/kast kodlanmadı** — `test_no_caste_is_hardcoded` kaynakta denetliyor.
2. **Paylaşım ödüllendirilmedi** — `test_fitness_has_no_sharing_term`
   hem config'te hem `Agent.fitness`'ta doğruluyor. `need_bonus` bunu ihlal
   etmez: alıcının verimidir, verenin ödülü değil.
3. **in/out ayrı ölçüldü**, örneklem büyüklükleriyle; her rejim kontrole karşı.

## 7. Yeni ölçüler

| Sütun | Anlamı |
|---|---|
| `kin_assortment` | `(gözlenen − beklenen)/(1 − beklenen)` ≈ Hamilton'un `r`'si. 0 = akrabalar rastgele dağılmış, 1 = komşular daima akraba |
| `kin_expected` | iyi karışmış dünyada beklenen akraba-komşu oranı (Σp²) |
| `bc_ratio` | gerçekleşen `b/c` — doğrusal aktarımda yapısal olarak ≤ 1 |
| `rescue_share` | paylaşımların kaçı ölmek üzere olan birine gitti |

## 8. Sonuç ve karar noktası

Hipotez **(B) doğrulandı**: adım 1'in negatif sonucu "kin altruizmi zor
evrimleşir" demek değildi; kurulum Hamilton kuralını matematiksel olarak
sağlanamaz kılmıştı. Tek yapısal engel kaldırılınca paylaşım hayatta kaldı.

Adım 2 (`attack` + tam in/out düşmanlık) artık sağlam temele oturabilir —
ama `need_bonus > 0` rejiminde kurulmalı, aksi halde aynı tavana çarpar.

## 9. Yeniden üretmek

```bash
python tools/sweep_hamilton.py --list
python tools/sweep_hamilton.py taban c_sifir r_yavas b_kitlik rbc --steps 6000
python tools/sweep_hamilton.py rbc_azalan r_azalan --steps 6000

python run.py --config experiments/faz3_azalan_verim.yaml --load-genomes docs/faz2/population.npz
python run.py --config experiments/faz3_azalan_kontrol.yaml --load-genomes docs/faz2/population.npz
python tools/kin_probe.py runs/faz3_azalan/population.npz runs/faz3_azalan_kontrol/population.npz
```
