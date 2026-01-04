from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Optional

from core.signals_def import SignalDef


@dataclass(frozen=True, slots=True)
class SignalValue:
    value: Optional[float]
    ts: Optional[float]
    stale: bool


class SignalStore:
    def __init__(self, defs: Dict[str, SignalDef]):
        if not defs:
            raise ValueError("SignalStore requires non-empty defs")
        self._defs = defs
        self._lock = threading.Lock()
        self._data: Dict[str, Tuple[float, float]] = {}

    @property
    def defs(self) -> Dict[str, SignalDef]:
        return self._defs

    def update(self, name: str, value: float, ts: float | None = None) -> None:
        if name not in self._defs:
            raise KeyError(f"Unknown signal: {name}")

        try:
            v = float(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Signal '{name}' value must be numeric") from e

        if math.isnan(v) or math.isinf(v):
            return

        t = time.monotonic() if ts is None else float(ts)

        with self._lock:
            self._data[name] = (v, t)

    def get(self, name: str, now: float | None = None) -> SignalValue:
        if name not in self._defs:
            raise KeyError(f"Unknown signal: {name}")

        n = time.monotonic() if now is None else float(now)

        with self._lock:
            sample = self._data.get(name)

        if sample is None:
            return SignalValue(value=None, ts=None, stale=True)

        v, ts = sample
        stale = (n - ts) > self._defs[name].stale_after_s
        return SignalValue(value=v, ts=ts, stale=stale)

    def get_many(self, names: Iterable[str]) -> Dict[str, SignalValue]:
        n = time.monotonic()
        out: Dict[str, SignalValue] = {}

        with self._lock:
            local = dict(self._data)

        for name in names:
            if name not in self._defs:
                raise KeyError(f"Unknown signal: {name}")

            sample = local.get(name)
            if sample is None:
                out[name] = SignalValue(value=None, ts=None, stale=True)
                continue

            v, ts = sample
            stale = (n - ts) > self._defs[name].stale_after_s
            out[name] = SignalValue(value=v, ts=ts, stale=stale)

        return out

    def snapshot(self) -> Dict[str, SignalValue]:
        return self.get_many(self._defs.keys())
