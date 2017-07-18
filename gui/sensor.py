
from pyforms import BaseWidget
from pyforms.Controls import ControlCombo, ControlEmptyWidget
from framework import Sensor


class SensorTab(BaseWidget):
    """
    Tab for sensors
    """

    _sensor = None

    def __init__(self, update_function = None):
        super().__init__("Output Tab")

        self._update_function = update_function

        self._device_select = ControlCombo(
            label="Sensor"
        )

        self._custom = ControlEmptyWidget()

        self._device_select.changed_event = self._on_device_change

        self._device_select.add_item('None', None)

        for class_type in Sensor.__subclasses__():
            self._device_select.add_item(class_type.__name__, class_type)

    def _on_device_change(self):
        device = self._device_select.value
        if callable(device):
            self._sensor = device()
            self._custom.value = self._sensor.get_custom_config()
        else:
            self._sensor = None
            self._custom.value = None
            print("Not Subclass")

        if callable(self._update_function):
            self._update_function({'sensor': self._sensor})
