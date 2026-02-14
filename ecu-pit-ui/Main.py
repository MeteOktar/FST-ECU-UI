import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.config_loader import load_signal_defs
from core.signal_store import SignalStore
from datasource.mock import MockDataSource
from ui.main_window import create_ui

def main():
    print("Initializing FST ECU Pit UI (Mock Stage)...")
    defs = load_signal_defs(BASE_DIR / "config" / "signals.yaml")
    store = SignalStore(defs)

    mock_source = MockDataSource(store)
    mock_source.start()

    try:
        print("Starting UI...")
        # Start the UI
        create_ui(store)
    except KeyboardInterrupt:
        print("\nStopping...")
        mock_source.stop()

if __name__ == "__main__":
    main()
