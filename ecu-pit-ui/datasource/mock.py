
import threading
import time
import math
import random
from core.signal_store import SignalStore

class MockDataSource:
    def __init__(self, store: SignalStore, interval: float = 0.05):
        self._store = store
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None

        # Simulation state
        self._rpm = 1000.0
        self._speed = 0.0
        self._tps = 0.0
        self._coolant = 20.0
        self._battery = 13.5
        self._lambda = 1.0
        self._gear = 1  # Start in 1st gear

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("Mock Data Source Started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        print("Mock Data Source Stopped.")

    def _run(self):
        t = 0.0
        while self._running:
            start_time = time.monotonic()
            
            # 1. TPS: Random walk
            self._tps += random.uniform(-5, 5)
            self._tps = max(0.0, min(100.0, self._tps))

            # 2. RPM: Follows TPS with lag + noise
            target_rpm = 1000 + (self._tps * 120) # Max ~13000
            diff = target_rpm - self._rpm
            self._rpm += diff * 0.1 # Lag
            if self._rpm > 13500: self._rpm = 13500 # Limiter
            
            # 3. Gear shifting simulation
            # Gear ratios (approximate, higher number = lower gear)
            gear_ratios = [3.5, 2.0, 1.4, 1.0, 0.8]
            ratio = gear_ratios[self._gear - 1]
            
            # Speed: Based on RPM and current gear ratio
            self._speed = (self._rpm / 13000) * 120 / ratio
            
            # Gear shifting logic
            if self._rpm > 6500 and self._gear < 5:
                self._gear += 1
                print(f"Shifted to gear {self._gear}")
            elif self._rpm < 2500 and self._gear > 1 and self._speed > 10:  # Don't downshift at low speed
                self._gear -= 1
                print(f"Shifted to gear {self._gear}")
           
            # 4. Coolant: Slow heat up
            if self._coolant < 90:
                self._coolant += 0.05
            else:
                self._coolant += random.uniform(-0.1, 0.1)

            # 5. Battery: Noise
            self._battery = 13.8 + random.uniform(-0.2, 0.2)
            
            # 6. Lambda: Noise around 1.0
            self._lambda = 1.0 + random.uniform(-0.05, 0.05)

            # Update Store
            self._store.update("rpm", self._rpm)
            self._store.update("speed", self._speed)
            self._store.update("tps", self._tps)
            self._store.update("coolant", self._coolant)
            self._store.update("battery", self._battery)
            self._store.update("lambda", self._lambda)

            time.sleep(self._interval)
            t += self._interval
