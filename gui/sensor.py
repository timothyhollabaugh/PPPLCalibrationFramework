"""
Module for the sensor tab in the GUI
"""

from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlCombo, ControlEmptyWidget, ControlList, ControlCheckBox
from framework import Sensor


class SensorTab(BaseWidget):
    """
    Tab for sensors
    Shows a drop down with all subclasses of Sensor
    imported anywhere into this program

    When one is selected, it creates an instance of that sensor
    and shows the custom config GUI for that Sensor.
    """

    _sensor = None
    _timer = QTimer()

    def __init__(self, update_function=None):
        super().__init__("Output Tab")

        # The update function will be called when the selected sensor changes to fire the 'sensor' event
        self._update_function = update_function

        self._device_select = ControlCombo(
            label="Sensor"
        )

        self._custom = ControlEmptyWidget()

        self._device_select.changed_event = self._on_device_change

        self._device_select.add_item('None', None)

        self._output = ControlList()

        self._live = ControlCheckBox(
            label="Live Output"
        )
        self._live.changed_event = self._on_live

        for class_type in Sensor.__subclasses__():
            self._device_select.add_item(class_type.__name__, class_type)

    def update_events(self, events):
        if isinstance(self._sensor, Sensor):
            self._sensor.update_events(events)

    def _on_device_change(self):
        device = self._device_select.value
        if callable(device):
            self._sensor = device()
            self._custom.value = self._sensor.get_custom_config()
        else:
            self._sensor = None
            self._custom.value = None
            #print("Not Subclass")

        if callable(self._update_function):
            self._update_function({'sensor': self._sensor})

    def _on_live(self):
        if self._live.value:
            if isinstance(self._sensor, Sensor):
                self._sensor.begin_measuring()
                self._output.horizontal_headers = self._sensor.get_headers()
                self._timer.timeout.connect(self._update_sensor)
                self._timer.start(50)
        else:
            self._timer.stop()
            if isinstance(self._sensor, Sensor):
                self._sensor.finish_measuring()

    def _update_sensor(self):
        if isinstance(self._sensor, Sensor):
            self._output += self._sensor.update()
            self._output.tableWidget.scrollToBottom()
