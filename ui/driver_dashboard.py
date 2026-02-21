"""
Driver Dashboard — sürücü ekranı (v2 – professional motorsport design).

Sadece SignalStore'dan okur; veri kaynağı (mock / CAN) soyutlanmıştır.
"""

from __future__ import annotations

import sys
from typing import Dict, List

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from core.signal_store import SignalStore
from core.lap_timer import LapTimer

# ── Lap display colors ──────────────────────────────────────
CLR_LAP_TIME  = "#AAAAAA"
CLR_DELTA_POS = "#CC1100"      # kırmızı — PB'den yavaş
CLR_DELTA_NEG = "#1DB954"      # yeşil — PB'den hızlı
CLR_PB_FLASH  = "#B266FF"      # mor — yeni PB
CLR_STALE     = "#331111"      # koyu kırmızı — stale veri

# ── Colour palette ──────────────────────────────────────────
CLR_BG        = "#0A0A0A"
CLR_GEAR      = "#EAEAEA"      # sıcak beyaz
CLR_SPEED     = "#D0D0D0"
CLR_UNIT      = "#555555"
CLR_SEPARATOR = "#1E1E1E"
CLR_DIM       = "#1A1A1A"      # placeholder arka plan
CLR_DIM_BORDER= "#2A2A2A"
CLR_DIM_TEXT  = "#3A3A3A"
CLR_TICK      = "#444444"

RPM_MAX     = 14000
RPM_REDLINE = 12000

# Segment renk geçişi: koyu yeşil → yeşil → amber → kırmızı
SEG_COLORS = [
    (0.00, QColor("#0D4D0D")),   # koyu yeşil (başlangıç)
    (0.40, QColor("#1DB954")),   # yeşil
    (0.70, QColor("#4ADE40")),   # parlak yeşil
    (0.82, QColor("#F5A623")),   # amber
    (0.88, QColor("#E8471B")),   # turuncu-kırmızı
    (1.00, QColor("#CC1100")),   # koyu kırmızı
]

FONT_FAMILY = "Helvetica Neue"  # macOS'ta mevcut, temiz sans-serif


def _seg_color(ratio: float) -> QColor:
    """0.0–1.0 arası ratio için gradient renk döndürür."""
    for i in range(len(SEG_COLORS) - 1):
        r0, c0 = SEG_COLORS[i]
        r1, c1 = SEG_COLORS[i + 1]
        if ratio <= r1:
            t = (ratio - r0) / (r1 - r0) if r1 != r0 else 0
            return QColor(
                int(c0.red()   + (c1.red()   - c0.red())   * t),
                int(c0.green() + (c1.green() - c0.green()) * t),
                int(c0.blue()  + (c1.blue()  - c0.blue())  * t),
            )
    return SEG_COLORS[-1][1]


# ── RPM Bar Widget ──────────────────────────────────────────
class RPMBar(QWidget):
    """Professional gradient RPM bar with tick marks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rpm = 0.0
        self.setMinimumHeight(48)
        self.setMaximumHeight(56)

    def set_rpm(self, rpm: float) -> None:
        self._rpm = max(0.0, min(RPM_MAX, rpm))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_y = 0
        bar_h = h - 18  # tick label alanı için altta boşluk

        # Background
        p.fillRect(0, 0, w, h, QColor(CLR_BG))

        # Segments
        total = 70
        gap = 2
        seg_w = (w - (total - 1) * gap) / total
        filled = int((self._rpm / RPM_MAX) * total)

        for i in range(total):
            x = i * (seg_w + gap)
            ratio = i / total

            if i < filled:
                color = _seg_color(ratio)
            else:
                color = QColor(CLR_DIM)

            p.fillRect(QRectF(x, bar_y + 2, seg_w, bar_h - 4), color)

        # Tick marks ve labels
        p.setPen(QPen(QColor(CLR_TICK), 1))
        tick_font = QFont(FONT_FAMILY, 8)
        p.setFont(tick_font)

        for rpm_val in range(0, RPM_MAX + 1, 2000):
            x = (rpm_val / RPM_MAX) * w
            p.drawLine(int(x), bar_h, int(x), bar_h + 4)
            label = str(rpm_val // 1000) if rpm_val >= 1000 else "0"
            p.drawText(QRectF(x - 12, bar_h + 4, 24, 14),
                       Qt.AlignmentFlag.AlignCenter, label)

        # Redline marker: ince kırmızı çizgi
        rl_x = (RPM_REDLINE / RPM_MAX) * w
        p.setPen(QPen(QColor("#CC1100"), 2))
        p.drawLine(int(rl_x), bar_y, int(rl_x), bar_h)

        p.end()


# ── Warning Indicator ───────────────────────────────────────
class WarningIndicator(QWidget):
    """Küçük dikdörtgen uyarı göstergesi — dim/aktif."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._active = False
        self._color = CLR_DIM
        self.setFixedSize(52, 24)

    def set_active(self, active: bool, color: str = "#CC1100") -> None:
        self._active = active
        self._color = color if active else CLR_DIM
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Box
        p.setPen(QPen(QColor(CLR_DIM_BORDER), 1))
        p.setBrush(QColor(self._color))
        p.drawRect(1, 1, self.width() - 2, self.height() - 2)

        # Label
        text_color = "#FFFFFF" if self._active else CLR_DIM_TEXT
        p.setPen(QPen(QColor(text_color)))
        p.setFont(QFont(FONT_FAMILY, 8, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._label)
        p.end()


# ── Battery Bar Placeholder ─────────────────────────────────
class BatteryBar(QWidget):
    """İnce akü göstergesi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._level = 0.0
        self.setFixedSize(64, 18)

    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(1.0, level))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Outline
        p.setPen(QPen(QColor(CLR_DIM_BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(1, 1, w - 10, h - 2)
        # Terminal
        p.fillRect(w - 8, h // 2 - 3, 6, 6, QColor(CLR_DIM_BORDER))

        # Fill
        fill_w = int((w - 14) * self._level)
        if fill_w > 0:
            p.fillRect(3, 3, fill_w, h - 6, QColor(CLR_DIM_BORDER))

        p.end()


# ── Main Dashboard Window ───────────────────────────────────
class DriverDashboard(QMainWindow):
    def __init__(self, store: SignalStore, lap_timer: LapTimer | None = None, mock_source=None):
        super().__init__()
        self.store = store
        self.lap_timer = lap_timer
        self._mock_source = mock_source
        self.setWindowTitle("FST Driver Dashboard")
        self.setStyleSheet(f"background-color: {CLR_BG};")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 12, 24, 8)
        root.setSpacing(0)

        # ── RPM Bar ──
        self.rpm_bar = RPMBar()
        root.addWidget(self.rpm_bar)

        # ── NO SIGNAL banner (hidden by default) ──
        self.no_signal_label = QLabel("⚠  NO SIGNAL  ⚠")
        self.no_signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_signal_label.setStyleSheet(f"""
            color: #FFFFFF;
            background-color: #CC0000;
            font-size: 48px;
            font-family: '{FONT_FAMILY}', sans-serif;
            font-weight: 800;
            padding: 8px;
        """)
        self.no_signal_label.setFixedHeight(72)
        self.no_signal_label.hide()
        root.addWidget(self.no_signal_label)

        # ── Thin separator ──
        sep1 = QWidget()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background-color: {CLR_SEPARATOR};")
        root.addWidget(sep1)
        root.addSpacing(8)

        # ── Gear number (center, enormous) ──
        self.gear_label = QLabel("N")
        self.gear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gear_label.setStyleSheet(f"""
            color: {CLR_GEAR};
            font-size: 260px;
            font-family: '{FONT_FAMILY}', sans-serif;
            font-weight: 200;
        """)
        root.addWidget(self.gear_label, stretch=3)

        # ── Speed ──
        speed_container = QWidget()
        speed_layout = QHBoxLayout(speed_container)
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.setSpacing(4)
        speed_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.speed_label = QLabel("0")
        self.speed_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBaseline
        )
        self.speed_label.setStyleSheet(f"""
            color: {CLR_SPEED};
            font-size: 120px;
            font-family: '{FONT_FAMILY}', sans-serif;
            font-weight: 300;
        """)
        speed_layout.addWidget(self.speed_label)

        unit_label = QLabel("km/h")
        unit_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )
        unit_label.setStyleSheet(f"""
            color: {CLR_UNIT};
            font-size: 40px;
            font-family: '{FONT_FAMILY}', sans-serif;
            font-weight: 300;
            padding-bottom: 22px;
        """)
        speed_layout.addWidget(unit_label)

        root.addWidget(speed_container)

        # ── Lap Time Row ──
        if self.lap_timer:
            lap_sep = QWidget()
            lap_sep.setFixedHeight(1)
            lap_sep.setStyleSheet(f"background-color: {CLR_SEPARATOR};")
            root.addWidget(lap_sep)
            root.addSpacing(4)

            lap_row = QHBoxLayout()
            lap_row.setContentsMargins(0, 0, 0, 0)
            lap_row.setSpacing(24)

            # Current lap elapsed
            self.lap_elapsed_label = QLabel("LAP  0:00.000")
            self.lap_elapsed_label.setStyleSheet(f"""
                color: {CLR_LAP_TIME};
                font-size: 28px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: 400;
            """)
            lap_row.addWidget(self.lap_elapsed_label)

            lap_row.addStretch()

            # Last lap
            self.last_lap_label = QLabel("LAST  –:––.–––")
            self.last_lap_label.setStyleSheet(f"""
                color: {CLR_LAP_TIME};
                font-size: 28px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: 400;
            """)
            lap_row.addWidget(self.last_lap_label)

            lap_row.addStretch()

            # Delta
            self.delta_label = QLabel("Δ  –.–––")
            self.delta_label.setStyleSheet(f"""
                color: {CLR_UNIT};
                font-size: 36px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: 700;
            """)
            lap_row.addWidget(self.delta_label)

            root.addLayout(lap_row)
            root.addSpacing(4)

        # ── Bottom separator ──
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {CLR_SEPARATOR};")
        root.addWidget(sep2)
        root.addSpacing(6)

        # ── Bottom bar: warnings + critical readouts + battery ──
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(8)

        self.warnings: Dict[str, WarningIndicator] = {}
        for name in ("OIL", "TEMP", "BATT", "ENG"):
            w = WarningIndicator(name)
            self.warnings[name] = w
            bottom.addWidget(w)

        bottom.addStretch()

        # Coolant temp readout
        self.coolant_label = QLabel("CLT  –°C")
        self.coolant_label.setStyleSheet(f"""
            color: {CLR_LAP_TIME};
            font-size: 32px;
            font-family: '{FONT_FAMILY}', monospace;
            font-weight: 500;
        """)
        bottom.addWidget(self.coolant_label)

        bottom.addSpacing(16)

        # Oil pressure readout
        self.oil_p_label = QLabel("OIL  – bar")
        self.oil_p_label.setStyleSheet(f"""
            color: {CLR_LAP_TIME};
            font-size: 32px;
            font-family: '{FONT_FAMILY}', monospace;
            font-weight: 500;
        """)
        bottom.addWidget(self.oil_p_label)

        bottom.addSpacing(16)

        self.battery_bar = BatteryBar()
        bottom.addWidget(self.battery_bar, alignment=Qt.AlignmentFlag.AlignRight)

        root.addLayout(bottom)

        # ── Refresh timer (20 Hz) ──
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(50)

    # ── Refresh ─────────────────────────────────────────────
    def _refresh(self):
        snap = self.store.snapshot()

        # Check if any critical signal is stale
        critical = ["rpm", "speed", "gear"]
        any_stale = any(snap[s].stale for s in critical)

        # NO SIGNAL banner
        if any_stale:
            self.no_signal_label.show()
        else:
            self.no_signal_label.hide()

        # Gear
        g_sig = snap["gear"]
        if g_sig.stale or g_sig.value is None:
            self.gear_label.setText("–")
            self.gear_label.setStyleSheet(f"""
                color: {CLR_STALE};
                font-size: 260px;
                font-family: '{FONT_FAMILY}', sans-serif;
                font-weight: 200;
            """)
        else:
            g = int(g_sig.value)
            self.gear_label.setText(str(g) if g > 0 else "N")
            self.gear_label.setStyleSheet(f"""
                color: {CLR_GEAR};
                font-size: 260px;
                font-family: '{FONT_FAMILY}', sans-serif;
                font-weight: 200;
            """)

        # RPM
        r_sig = snap["rpm"]
        if r_sig.stale or r_sig.value is None:
            self.rpm_bar.set_rpm(0)
        else:
            self.rpm_bar.set_rpm(r_sig.value)

        # Speed
        s_sig = snap["speed"]
        if s_sig.stale or s_sig.value is None:
            self.speed_label.setText("–")
            self.speed_label.setStyleSheet(f"""
                color: {CLR_STALE};
                font-size: 120px;
                font-family: '{FONT_FAMILY}', sans-serif;
                font-weight: 300;
            """)
        else:
            self.speed_label.setText(str(int(s_sig.value)))
            self.speed_label.setStyleSheet(f"""
                color: {CLR_SPEED};
                font-size: 120px;
                font-family: '{FONT_FAMILY}', sans-serif;
                font-weight: 300;
            """)

        # Coolant temp (warn > 100°C, stale → dim)
        c_sig = snap["coolant"]
        if c_sig.stale or c_sig.value is None:
            self.coolant_label.setStyleSheet(f"""
                color: {CLR_STALE};
                font-size: 32px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: 500;
            """)
            self.coolant_label.setText("CLT  –°C")
        else:
            ct = c_sig.value
            color = CLR_DELTA_POS if ct > 100 else CLR_LAP_TIME
            self.coolant_label.setStyleSheet(f"""
                color: {color};
                font-size: 32px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: {'700' if ct > 100 else '500'};
            """)
            self.coolant_label.setText(f"CLT  {int(ct)}°C")

        # Oil pressure (warn < 1.5 bar, stale → dim)
        o_sig = snap["oil_pressure"]
        if o_sig.stale or o_sig.value is None:
            self.oil_p_label.setStyleSheet(f"""
                color: {CLR_STALE};
                font-size: 32px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: 500;
            """)
            self.oil_p_label.setText("OIL  – bar")
        else:
            op = o_sig.value
            color = CLR_DELTA_POS if op < 1.5 else CLR_LAP_TIME
            self.oil_p_label.setStyleSheet(f"""
                color: {color};
                font-size: 32px;
                font-family: '{FONT_FAMILY}', monospace;
                font-weight: {'700' if op < 1.5 else '500'};
            """)
            self.oil_p_label.setText(f"OIL  {op:.1f} bar")

        # Lap timer
        if self.lap_timer:
            # Current lap elapsed
            elapsed = self.lap_timer.elapsed
            self.lap_elapsed_label.setText(
                f"LAP  {self.lap_timer.format_time(elapsed)}"
            )

            # Last lap
            last = self.lap_timer.last_lap
            if last:
                time_str = self.lap_timer.format_time(last.lap_time)
                if last.is_personal_best:
                    self.last_lap_label.setStyleSheet(f"""
                        color: {CLR_PB_FLASH};
                        font-size: 28px;
                        font-family: '{FONT_FAMILY}', monospace;
                        font-weight: 700;
                    """)
                    self.last_lap_label.setText(f"PB!  {time_str}")
                else:
                    self.last_lap_label.setStyleSheet(f"""
                        color: {CLR_LAP_TIME};
                        font-size: 28px;
                        font-family: '{FONT_FAMILY}', monospace;
                        font-weight: 400;
                    """)
                    self.last_lap_label.setText(f"LAST  {time_str}")

            # Delta
            delta = self.lap_timer.delta
            if delta is not None:
                delta_str = self.lap_timer.format_delta(delta)
                color = CLR_DELTA_NEG if delta < 0 else CLR_DELTA_POS
                self.delta_label.setStyleSheet(f"""
                    color: {color};
                    font-size: 36px;
                    font-family: '{FONT_FAMILY}', monospace;
                    font-weight: 700;
                """)
                self.delta_label.setText(f"Δ  {delta_str}")

    # ── Keyboard shortcut ───────────────────────────────────
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and self._mock_source:
            if self._mock_source._paused:
                self._mock_source.resume()
            else:
                self._mock_source.pause()
        else:
            super().keyPressEvent(event)


# ── Entry point ─────────────────────────────────────────────
def create_driver_ui(store: SignalStore, lap_timer: LapTimer | None = None, mock_source=None):
    app = QApplication(sys.argv)
    window = DriverDashboard(store, lap_timer, mock_source)
    window.showFullScreen()
    sys.exit(app.exec())
