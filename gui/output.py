
from pyforms import BaseWidget
from pyforms.Controls import ControlCombo, ControlEmptyWidget
from framework import OutputDevice


class OutputTab(BaseWidget):
    """
    Tab to select the output device
    """

    _output = None
    _update_function = None

    def __init__(self, update_function=None):
        super().__init__("Output Tab")

        self._update_function = update_function

        self._device_select = ControlCombo(
            label="Output Device"
        )

        self._custom = ControlEmptyWidget()

        self._device_select.changed_event = self._on_device_change

        self._device_select.add_item('None', None)

        for class_type in OutputDevice.__subclasses__():
            self._device_select.add_item(class_type.__name__, class_type)

    def _on_device_change(self):
        device = self._device_select.value
        if callable(device):
            self._output = device()
            self._custom.value = self._output.get_custom_config()
        else:
            self._output = None
            self._custom.value = None

        if callable(self._update_function):
            self._update_function({'output': self._output})
