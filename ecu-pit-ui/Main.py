import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.config_loader import load_signal_defs
from core.signal_store import SignalStore
from core.lap_timer import LapTimer
from datasource.mock import MockDataSource


def main():
    driver_mode = "--driver" in sys.argv

    print("Initializing FST ECU Pit UI (Mock Stage)...")
    defs = load_signal_defs(BASE_DIR / "config" / "signals.yaml")
    store = SignalStore(defs)

    lap_timer = LapTimer() if driver_mode else None

    mock_source = MockDataSource(store, lap_timer=lap_timer)
    mock_source.start()

    try:
        if driver_mode:
            print("Starting Driver Dashboard...")
            from ui.driver_dashboard import create_driver_ui
            create_driver_ui(store, lap_timer=lap_timer, mock_source=mock_source)
        else:
            print("Starting Pit UI...")
            from ui.main_window import create_ui
            create_ui(store)
    except KeyboardInterrupt:
        print("\nStopping...")
        mock_source.stop()

if __name__ == "__main__":
    main()
