# Formula Student ECU – Telemetri UI (Mock Stage)

Bu proje, Formula Student aracı için **pit/laptop** ve **araç içi sürücü** telemetri arayüzünü kapsar.
Bu aşamada gerçek CAN hattı kullanılmaz; sistem tamamen mock verilerle çalışır.
Mimari, ileride CAN Bus ve DBC entegrasyonu eklendiğinde UI tarafında değişiklik gerektirmeyecek şekilde tasarlanmıştır.

## Amaç (Bu Aşama)

- UI ve veri katmanını CAN'dan tamamen bağımsız kurmak
- Realtime grafik ve numeric dashboard'u mock verilerle doğrulamak
- CAN Bus ve DBC entegrasyonuna sorunsuz geçiş için altyapı hazırlamak

## Kapsam

**Bu aşamada yapılanlar:**

- Mock sinyal üretimi (RPM, Speed, TPS, Coolant, Battery, Lambda, Oil Pressure, Oil Temp, Fuel Pressure, Gear)
- Pit UI: Realtime grafik çizimi (tüm sinyaller)
- Driver Dashboard: Vites, RPM bar, hız, tur süresi, delta göstergesi
- Lap Timer: Tur süresi takibi, Personal Best, Delta (PB'ye göre +/-)
- CAN uyumlu veri akışı mimarisi

**Bu aşamada yapılmayanlar:**

- Gerçek CAN bağlantısı
- ECU'ya kalibrasyon parametresi yazma
- Fault / DTC simülasyonu

## Kullanılan Teknolojiler

- Python 3.11+
- PySide6 (Qt tabanlı UI)
- pyqtgraph (realtime grafik)
- NumPy (mock sinyal üretimi ve buffer yönetimi)
- PyYAML (sinyal konfigürasyonu)
- python-can (ileride CAN entegrasyonu için)
- cantools (ileride DBC parsing için)

## Kurulum

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Çalıştırma

### Pit UI (laptop – tüm sinyallerin grafikleri)

```bash
python ecu_ui/main.py
```

### Driver Dashboard (araç içi – vites, RPM, hız, lap time)

```bash
python ecu_ui/main.py --driver
```

Fullscreen açılır. Çıkmak için `Cmd+Q` veya `Alt+F4`.

### Klavye Kısayolları (Driver Dashboard)

| Tuş     | İşlev                                                            |
| ------- | ---------------------------------------------------------------- |
| `Space` | Mock veri akışını kes / devam ettir (CAN disconnect simülasyonu) |
| `Cmd+Q` | Çıkış                                                            |

### Stale Data Detection

CAN hattı koparsa veya veri akışı durursa dashboard otomatik tepki verir:

- **⚠ NO SIGNAL ⚠** kırmızı banner ekranın üstünde belirir
- Vites, hız, CLT, OIL değerleri "–" yazısına döner ve kararır
- RPM bar sıfıra düşer
- Veri tekrar geldiğinde her şey otomatik normale döner

Stale süresi `config/signals.yaml` içindeki `stale_after_s` değerine göre belirlenir.

## Dosya Düzeni

```
ecu-pit-ui/
├── Main.py                    # Uygulama giriş noktası (--driver flag)
├── config/
│   └── signals.yaml           # Sinyal tanımları (unit, min, max, stale)
├── core/
│   ├── signals_def.py         # SignalDef dataclass
│   ├── config_loader.py       # YAML → SignalDef parser
│   ├── signal_store.py        # Thread-safe merkezi veri deposu
│   └── lap_timer.py           # Tur süresi takibi ve delta hesaplama
├── datasource/
│   └── mock.py                # Mock sinyal üreteci + lap simulation
└── ui/
    ├── main_window.py         # Pit UI (pyqtgraph grafikleri)
    └── driver_dashboard.py    # Sürücü dashboard (RPM bar, vites, hız, lap)
```

## Veri Akışı

```
MockDataSource (ileride: CANDataSource)
        ↓ store.update()
    SignalStore (thread-safe)
        ↓ store.snapshot()
    UI (Qt Timer, 20 Hz)
        ├── Pit UI (grafikler)
        └── Driver Dashboard (göstergeler + lap timer)
```

## Tasarım Kararları

- UI thread hiçbir zaman blocking I/O yapmaz
- Veri kaynağı (mock / CAN) UI'dan tamamen soyutlanmıştır
- `SignalStore` ortak interface — aynı store'dan birden fazla UI beslenebilir
- Realtime performans, estetikten önce gelir
- Tur tetikleyicisi (mock timer / GPS / IR beacon) `LapTimer.complete_lap()` üzerinden bağlanır

## Güzel Kaynak

- https://www.teamtelemetry.de/Team_2023/Manual/manual_guide_English_V0601.pdf
