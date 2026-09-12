# Faz 3 — adım 2: saldırı ve "iyilik ile öteki'ne kötülük aynı madalyonun iki yüzü mü?"

seed 42, 12000 adım = 24 dönem, `r_azalan + need_bonus` rejimi (adım 1.5'te
paylaşımın nefes aldığı rejim), Faz 2 tohumu, karıştırma kontrolüyle yan yana.

**Cevap: hayır. Grup-içi fedakârlık evrimleşti; grup-dışı düşmanlık evrimleşmedi.**
İkisi bu kurulumda aynı madalyonun iki yüzü çıkmadı.

---

## 1. Dört hücreli matris (son çeyrek, fırsata koşullu)

| | **asıl koşum** in-grup | **asıl** dış-grup | **kontrol** in-grup | **kontrol** dış-grup |
|---|---|---|---|---|
| **PAYLAŞ** | **56.11%** | 21.51% | 4.85% | 4.47% |
| **SALDIR** | 5.10% | 3.84% | 4.09% | 4.18% |

- **Kontrolün dört hücresi birbirinin aynı** (%4.1–4.9). Soyisim bilgi
  taşımayınca ne kayırma ne düşmanlık var — kontrol tam olarak yapması
  gerekeni yaptı.
- **Paylaşım güçlü biçimde akrabaya yönelmiş**: in/out oranı **×2.6**.
- **Saldırı yabancıya yönelmemiş** — hatta in-grupta biraz *daha yüksek*
  (%5.10 vs %3.84). Parochial imzanın ikinci yarısı **yok**.

## 2. Çeyrekler boyunca

| eğri | Ç1 → Ç2 → Ç3 → Ç4 | eğim |
|---|---|---|
| PAYLAŞ in-grup (asıl) | 42.5 → 69.1 → 64.6 → 56.1 | **+0.58**/dönem |
| PAYLAŞ dış-grup (asıl) | 17.7 → 11.9 → 23.0 → 21.5 | +0.34 |
| SALDIR in-grup (asıl) | 0.74 → 2.15 → 4.13 → 5.10 | +0.25 |
| SALDIR dış-grup (asıl) | 1.20 → 3.69 → 4.88 → 3.84 | +0.15 |
| PAYLAŞ in-grup (kontrol) | 18.0 → 7.2 → 5.9 → 4.9 | −0.72 |
| SALDIR in/dış (kontrol) | ikisi de 1.4 → 3.6 → 3.5 → 4.1 | +0.13 / +0.14 |

Saldırı oranı **her iki koşumda da aynı şekilde yükseliyor** (≈1.3% → 4.1%).
Yani saldırı bir strateji olarak evrimleşiyor ama **akrabalığa kör**:
kontrolde de birebir aynı yükseliş var.

## 3. Düzeltilmiş ayrımcılık ölçüleri (enerji katmanlı, yüzde puan)

```
asıl koşum
  paylaşım :  +7.1  +19.8  +57.0  +56.1  +47.8  +37.6  +28.3  +31.7
  saldırı  : -0.16  -0.43  -2.45  -1.25  -1.62  -2.57  +3.52  +0.33
kontrol
  paylaşım :  +1.1   -1.2   +0.8   +0.5   +0.7   +0.5   +0.5   +0.3
  saldırı  : +0.14  +0.45  +0.03  +0.00  -0.02  -0.24  +0.06  -0.27
```

- **Paylaşım**: asıl koşum +28…+57 puan, kontrol +0.3…+1.1. Büyüklük farkı
  ~50×. Sağlam.
- **Saldırı**: önce hafif akraba-esirgeme (−0.2…−2.6), sonra işaret değiştiriyor
  (+3.5, +0.3). **Kararsız ve paylaşımdan ~20× küçük.** Bir yön iddiası
  taşımıyor.

## 4. Birlikte hareket

| koşum | r(iç-paylaş, dış-saldır) | r(düzeltilmiş ayrımcılıklar) |
|---|---|---|
| asıl | 0.682 | 0.487 |
| kontrol | −0.902 | 0.126 |

İkinci sütun asıl kanıt. 0.487 sıfırdan büyük ama saldırı eğrisi zaten
kararsız olduğu için bu korelasyon **tek başına parochial altruism kanıtı
değildir** — dört hücreli matris ile birlikte okunmalı, ve matris saldırı
tarafında imzayı vermiyor.

## 5. Nedensel sonda (beyin düzeyinde)

Aynı sensör vektörü, **yalnızca** akrabalık kanalı değişiyor:

| kayıt | PAYLAŞ farkı | kayıran | SALDIR farkı | kayıran |
|---|---|---|---|---|
| asıl koşum | +0.0194 | %61.0 | +0.0419 | %56.1 |
| karıştırma kontrolü | +0.0186 | %56.6 | −0.0053 | %46.6 |
| faz2 tohumu | +0.0000 | %0.0 | +0.0000 | %0.0 |

**Dürüst okuma — iki ölçü büyüklükte uyuşmuyor** (adım 1.5'teki gibi):

- Simülasyon içi paylaşım ayrımcılığı **çok güçlü** (+28…+57 puan, kontrol düz).
- Sonda aynı yönü gösteriyor ama **zayıf** (%61.0 vs kontrol %56.6).
- Sonda rastgele sensör uzayında ortalama duyarlılık ölçer; gerçek koşumda
  beyin bu uzayın dar bir bölgesinde çalışır. Ayrımcılık o bölgede
  yoğunlaşmışsa sonda onu seyreltir. Bu sondanın bilinen sınırı.
- Saldırı için sonda **pozitif** (%56.1 = akrabaya saldırma eğilimi), yani
  parochial düşmanlığın tersi. Simülasyon içi ölçüyle de tutarlı.

## 6. Neden düşmanlık evrimleşmedi?

Saldırının kârlılığı hedefin **akrabalığına değil zenginliğine** bağlı:
maliyet sabit, kazanç hedefin enerjisiyle sınırlı. Fakire saldırmak zarar,
zengine saldırmak kâr. Kimin zengin olduğu ise soyisimden bağımsız.

Ayrıca bu rejimde komşuların **%84'ü akraba** (`opp_kin` 225 125 vs
`opp_nonkin` 41 822, assortment 0.751). Yabancı zaten nadir; "yabancıya
saldır" stratejisinin uygulanacak hedefi az.

## 7. Sınırlar

- **Soy çeşitliliği çöktü**: asıl koşumda etkin soy 4.7 (kontrolde 25.3).
  `max_speed 0.20` akrabaları bir arada tutuyor — assortment 0.751'i
  mümkün kılan da bu, ama dış-grup örneklemini küçülten de bu.
- Saldırı mekaniğinde **misilleme, hafıza, itibar yok**. Parochial altruism
  literatüründe grup-dışı düşmanlık genelde **gruplar arası rekabet**
  (kaynak için grup-grup çatışması) altında çıkar; burada rekabet bireysel.
- Tek seed. Bulgunun sağlamlığı için farklı seed'lerle tekrar gerekir.

## 8. Yeniden üretmek

```bash
python run.py --config experiments/faz3b_saldiri.yaml --viz frames \
    --load-genomes docs/faz2/population.npz
python run.py --config experiments/faz3b_kontrol.yaml --viz none \
    --load-genomes docs/faz2/population.npz
python tools/parochial_report.py runs/faz3b_saldiri runs/faz3b_kontrol
python tools/kin_probe.py runs/faz3b_saldiri/population.npz runs/faz3b_kontrol/population.npz
```
