# Hazir deney konfigurasyonlari

Her dosya `config.yaml` uzerine bindirilir; sadece degistirdigi anahtarlari
icerir. `config.yaml` her zaman **en guncel fazin** varsayilanini tasir
(su an Faz 4), onceki fazlar buradan yeniden uretilir. Faz 1/2/3 dosyalari
`rules.predator.enabled: false` tasir: varsayilan ilerledi diye eski bir
deney sessizce baska bir deneye donusmemeli.

```bash
python run.py --config experiments/<dosya>.yaml
```

| Dosya | Soru |
|---|---|
| `faz1_klonlar.yaml` | Taban cizgisi: klon refleks ajanlar, mutasyon yok |
| `faz2_evrim.yaml` | Nesilli GA + evrimlesebilir rnn, sosyal kural yok |
| `faz2_kontrol_secilimsiz.yaml` | Secilim kapali, sadece suruklenme |
| `faz3_paylasimsiz.yaml` | Ayni ekoloji, paylasim mekanigi tamamen kapali |
| `faz3_kontrol_akrabalik.yaml` | **Asil Faz 3 kontrolu:** soyisim kalitsal degil |
| `faz3_kontrol_karistir.yaml` | Soyisimler her adim karistirilir (en sert kontrol) |
| `faz3_kontrol_dagit.yaml` | Yavrular haritaya rastgele dagilir (uzamsal yapi yok) |
| `faz3_azalan_verim.yaml` | Adim 1.5: need_bonus ile b/c tavani kalkar, paylasim yasar |
| `faz3_azalan_kontrol.yaml` | Ayni rejim + soyisim karistirma kontrolu |
| `faz3b_saldiri.yaml` | **Adim 2:** saldiri acik, dort hucreli in/out olcumu |
| `faz3b_kontrol.yaml` | Adim 2 karistirma kontrolu |
| `faz4_avci.yaml` | **Faz 4 adim 1:** dogal avci (ortak, dissal, GRUP-KOR) |
| `faz4_avci_kontrol.yaml` | Avcili kolun karistirma kontrolu |
| `faz4_avcisiz.yaml` | Avcisiz taban kol (2x2'nin ucuncu hucresi) |
| `faz4_avcisiz_kontrol.yaml` | Avcisiz karistirma kontrolu |
| `faz4_taban.yaml` | **Faz 4 olculebilir taban** — rejim ayni, TOHUM farkli (zorunlu) |

Tek seferlik degisiklikler icin dosya acmaya gerek yok:

```bash
python run.py --set rules.share.overhead=3.0 --name pahali_paylasim
python run.py --set rules.kinship.radius=6.0 --name genis_menzil
```
