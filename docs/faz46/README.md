# Faz 4.6 — korunumlu zeminde `r·b > c` aranması

Faz 4.5, Faz 3'ün pozitif sonucunun paylaşımın **enerji ürettiği** bir dünyanın
artefaktı olduğunu gösterdi. Bu faz asıl soruyu sorar: korunum yasasını
**ihlal etmeden** akraba fedakârlığının gerektirdiği `r·b > c` sağlanabilir mi?

**Tam rapor: [hamilton_arayisi.md](hamilton_arayisi.md)**

## Kısa cevap: hayır — ve nedeni yapısal

| | sonuç |
|---|---|
| **15 dürüst koşul** | `r·b/c` en yüksek **0.989**; **0/15** koşul 1'i geçiyor. Enerji korunumu 15/15 koşumda TAM (yaratılan enerji = 0). |
| **Neden** | Korunumlu aktarımda enerji `b/c ≤ 1` **yapısal**; ölçülen fitness `b/c` yalnızca 0.98–1.48. `r ≤ 1` tanım gereği. |
| **Takas** | `r` ile `b/c` **ters** hareket ediyor (korelasyon −0.51): akrabaları sıkıştırmak `r`'yi yükseltiyor ama komşular zaten benzer ve tok olduğu için transferin marjinal faydası düşüyor. |
| **En iyi ölçülebilir nokta** | `r·b/c` = 0.901'de ayrışma **3/5 seed** (ölçüt ≥2/3 istiyordu) ve etki **0.16 puan** — Faz 3'ün pompalı zeminindeki +28 puanın yanında yok hükmünde. |
| **Yan bulgu** | Saldırı 5/5 seed'de yabancıya yöneliyor (`atk_t` −6.7…−14.7). Korunumlu zeminde **düşmanlık ayrım gözetiyor, fedakârlık gözetmiyor.** |

## Yeni ölçüm araçları

- `genetic_r` — Hamilton'un `r`'si **etiketten değil genomdan**: aktör ile en
  yakın komşusunun genom benzerliği (regresyon tanımı; rastgele eşleşmede 0,
  klonlarda 1).
- `tools/hamilton_probe.py` — `b` ve `c` **varsayılmaz, ölçülür**:
  `yavru ~ yaş + yemek + VERİLEN + ALINAN` regresyonu.
- `bc_ratio` (enerji) ile `bc_ratio_fit` (`need_bonus` çarpanlı **tahmin**)
  ayrıldı. İkincisinden "Hamilton sağlandı" çıkarmak kendi varsayımını ölçmek
  olurdu — ve ölçüm onu 2–3× fazla tahmin ettiğini gösteriyor.

## Dosyalar

| dosya | içerik |
|---|---|
| `hamilton_arayisi.md` | tam rapor: 15 koşul, takas, beklentinin tersine çıkan kaldıraç, sınırlar |
| `olcut.md` | ölçüt — **koşumlardan önce** commit edildi |
| `hamilton_haritasi.txt` / `.json` | 15 koşulun `r`, `b`, `c`, `b/c`, `r·b/c` tablosu |
| `hamilton_takas.png` | `r` arttıkça `b/c` düşüyor; `r·b/c` 1'in altında tıkanıyor |
| `sonda_*.txt` | üç temsili koşulun ham sonda çıktısı |
| `generations_BC6_*.csv` | en iyi ölçülebilir koşulun asıl + kontrol koşumu |
