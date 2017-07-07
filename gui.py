"""
Implements a GUI for the calibration
"""
import sys
import pyforms
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlText, ControlCombo, ControlNumber, ControlButton, ControlCheckBoxList
from framework import AxisController
from framework import ControlAxis
from motion import LinearAxis, RotateAxis
from laser import LaserFequencyAxis, LaserPowerAxis


class ControllerWindow(BaseWidget):
    """
    A window to list the controllers
    """

    def __init__(self):
        super().__init__("Calibration Controller")

        self._control_list = ControlList(
            label="Control List",
            default="Control List 2",
            add_function=self._add_control,
            remove_function=self._remove_control
        )

    def _add_control(self):
        win = ControlWindow(self.add_control)
        win.show()

    def _remove_control(self):
        pass
    
    def add_control(self, control):
        print(control)

class ControlWindow(BaseWidget):
    """
    A window for a ControlAxis
    """

    def __init__(self, done_function, control_axis=None):
        if not control_axis is None:
            assert isinstance(control_axis, ControlAxis)
        assert callable(done_function)

        super().__init__("Control Axis")

        self._control_axis = control_axis
        self._done_function = done_function

        # The name of the axis
        self._name_field = ControlText(
            label="Name"
        )

        # The class that the axis uses
        self._type_field = ControlCombo(
            label="Type"
        )

        for class_type in ControlAxis.__subclasses__():
            self._type_field.add_item(class_type.__name__, class_type)

        # The min_value
        self._min_field = ControlNumber(
            label="Minimum Value",
            default=0 if self._control_axis is None else self._control_axis.get_min_value(),
            minimum=-sys.float_info.max,
            maximum=sys.float_info.max,
        )

        # The max_value
        self._max_field = ControlNumber(
            label="Maximum Value",
            default=1 if self._control_axis is None else self._control_axis.get_max_value(),
            minimum=-sys.float_info.max,
            maximum=sys.float_info.max,
        )

        # The number of steps
        self._steps_field = ControlNumber(
            label="Steps",
            default=1 if self._control_axis is None else self._control_axis.get_steps(),
            minimum=-sys.float_info.max,
            maximum=sys.float_info.max,
        )

        # The device list
        self._device_field = ControlCheckBoxList(
            label="Devices"
        )

        # The Done button
        self._done_button = ControlButton(
            label="Done",
        )
        self._done_button.value = self._done

    def _done(self):
        self._done_function(None)
        self.close()

pyforms.start_app(ControllerWindow)
