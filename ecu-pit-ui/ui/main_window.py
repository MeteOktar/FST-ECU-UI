import sys
import time
from typing import Dict, List

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QMainWindow, QWidget

from core.signal_store import SignalStore, SignalValue


class MainWindow(QMainWindow):
    def __init__(self, store: SignalStore):
        super().__init__()
        self.store = store
        self.signals = list(store.defs.keys())
        self.data: Dict[str, List[float]] = {sig: [] for sig in self.signals}
        self.times: List[float] = []

        self.setWindowTitle("FST ECU Pit UI")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        self.plots: Dict[str, pg.PlotWidget] = {}
        self.curves: Dict[str, pg.PlotCurveItem] = {}

        row, col = 0, 0
        for sig in self.signals:
            plot = pg.PlotWidget(title=sig.upper())
            plot.setLabel('left', store.defs[sig].unit)
            plot.setLabel('bottom', 'Time (s)')
            plot.showGrid(x=True, y=True)
            curve = plot.plot(pen='y')
            self.plots[sig] = plot
            self.curves[sig] = curve
            layout.addWidget(plot, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(50)  # 20 Hz

        self.start_time = time.time()

    def update_plots(self):
        current_time = time.time() - self.start_time
        self.times.append(current_time)

        snapshot = self.store.snapshot()
        for sig in self.signals:
            val = snapshot[sig].value
            if val is not None:
                self.data[sig].append(val)
            else:
                # If no value, repeat last or 0
                last_val = self.data[sig][-1] if self.data[sig] else 0
                self.data[sig].append(last_val)

        # Keep only last 100 points for performance
        max_points = 100
        if len(self.times) > max_points:
            self.times = self.times[-max_points:]
            for sig in self.signals:
                self.data[sig] = self.data[sig][-max_points:]

        # Update curves
        for sig in self.signals:
            self.curves[sig].setData(self.times, self.data[sig])


def create_ui(store: SignalStore):
    app = QApplication(sys.argv)
    window = MainWindow(store)
    window.show()
    sys.exit(app.exec())