
from pyforms import BaseWidget
from pyforms.Controls import ControlCombo, ControlEmptyWidget
from framework import LightSource


class LightSourceTab(BaseWidget):
    """
    Tab to select the lightsource device
    """

    _lightsource = None
    _update_function = None

    def __init__(self, update_function=None):
        super().__init__("Light Source Tab")

        self._update_function = update_function

        self._device_select = ControlCombo(
            label="Light Source"
        )

        self._custom = ControlEmptyWidget()

        self._device_select.changed_event = self._on_device_change

        self._device_select.add_item('None', None)

        for class_type in LightSource.__subclasses__():
            self._device_select.add_item(class_type.__name__, class_type)

    def _on_device_change(self):
        device = self._device_select.value
        if callable(device):
            self._lightsource = device()
            self._custom.value = self._lightsource.get_custom_config()
        else:
            self._lightsource = None
            self._custom.value = None

        if callable(self._update_function):
            self._update_function({'lightsource': self._lightsource})
