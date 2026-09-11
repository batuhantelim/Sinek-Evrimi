# Hazir deney konfigurasyonlari

Her dosya `config.yaml` uzerine bindirilir; sadece degistirdigi anahtarlari
icerir. `config.yaml` her zaman **en guncel fazin** varsayilanini tasir
(su an Faz 3), onceki fazlar buradan yeniden uretilir.

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

Tek seferlik degisiklikler icin dosya acmaya gerek yok:

```bash
python run.py --set rules.share.overhead=3.0 --name pahali_paylasim
python run.py --set rules.kinship.radius=6.0 --name genis_menzil
```
