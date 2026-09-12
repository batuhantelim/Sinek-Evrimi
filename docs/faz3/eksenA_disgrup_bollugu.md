# Faz 3 ara tarama — eksen A: dış-grup bolluğu düşmanlığı tetikliyor mu?

Sağlamlık taramasında tek aykırı seed (2024) hem en yüksek dış-grup fırsat
payına hem en düşük kümelenmeye sahipti; bu iki şey o seed'de iç içeydi.
Burada onları ayırmaya çalıştık.

**Yeni mekanik yok** — yalnızca dünya parametreleri. Rejim adım 2 ile aynı;
`tests/test_tools.py` bir koşulun `evolution.fitness`, `rules.share.*`,
`rules.attack.*` veya `brain.*` dalına dokunmasını engelliyor.

6 koşul × 2 seed (42, 7) = 12 koşum, her biri kendi karıştırma kontrolüyle.
12000 adım, Faz 2 tohumu.

---

## 1. Ana sonuç: H1 reddedildi — ve adım 2'nin bulgusu daralıyor

| | |
|---|---|
| dış-grup payı ~ `atk_t` | **−0.133** (R² = 0.018) |
| assortment ~ `atk_t` | +0.414 (R² = 0.172) |
| yemek doluluğu ~ `atk_t` | **+0.502** (R² = 0.252) |

`atk_t < 0` = saldırı yabancıya yöneliyor.

**Dış-grup bolluğu düşmanlığı öngörmüyor.** En güçlü düşmanlık
(`atk_t` = −18.04) tablonun **en düşük** dış-grup payına (%4.8) sahip koşumda.

### Daha önemlisi: 12 koşumun 10'unda saldırı yabancıya yöneldi

| karar | koşum | koşul |
|---|---|---|
| kör | 2 | yalnızca `A1_taban` (dokunulmamış taban rejim) |
| **yabancıya** | **10** | diğer **5 koşulun hepsi** |

Adım 2'de "saldırı akrabalığa kör" demiştim. Bu **taban rejime özgüymüş**:
dünya parametrelerini herhangi bir yönde oynattığımızda düşmanlık ortaya
çıkıyor. Genel bir özellik değil, dar bir rejimin özelliği.

Bu, adım 2 raporunun düzeltilmesi gereken yanıdır. Adım 2'nin kendi içindeki
ölçümü yanlış değildi (5 seed'de tekrarlandı) — ama "bu kurulumda düşmanlık
evrimleşmiyor" genellemesi fazla genişti.

## 2. Eşik hikâyesi de tutmuyor

İlk 8 nokta "assortment ≥ 0.61 → kör, ≤ 0.46 → yabancıya" gibi temiz bir
eşik gösteriyordu. Son iki nokta onu bozdu:

| koşum | assortment | karar |
|---|---|---|
| `A1_taban` / s42 | **0.767** | kör |
| `A2_tam_karisma` / s42 | **0.768** | yabancıya |

Neredeyse aynı assortment, zıt karar. **Assortment tek başına belirleyici
değil.** (Bu yüzden 8 noktada durup rapor etmedim.)

## 3. Kendi taramamdaki konfound

Eksen A kaldıraçları (`split_rate`, `max_speed`, `spawn_radius`) yemek
dengesini de oynattı: koşul ortalamalarında yemek doluluğu **%22.7 – %49.4**
arasında değişiyor. Ve yemek doluluğu `atk_t`'nin en güçlü tek yordayıcısı
(+0.502). Yani eksen A, istemeden eksen B'yi de süpürmüş.

Tahminciler arası bağımlılık da yüksek:
`dış-grup ~ soy +0.875`, `dış-grup ~ assortment −0.829`, `assortment ~ soy −0.728`.

Çoklu regresyon (n = 12, 3 tahminci — **zayıf**):

```
atk_t = −30.0 + 12.0·dış_pay + 25.5·assortment + 15.2·yemek     R² = 0.424
```

Üç değişken birlikte varyansın ancak %42'sini açıklıyor. Bu tabloyla
"sürücü şudur" demek mümkün değil; söylenebilecek olan, **dış-grup
bolluğunun sürücü OLMADIĞI**.

## 4. Bir koşum niteliksel olarak farklı

`A2_tam_karisma` / s7: saldırı oranı **%77.2**, popülasyon 700 → 258.
Koloni çökmenin eşiğinde; oradaki "düşmanlık" muhtemelen çaresizlik.
Ortalamalara bu noktayı dâhil ederken dikkat.

## 5. Sıradaki: eksen B'yi kasıtlı süpürmek

Yemek doluluğu kazara süpürüldü ve en güçlü sinyali verdi. Artık kasıtlı
süpürülmeli — **assortment ölçülerek**, çünkü aynı konfound orada da olacak.
Ek olarak eksen B koşumlarında `opp_kin`/`opp_nonkin` mutlak sayıları da
kaydediliyor (bu partide yoktu).

Küçük örneklem uyarısı: `A2_orta_karisma`/s42'de dış-grup payı yalnızca %4.8
ve etkin soy 1.3. Oranın gürültü olmadığına dair dolaylı kanıt, `atk_t`'nin
dönemler **arası** hesaplanması: gürültü olsaydı dönem-içi varyans büyür ve
t küçük çıkardı; −18.04 tutarlı bir farkı gösterir. Yine de mutlak sayılarla
teyit edilmeli.

## 6. Tam tablo

Ham veri: `eksenA_taramasi.jsonl`, özet: `eksenA_taramasi.txt`.

```bash
python tools/env_sweep.py --conditions A1_cok_dusuk A1_taban A1_yuksek \
    A1_cok_yuksek A2_orta_karisma A2_tam_karisma --seeds 42 7
python tools/env_sweep.py --summary sonuc.jsonl
```
