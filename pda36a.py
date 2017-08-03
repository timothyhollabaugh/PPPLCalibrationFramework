"""
A module for the PDA36A Sensor
"""

import time
from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlNumber, ControlLabel
from labjack import ljm
from framework import Sensor


class PDA36A(Sensor):
    """
    A Sensor to measure the output of a PDA36A sensor with a Labjack
    Measures both power and frequency
    This will use any labjack T7 connected over USB
    This only uses the AIN0 port of the labjack
    """

    _labjack = None
    _serial_number = 0

    _power = 0

    _frequency = 0
    _freq_start = 0
    _last_on = False

    def __init__(self):
        self._labjack = ljm.openS("T7", "USB", "ANY")

        self._serial_number = ljm.eReadName(self._labjack, 'SERIAL_NUMBER')

        # Start making the GUI to display when this sensor is selected
        self._widget = BaseWidget()

        # Label to show the serial number of the Labjack
        self._widget.serial_number = ControlLabel()
        self._widget.serial_number.value = str(int(self._serial_number))

        # Number input to get the threshold for an 'on' signal
        # for frequency calculations
        self._widget.threshold = ControlNumber(
            label="Threshold",
            default=0.1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

    def get_custom_config(self):
        # Get the config GUI to display
        return self._widget

    def update(self):
        """
        Take a measurement of the labjack and update the GUI
        """

        # Make sure there is a labjack
        if self._labjack is not None:

            # Read the voltage from AIN0
            self._power = ljm.eReadName(self._labjack, 'AIN0')

            # Calculate the frequency
            # We need to get the time from rising edge to rising edge
            on = self._power > self._widget.threshold.value
            if on:
                if not self._last_on:
                    delta_time = time.time() - self._freq_start
                    self._frequency = 1 / delta_time
                    self._freq_start = time.time()
            self._last_on = on
        return [self._power, self._frequency]

    def begin_measuring(self, save_dir):
        pass

    def get_headers(self):
        return ["PDA36A Power", "PDA36A Frequency"]
