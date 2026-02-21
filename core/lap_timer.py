"""
Lap Timer — tur süresi takibi ve delta hesaplama.

Thread-safe. Veri kaynağından bağımsız (mock / CAN / GPS beacon).
İleride gerçek tur tetikleyicisi (GPS geofence, IR beacon) buraya bağlanır.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True, slots=True)
class LapInfo:
    lap_number: int
    lap_time: float       # saniye
    is_personal_best: bool


class LapTimer:
    def __init__(self):
        self._lock = threading.Lock()
        self._lap_start: Optional[float] = None
        self._current_lap: int = 0
        self._laps: List[float] = []         # tamamlanan tur süreleri
        self._best_time: Optional[float] = None
        self._last_lap: Optional[LapInfo] = None

    def start_session(self) -> None:
        """Oturumu başlat, ilk tur sayacını çalıştır."""
        with self._lock:
            self._lap_start = time.monotonic()
            self._current_lap = 1

    def complete_lap(self) -> Optional[LapInfo]:
        """
        Mevcut turu tamamla, yeni turu başlat.
        Dışarıdan çağrılır: mock timer, GPS geofence, IR beacon vb.
        """
        with self._lock:
            if self._lap_start is None:
                return None

            now = time.monotonic()
            lap_time = now - self._lap_start

            # PB kontrolü
            is_pb = self._best_time is None or lap_time < self._best_time
            if is_pb:
                self._best_time = lap_time

            info = LapInfo(
                lap_number=self._current_lap,
                lap_time=lap_time,
                is_personal_best=is_pb,
            )

            self._laps.append(lap_time)
            self._last_lap = info

            # Yeni tur başlat
            self._lap_start = now
            self._current_lap += 1

            return info

    @property
    def elapsed(self) -> float:
        """Mevcut turun geçen süresi (saniye)."""
        with self._lock:
            if self._lap_start is None:
                return 0.0
            return time.monotonic() - self._lap_start

    @property
    def best_time(self) -> Optional[float]:
        with self._lock:
            return self._best_time

    @property
    def last_lap(self) -> Optional[LapInfo]:
        with self._lock:
            return self._last_lap

    @property
    def delta(self) -> Optional[float]:
        """
        Mevcut tur süresi - PB.
        Negatif = PB'den hızlı, Pozitif = PB'den yavaş.
        PB yoksa None döner.
        """
        with self._lock:
            if self._best_time is None or self._lap_start is None:
                return None
            return (time.monotonic() - self._lap_start) - self._best_time

    @property
    def current_lap_number(self) -> int:
        with self._lock:
            return self._current_lap

    @property
    def total_laps(self) -> int:
        with self._lock:
            return len(self._laps)

    @staticmethod
    def format_time(seconds: float) -> str:
        """Tur süresini 'M:SS.mmm' formatına çevir."""
        mins = int(seconds) // 60
        secs = seconds - (mins * 60)
        return f"{mins}:{secs:06.3f}"

    @staticmethod
    def format_delta(delta: float) -> str:
        """Delta'yı '+0.342' / '-0.521' formatına çevir."""
        sign = "+" if delta >= 0 else "-"
        return f"{sign}{abs(delta):.3f}"
