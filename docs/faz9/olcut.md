# Faz 9 ölçütü — KOŞUMLARDAN ÖNCE yazıldı

(Kural: "ölçütü sonucu görmeden ilan edin". Bu dosya Faz 9 koşumları
başlatılmadan önce commit edilmiştir; git geçmişi tanıktır.)

## Zemin

Faz 8'in yoğunluğa bağlı seçilim rejimi (`experiments/faz8_yogunluk.yaml`),
taze başlangıç, tohum gerekmez, korunumlu enerji. O zeminde etkin soy 4.4–15.1
ve dış-grup fırsat payı %11.9–49.8 — yani **"yabancı" gerçekten var** ve
in/out ilk kez anlamlı biçimde ölçülebiliyor.

---

## Bileşen 1 — melez soyisim

### Mekanik (kararlar önceden yazıldı)

- **Üreme aseksüel kalıyor.** Genom **tek** ebeveynden gelir; melezlik
  **yalnızca ETİKETdir**. (Faz 4.6/7 dersi: soyisim ≠ genetik benzerlik.)
- Bir doğum, ebeveynin menzilinde **farklı soydan** bir birey varsa ve
  `rules.hybrid.rate` olasılığı tutarsa melez olur: çocuğun etiketi
  `{X, Y}` — ebeveynin soyu ve o komşunun soyu.
- **Melezleşme yalnızca iki SAF soy arasında olur.** Ebeveyn zaten melezse
  çocuk etiketi aynen miras alır ("melez saf döller"). Gerekçe: etiket en
  fazla iki bileşen taşısın, yoksa hangi iki soyun birleştiği yorumlanamaz
  hale gelir ve etiket uzayı patlar.
- **Akrabalık = en az bir ortak bileşen.** Saf X ile melez {X,Y} akrabadır;
  {X,Y} ile {X,Z} akrabadır; {X,Y} ile saf Z yabancıdır. Bu, Faz 3'ten beri
  kullanılan ikili `kin` kanalını bozmaz, yalnızca genelleştirir.
- **Enerji defterine dokunmaz**: melezlik bir etikettir, ikinci ebeveyn hiçbir
  şey ödemez ve hiçbir şey almaz. `energy_created` = 0 kalmalı.
- `rate = 0.0`'da **hiçbir rastgele çekim yapılmaz** → Faz 1–8 `state_hash`
  değerleri birebir korunur.

### ⚠ Melezin kaderi ÖLÇÜLÜR, KODLANMAZ

Hiçbir yerde "melez şöyle muamele görsün" diye bir kural yoktur. Melez bir
sınıf/kast **değildir**; yalnızca iki bileşenli bir etikettir. Kaynak testi
bunu denetler.

### Ölçüt 1 — melez gerçekten oluşuyor ve ÖRNEKLEM YETERLİ

Son çeyrekte:

1. **melez payı ≥ %5** (popülasyonun),
2. **melezli fırsat gözlemi ≥ 1000** (`opp_hybrid`) — Faz 5/6'nın küçük
   örneklem tuzağına düşmemek için.

Sağlanmazsa `rules.hybrid.rate` yükseltilir ve **ölçütü geçen en küçük** değer
pinlenir; iki kola da aynı uygulanır.

### Ölçüt 2 — zemin bozulmadı

Faz 8'in dört parçalı ölçütü **hâlâ geçmeli** (etkin soy ≥ 5.0, dış-grup payı
≥ %10, en büyük soy < %80, koloni sağlıklı: N ve kişi başı toplama, melez-yok
kolunun sırasıyla ≥ %50 ve ≥ %70'i). Melez mekaniği çeşitliliği yok ederse
ölçecek bir şey kalmaz.

⚠ **Etiket sayımı notu**: melez `{X,Y}` soy istatistiklerinde **kendi grubu**
sayılır. Yani melez üretmek `lineage_effective`'i tanım gereği yükseltebilir —
bu yüzden ölçüt 2 melez-yok koluna karşı okunur, sıfıra karşı değil.

### Ölçüt 3 — döngüsellik/ölçülebilirlik korunuyor

`genetic_r`, melez-yok kolunun **yarısının altına inmemeli**. Melezlik akrabalık
yapısını yok ederse in/out ölçülebilir görünür ama ölçülecek akrabalık kalmaz
(Faz 8'de aynı şart konmuştu).

### ASIL SORU (bileşen 1): melez dışlanıyor mu, köprü mü?

Son çeyrekte, **fırsata koşullu** ve **verici enerjisine göre katmanlı**
(`kin_bias_adj` ile aynı düzeltme), üç hücre ayrı ölçülür:

| hücre | tanım |
|---|---|
| **saf-akraba** | en yakın komşu, aktörle aynı saf soydan |
| **melez-akraba** | en yakın komşu melez ve aktörle **en az bir** bileşeni ortak |
| **yabancı** | hiç ortak bileşen yok |

Sınıflandırma (koşumdan önce yazıldı, her biri **karıştırma kontrolüne** karşı):

- **DIŞLAMA**: melez-akrabaya paylaşım, saf-akrabadan **düşük** *ve* saldırı
  **yüksek** — ikisi de Welch t > 2 ile, ≥ 2/3 seed.
- **KÖPRÜ**: melez-akrabaya paylaşım saf-akrabadan düşük **değil** (t > −2) ve
  yabancıdan **yüksek** (t > 2), ≥ 2/3 seed.
- **FARK YOK**: ikisi de sağlanmıyor. (Beklenen varsayılan; negatif de sonuçtur.)

---

## Bileşen 2 — soy-arası ilişki matrisi (ÖLÇÜLEN, atanmayan)

`(soy_i, soy_j)` hücrelerinde paylaşım ve saldırı oranları. Hiçbir çift
"müttefik"/"düşman" diye **atanmaz**; etiketler matristen **sonradan** okunur.

### Ölçüt 4 — matris YAPI gösteriyor mu

Yapı iddiası ancak şu üçü birden sağlanırsa yazılır:

1. **Örneklem**: rapor edilen her hücrede en az **200 fırsat** gözlemi.
2. **Kontrole karşı fazlalık**: hücre oranlarının yayılımı (soy çiftleri arası
   standart sapma) karıştırma kontrolündeki yayılımdan **belirgin yüksek**
   (≥ 1.5×, ≥ 2/3 seed). Kontrolde etiket bilgisizdir; oradaki yayılım saf
   gürültü ve örneklem etkisidir.
3. **Kararlılık**: bir çiftin son iki çeyrekteki işareti aynı kalıyor mu
   (ittifak/düşmanlık **kalıcı** mı, yoksa dönemsel gürültü mü).

Sağlanmazsa: "matris yapı göstermedi, ilişkiler ayrımsız" diye raporlanır.

### Ek: melez oluşumu matrisle ilişkili mi

Hangi soy çiftleri melez üretiyor — düşük karşılıklı saldırı gösterenler mi?
`corr(çiftin melez üretimi, çiftin saldırı oranı)` raporlanır. **Tek başına
nedensellik iddiası değildir**; melezleşme mekaniği zaten mekânsal yakınlığa
bağlı ve saldırı da öyle (ortak konfound: komşuluk).

---

## Bileşen 3 — Faz 8'in işbirliği gözlemini KONTROLLÜ sına

Faz 8'de işbirliği 2/5 seed'de taban bandını (%0.6–2.4) aştı (%5.40, %3.49) ama
**eşleşmiş sosyal kontrol yoktu**; bu yüzden "gözlem" diye işaretlenmişti.

### Ölçüt 5 — yükseliş etiket BİLGİSİNE mi bağlı

Aynı seed'ler, aynı rejim, iki kol: asıl vs **karıştırma kontrolü** (soyisim
her adım permüte edilir; Faz 3'ten beri kullanılan en sert kontrol).

- **Yükseliş gerçek ve soy-temelli**: kontrolde işbirliği belirgin düşük
  (Welch t > 2, ≥ 2/3 seed) **ve** asıl kol bandın üstünde.
- **Yükseliş yoğunluk/çeşitlilik etkisi**: kontrolde de aynı seviyede →
  soy bilgisiyle ilgisi yok, öyle raporlanır.

### Ölçüt 6 — bandı aşan seed'lerde MEKANİZMA hangisi

Üçe ayrılır, her biri kendi eşleşmiş kontrolüne karşı:

- **akrabalık**: `kin_bias_adj` kontrolden yukarı ayrışıyor mu,
- **karşılıklılık**: `recip_bias_adj` (defter açıksa) ayrışıyor mu,
- **ayrımsız**: ikisi de hayır ama seviye yüksek.

### Ölçüt 7 — asimetri hâlâ duruyor mu

Faz 4.5/4.6/6'da üç kez tekrarlanan bulgu: **düşmanlık ayrım gözetir,
fedakârlık gözetmez**. Çeşitlilik + melez zeminde `atk_t` ile `share_t`
karşılaştırılır; değişip değişmediği raporlanır.

---

## Kontroller (ŞART)

| kol | ne bozar | beklenen |
|---|---|---|
| **melez-yok** | `rules.hybrid.enabled: false` — çocuk ebeveynin etiketini alır | melez mekaniğinin kendi etkisini izole eder |
| **karıştırma** | `rules.kinship.control: shuffle_surnames` — etiket tanımı gereği bilgisiz | melez/matris/işbirliği sinyalleri anlamsızlaşmalı |

Her metrik kontrole karşı okunur. **Örneklem büyüklükleri (melez sayısı, hücre
başına fırsat) her tabloda raporlanır** — küçük örneklem tuzağı (Faz 5/6 dersi).

## Değişmeyen kurallar

Korunumlu enerji (`energy_created` = 0, test zorlar); rol/kast kodlanmaz (melez
bir **sınıf değildir**); paylaşım/saldırı ödüllendirilmez; in/out ayrı;
determinizm (melez kapalıyken Faz 1–8 hash'leri korunur); kişi başı birim;
kaldıracın yan etkisi ölçülür.

## Yaklaşım

Önce **bileşen 1**: mekanik + melez-yok kontrolü, melez gerçekten oluşuyor mu
ve örneklem yeterli mi (ölçüt 1–3). Sonra bileşen 2 ve 3. 2–3 seed, kritik ya
da umut veren sonuç 5 seed.
