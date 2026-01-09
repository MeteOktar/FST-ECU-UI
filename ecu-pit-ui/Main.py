import time
from core.config_loader import load_signal_defs
from core.signal_store import SignalStore
from datasource.mock import MockDataSource

def main():
    print("Initializing FST ECU Pit UI (Mock Stage)...")
    defs = load_signal_defs("ecu-pit-ui/config/signals.yaml")
    store = SignalStore(defs)

    mock_source = MockDataSource(store)
    mock_source.start()

    try:
        while True:
            # Print a few key signals
            data = store.snapshot()
            rpm = data["rpm"].value
            speed = data["speed"].value
            temp = data["coolant"].value
            tps = data["tps"].value
            
            # Simple dashbaord output
            print(f"\rRPM: {rpm:.0f} | Speed: {speed:.1f} km/h | TPS: {tps:.1f}% | Coolant: {temp:.1f} C   ", end="", flush=True)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        mock_source.stop()

if __name__ == "__main__":
    main()
