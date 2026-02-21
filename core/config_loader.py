from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml

from core.signals_def import SignalDef


def load_signal_defs(yaml_path: str | Path) -> Dict[str, SignalDef]:
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"signals.yaml not found: {path}")

    raw: Dict[str, Any]
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict) or "signals" not in raw:
        raise ValueError("YAML must be a mapping with a top-level 'signals:' key")

    signals = raw["signals"]
    if not isinstance(signals, dict) or len(signals) == 0:
        raise ValueError("'signals' must be a non-empty mapping")

    defs: Dict[str, SignalDef] = {}
    for name, cfg in signals.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"Signal '{name}' must map to a dictionary")

        unit = str(cfg.get("unit", "")).strip()
        if not unit:
            raise ValueError(f"Signal '{name}' missing non-empty 'unit'")

        try:
            vmin = float(cfg.get("min"))
            vmax = float(cfg.get("max"))
            stale_after_s = float(cfg.get("stale_after_s"))
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Signal '{name}' must have numeric min/max/stale_after_s"
            ) from e

        if vmax <= vmin:
            raise ValueError(f"Signal '{name}' max must be > min")
        if stale_after_s <= 0:
            raise ValueError(f"Signal '{name}' stale_after_s must be > 0")

        description = str(cfg.get("description", "")).strip()

        defs[name] = SignalDef(
            name=name,
            unit=unit,
            min=vmin,
            max=vmax,
            stale_after_s=stale_after_s,
            description=description,
        )

    return defs
