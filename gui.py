"""
Implements a GUI for the calibration
"""
import sys
import pyforms
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlText, ControlCombo, ControlNumber, ControlButton, ControlCheckBoxList, ControlEmptyWidget, ControlLabel, ControlDockWidget, ControlBase, ControlMdiArea
from framework import AxisController
from framework import ControlAxis
import motion
from motion import LinearAxis, RotateAxis
from laser import LaserFequencyAxis, LaserPowerAxis


class ControllerWindow(BaseWidget):
    """
    A window to list the controllers
    """

    _control_axis = []

    def __init__(self):
        super().__init__("Calibration Controller")

        self._control_list = ControlList(
            label="Control List",
            default="Control List 2",
            add_function=self._add_control,
            remove_function=self._remove_control
        )
        
        self._control_panel = ControlDockWidget(
            label="Control Axis"
        )

    def _add_control(self):
        win = ControlWindow(self.add_control)
        win.show()

    def _remove_control(self):
        pass

    def add_control(self, control):
        assert isinstance(control, ControlAxis)
        self._control_axis.append(control)
        self._control_list += [control.get_name(), control.get_value(), control.get_min_value(), control.get_max_value(), control.get_step(), control.get_steps()]

        control_panel = ControlAxisPanel(control)

        #self._control_panel += control_panel

        if self._control_panel.value is None:
            self._control_panel.value = [control_panel, control_panel]
        elif isinstance(self._control_panel.value, list):
            self._control_panel.value = self._control_panel.value.extend(control_panel)
        else:
            self._control_panel.value = [self._control_panel.value, control_panel]
        
        print(control)

class ControlAxisPanel(BaseWidget):
    """
    A Panel that represents a ControlAxis
    """

    def __init__(self, control_axis):
        assert isinstance(control_axis, ControlAxis)
        super().__init__(control_axis.get_name())

        self._control_axis = control_axis

        self._name_field = ControlLabel(
            label=control_axis.get_name()
        )

        self._value_field = ControlLabel(
            label=str(control_axis.get_value())
        )

        self._decrease_button = ControlButton(
            label="<-"
        )

        self._increase_button = ControlButton(
            label="->"
        )

        self._edit_button = ControlButton(
            label="Edit"
        )

        self.formset = [
            "_name_field",
            ("_decrease_button", "_value_field", "_increase_button"),
            "_edit_button"
        ]        

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

        self._type_field.current_index_changed_event = self._on_type_change

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
        self._device_field = ControlEmptyWidget(
            label="Devices"
        )

        self._device_field.changed_event = self._on_device_checked

        # The Done button
        self._done_button = ControlButton(
            label="Done",
        )
        self._done_button.value = self._done

        # The Status Line
        self._status = ControlLabel(
            label=""
        )

        #self._on_type_change(self._type_field.current_index)

    def _on_type_change(self, _):
        axis_type = self._type_field.value
        all_devices = axis_type.get_devices()
        device_widget = DeviceList(all_devices)
        self._device_field.value = device_widget


    def _on_device_checked(self):
        pass

    def _done(self):
        axis_type = self._type_field.value

        devices = self._device_field.value.get_devices()
        devices_needed = axis_type.get_devices_needed()

        print(devices)
        print(len(devices))
        print(devices_needed)
        print(len(devices_needed))
        if len(devices) >= len(devices_needed):
            name = self._name_field.value
            min_value = self._min_field.value
            max_value = self._max_field.value
            steps = self._steps_field.value
            
            axis = axis_type(min_value, max_value, steps, name, devices)

            self._done_function(axis)
            self.close()
        else:
            self._status.value = "Select Devices to use!"
            return

class DeviceList(BaseWidget):
    """
    Lists devices
    """

    def __init__(self, all_devices):
        super().__init__("Devices")

        self._devices = all_devices

        for key, devices in all_devices.items():
            device_list = ControlCheckBoxList(
                label=key
            )
            setattr(self, key, device_list)
            for device in devices:
                setattr(self, key, getattr(self, key) + device[0])

    def get_devices(self):
        """
        Returns the selected devices
        """
        all_devices = {}
        for key, devices in self._devices.items():
            index = getattr(self, key).selected_row_index
            device = devices[index]
            all_devices[key] = device

        return all_devices

try:
    pyforms.start_app(ControllerWindow)
finally:
    motion.cleanup()
