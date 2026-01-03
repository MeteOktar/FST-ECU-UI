Formula Student ECU – Pit UI (Mock Stage)

Bu proje, Formula Student aracı için pit/laptop üzerinde çalışan ECU telemetri arayüzünün ilk geliştirme aşamasını kapsar.
Bu aşamada gerçek CAN hattı kullanılmaz; sistem tamamen mock verilerle çalışır. Mimari, ileride CAN Bus ve DBC entegrasyonu eklendiğinde UI tarafında değişiklik gerektirmeyecek şekilde tasarlanır.

Amaç (Bu Aşama)

    UI ve veri katmanını CAN’dan tamamen bağımsız kurmak

    Realtime grafik ve numeric dashboard’u mock verilerle doğrulamak

    CAN Bus ve DBC entegrasyonuna sorunsuz geçiş için altyapı hazırlamak

Kapsam

    Bu aşamada yapılanlar:

        Mock sinyal üretimi (RPM, Speed, TPS, Coolant, Battery, Lambda)

        Realtime grafik çizimi

        Numeric telemetri ekranı

        Fault / DTC simülasyonu

        CAN uyumlu veri akışı mimarisi

    Bu aşamada yapılmayanlar:

        Gerçek CAN bağlantısı

        ECU’ya kalibrasyon parametresi yazma

        Araç üstü sürücü ekranı (dashboard)

Kullanılan Teknolojiler

    Python 3.11+

    PySide6 (Qt tabanlı UI)

    pyqtgraph (realtime grafik)

    NumPy (mock sinyal üretimi ve buffer yönetimi)

    python-can (ileride CAN entegrasyonu için)

    cantools (ileride DBC parsing için)

Kurulum
    pip3 install pyside6 pyqtgraph numpy python-can cantools

Dosya Düzeni

    ecu-pit-ui/
    │
    ├── ui/                  # Qt widget’ları ve layout’lar
    ├── core/                # SignalStore ve veri modelleri
    ├── datasource/
    │   ├── mock.py          # MockDataSource (aktif)
    │   └── can.py           # CANDataSource (şimdilik boş)
    ├── logging/             # CSV / Parquet loglama
    ├── config/
    │   └── signals.yaml     # Sinyal tanımları (unit, min, max)
    ├── main.py              # Uygulama giriş noktası
    └── README.md

Veri Akışı
    MockDataSource
        ↓
    SignalStore
    (value, timestamp, stale flag)
        ↓
    UI (Qt Timer ile render)

Tasarım Kararları

    UI thread hiçbir zaman blocking I/O yapmaz

    Veri kaynağı (mock / CAN) UI’dan tamamen soyutlanmıştır

    MockDataSource, ileride CAN frame veya DBC decode edilmiş sinyal üretecek şekilde değiştirilebilir

    Realtime performans, estetikten önce gelir

güzel kaynak

    https://www.teamtelemetry.de/Team_2023/Manual/manual_guide_English_V0601.pdf