
import time
from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlNumber, ControlLabel
from labjack import ljm
from framework import Sensor

class PDA36A(Sensor):
    """
    A Sensor to measure the output of a PDA36A sensor with a Labjack
    """

    _labjack = None
    _serial_number = 0
    _power = 0

    _frequency = 0
    _freq_start = 0
    _last_on = False

    _start_time = 0

    _timer = QTimer()

    def __init__(self):
        self._labjack = ljm.openS("T7", "USB", "ANY")

        self._serial_number = ljm.eReadName(self._labjack, 'SERIAL_NUMBER')

        self._widget = BaseWidget()

        self._widget.measure_time = ControlNumber(
            label="Measure Time (s)",
            default=1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._widget.threshold = ControlNumber(
            label="Threshold",
            default=1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._widget.power = ControlLabel()
        self._widget.power.value = str(self._power)

        self._widget.frequency = ControlLabel()
        self._widget.frequency.value = str(self._frequency)

        self._timer.timeout.connect(self._measure)
        self._timer.start()

    def __del__(self):
        self._timer.stop()

    def get_custom_config(self):
        return self._widget

    def _measure(self):
        if self._labjack is not None:
            self._power = ljm.eReadName(self._labjack, 'AIN0')
            
            on = self._power > self._widget.threshold.value
            if on:
                if not self._last_on:
                    delta_time = time.time() - self._freq_start
                    self._frequency = 1 / delta_time
                    self._freq_start = time.time()
            self._last_on = on

            self._widget.power.value = str(self._power)
            self._widget.frequency.value = str(self._frequency)

    def begin_measuring(self):
        self._start_time = time.time()

    def update(self):
        return [self._power, self._frequency]

    def is_done(self):
        return time.time() - self._start_time > self._widget.measure_time.value
