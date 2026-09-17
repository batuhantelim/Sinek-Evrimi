# Faz 9 (revize) ölçütü — sürekli akrabalık, KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya sürekli akrabalık
koşumları başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.
`docs/faz9/olcut.md` bileşen 1'in ölçütüdür ve geçerliliğini korur.)

## Neden

Bileşen 1 ölçüldü: melez **ayrımcılığa uğramıyor** (FARK YOK 3/3), ama
mekanik kendi ölçüm zeminini yiyor. Akrabalık **"en az bir ortak bileşen"**
diye tanımlandığı için, popülasyonun yarısı melezken neredeyse herkes herkese
akraba oluyor: dış-grup fırsat payı %49.7→31.0, %11.9→**1.8**, %16.2→**6.6**
(zemin ölçütü 1/3 seed). `lineage_effective` ile dış-grup payı **zıt yönde**
hareket ediyor.

Teşhis: sorun ikili eşiğin kendisinde. `{A,B}` ile `{B,C}` **tam** akraba
sayılıyor, oysa payda bir bileşen ortak, bir bileşen ayrı.

## Değişiklik: akrabalık bir EŞİK değil, bir ORAN

`kin` artık `{-1, +1}` değil, paylaşılan bileşen oranından türeyen sürekli bir
sayı. Sensöre **ham** girer: `kin_sensor = 2·r − 1` (r ∈ [0,1] → sensör
[−1,+1], saf soylarda eski ±1 değerleriyle **birebir aynı**).

### ⚠ Bu bir DAVRANIŞ KURALI değil, bir ÖLÇÜ

Hiçbir yerde `if r > 0.5: paylaş` gibi bir eşik yoktur. Sensör ham oranı
taşır; beyin onu nasıl kullanacağına (ya da hiç kullanmayacağına) evrimle
karar verir. Kaynak testi (`test_continuous_kin_is_not_a_rule`) sosyal
döngüde oranın yalnızca sensöre ve **ölçüm** sayaçlarına gittiğini, hiçbir
davranış dalına eşikle girmediğini denetler.

### İki aday formül — seçim ÖLÇÜLEREK yapılır

| ad | tanım | `{A,B}` vs `{B,C}` | saf X vs `{X,Y}` |
|---|---|---|---|
| **`jaccard`** | \|kesişim\| / \|birleşim\| | 1/3 ≈ 0.333 | 1/2 = 0.5 |
| **`mean`** | \|kesişim\| / ortalama etiket boyu | 1/2 = 0.5 | 2/3 ≈ 0.667 |

Her ikisinde de saf X vs saf X = 1.0, saf X vs saf Y = 0.0 — yani **tek
bileşenli etiketlerde ikisi de eski ikili değere indirgenir**.

**Seçim kuralı (önceden ilan edilir):** kazanan, **çift bazında genom
benzerliğiyle daha yüksek Pearson korelasyonu** veren formüldür.
Çift bazında genom benzerliği, `genetic_r`'nin regresyon tanımının çift
karşılığıdır:

```
sim(a,b) = Σ_k (a_k − μ_k)(b_k − μ_k) / ( Σ_k (a_k − μ_k)² )    μ = havuz ortalaması
```

Ölçüm `tools/kin_ratio_probe.py` ile, melez **AÇIK** bir koşumda, son
çeyrekte, ≥ 2000 çift üzerinde, 3 seed'de yapılır. İki formül arasındaki fark
3 seed'de tutarlı değilse (işaret dönüyorsa) **`jaccard` seçilir** ve gerekçe
"fark ölçülemedi, daha muhafazakâr olan (yabancıyı daha geniş tanımlayan)
alındı" diye yazılır. Gerekçe her hâlükârda `docs/faz9/surekli.md`'ye yazılır.

### Dış-grup eşiği — SALT ANALİZ kategorisi

`rules.kinship.out_threshold: 0.5`. **r < 0.5 ⇒ dış-grup (yabancı)**;
r ≥ 0.5 ⇒ in-group. Bu eşik yalnızca `opp_kin`/`opp_nonkin` ve üç hücreli
melez matrisinin **sınıflandırmasında** kullanılır — ajanın kararına hiçbir
yerde girmez. Eşik burada, sonuç görülmeden sabitlenmiştir.

Saf soylarda (r ∈ {0,1}) eşik eski ikili ayrımla **aynı** sonucu verir.
Melez çiftlerde `jaccard` altında `{A,B}` vs `{B,C}` artık **yabancı**
sayılır; `mean` altında sınırda (0.5 ≥ 0.5) **akraba** sayılır. Formül
seçimi bu yüzden zemini de etkiler — ama seçim ölçütü yukarıda yazıldığı gibi
**genetik tutarlılıktır**, ölçülebilirlik değil. Ölçülebilirlik ayrı bir
ölçüttür (aşağıda) ve seçilen formülle **sağlanmazsa mekanik reddedilir**,
formül sonuca göre değiştirilmez.

---

## Ölçüt A — GERİYE DÖNÜK UYUM (önce bu)

1. `rules.hybrid.enabled: false` (ya da `rate: 0.0`) iken Faz 1–8'in
   `state_hash` değerleri **birebir** korunur. Test zorlar.
2. `kin_mode: binary` kolu, Faz 9 bileşen 1'in davranışını **birebir**
   üretir (aynı `state_hash`).
3. Saf soylardan oluşan bir popülasyonda `kin_mode: ratio` ile
   `kin_mode: binary` **birebir aynı** `state_hash` verir — yani sürekli
   ölçü, eski fazların hiçbirini değiştirmez.
4. Enerji korunumu: `energy_created` = 0 (oran bir ölçüdür, enerji taşımaz).

A sağlanmadan hiçbir koşum başlatılmaz.

## Ölçüt B — ASIL SORU: melez açıkken zemin ölçülebilir kalıyor mu

Melez **AÇIK**, `experiments/faz9_surekli.yaml`, son çeyrek:

1. **dış-grup fırsat payı ≥ %10, 3/3 seed** (sonra umut verirse 5/5).
   Bileşen 1'de bu 1/3 idi.
2. **etkin soy ≥ 5.0** (Faz 7/8 ölçütü değişmedi).
3. **`genetic_r`**, melez-yok kolunun **yarısının altına inmemeli**
   (bileşen 1 ile aynı döngüsellik şartı).
4. **Koloni sağlıklı**: N ve kişi başı toplama, melez-yok kolunun sırasıyla
   ≥ %50 ve ≥ %70'i.

Dört şart birden geçmezse: "sürekli akrabalık zemini kurtarmadı" diye
raporlanır ve bileşen 2–3'e **geçilmez** (bileşen 1'in dersi).

## Ölçüt C — iki sayı artık AYNI yönde mi

Bileşen 1'in rahatsız edici bulgusu: `lineage_effective` artarken dış-grup
payı düşüyordu. Sürekli ölçüde, üç kol (melez-yok / melez+ikili /
melez+sürekli) üzerinden `corr(lineage_effective, dış-grup payı)` raporlanır.
**İşaretin pozitife dönmesi bekleniyor**; dönmezse bu bir bulgudur ve öyle
yazılır (ölçüt değil, rapor edilen gözlem).

## Ölçüt D — mandal hâlâ duruyor mu (GÖZLEM, ölçüt değil)

Melez payı yine doyuma tırmanıyor mu? Sürekli akrabalık **mandalı çözmez**
(kural aynı: melez saf döller); yalnızca mandalın ölçüm zeminine verdiği
zararı tolere edip etmediğini sınar. Melez payı yine %50'nin üstüne çıkar ama
ölçüt B geçerse: **mandal ayrıca çözülmez**, öyle raporlanır.

---

## Kollar

| kol | ayar | ne için |
|---|---|---|
| **melezyok** | `rules.hybrid.enabled: false` | referans zemin (Faz 8) |
| **ikili** | melez açık, `kin_mode: binary` | Faz 9 bileşen 1'in birebir tekrarı |
| **surekli** | melez açık, `kin_mode: ratio` | asıl kol |
| **karistirma** | + `rules.kinship.control: shuffle_surnames` | bilgisiz kontrol |

Üç kol da **aynı seed**, aynı rejim, aynı adım sayısı. Her sosyal ölçü kendi
karıştırma kontrolüne karşı okunur.

## Değişmeyen kurallar

Rol/kast kodlanmaz (melez bir sınıf değildir); paylaşım/saldırı
ödüllendirilmez; in/out ayrı ölçülür; korunumlu enerji; determinizm;
kişi başı mutlak birim; kaldıracın yan etkisi ölçülür.

## Yaklaşım

1. Sürekli ölçüyü kur, **ölçüt A**'yı testlerle doğrula.
2. Formülü `tools/kin_ratio_probe.py` ile **seç** (yukarıdaki kural).
3. **Ölçüt B**'yi 3 seed'de ölç.
4. **Ancak B geçerse** bileşen 2 (soy-arası matris) ve bileşen 3
   (Faz 8'in işbirliği gözleminin kontrollü sınaması).
