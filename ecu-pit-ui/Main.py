from core.config_loader import load_signal_defs
from core.signal_store import SignalStore

def main():
    defs = load_signal_defs("ecu-pit-ui/config/signals.yaml")
    store = SignalStore(defs)

    store.update("rpm", 3500)
    rpm = store.get("rpm")
    print(rpm)

if __name__ == "__main__":
    main()
