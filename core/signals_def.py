from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SignalDef: #her signal classi
    name: str
    unit: str
    min: float
    max: float
    stale_after_s: float
    description: str = ""
