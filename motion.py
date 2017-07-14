"""
ControlAxis for motion control of Thorlabs stages
"""
import math
import thorlabs_apt
from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlCombo, ControlNumber
from framework import ControlAxis


def get_devices():
    """
    Get the thorlabs hardware stages that can be used with LinearAxis and RotateAxis in a tuple
    (human readable name, serial number)
    """
    serial_numbers = thorlabs_apt.list_available_devices()
    devices = []
    for number in serial_numbers:
        info = thorlabs_apt.hardware_info(number[1])
        devices.append(("{} {} S/N: {}".format(info[2].decode(
            "utf - 8"), info[0].decode("utf - 8"), number[1]), number[1]))
    return devices


DEVICES = get_devices()

print("Found Thorlabs APT Devices:")
print(DEVICES)


def cleanup():
    thorlabs_apt.core._cleanup()


class LinearAxis(ControlAxis):
    """
    A ControlAxis to control the mm to the laser
    """

    _linear_stage = None
    _widget = None
    _homing_timer = None

    def get_custom_config(self):
        """
        Gets a pyforms BaseWidget to complete configuration for LinearAxis
        """

        if self._widget is None:
            widget = BaseWidget("Linear Axis Config")

            widget.device_list = ControlCombo(
                label="Device"
            )

            widget.device_list += ('None', None)

            for device in DEVICES:
                widget.device_list += device

            if self._linear_stage is not None:
                widget.value = self._linear_stage.serial_number

                print("Stage:", self._linear_stage.serial_number)
                print("Widget:", widget.value)

            widget.device_list.current_index_changed_event = self._update_stage

            widget.formset = [
                'device_list',
                ''
            ]

            self._widget = widget

            self._update_stage(0)

        if self._linear_stage is not None:
            self._linear_stage.identify()

        return self._widget

    def _update_stage(self, _):
        device = self._widget.device_list.value
        if device is not None and device != 'None':
            print("Update:", device)
            self._linear_stage = thorlabs_apt.Motor(device)
            self._linear_stage.identify()
            self._value = self.get_current_value()
            if not self._linear_stage.has_homing_been_completed:
                self.goto_home()

    def _write_value(self, value):
        if self._linear_stage is not None:
            self._linear_stage.move_to(value)

    def get_current_value(self):
        if self._linear_stage is not None:
            return self._linear_stage.position
        else:
            return self.get_value()

    def _update_homing(self):
        if self.is_done():
            self._write_value(self._value)
            self._homing_timer.stop()
            self._homing_timer = None

    def goto_home(self):
        self._value = 0

        if self._linear_stage is not None:
            self._linear_stage.move_home()

            self._homing_timer = QTimer()
            self._homing_timer.timeout.connect(self._update_homing)
            self._homing_timer.start(500)

    def is_done(self):
        """
        Returns if the stage is done moving
        """
        if self._linear_stage is not None:
            return not self._linear_stage.is_in_motion


class RotateAxis(ControlAxis):
    """
    Axis to control a rotational axis pointed at a surface
    """

    _rotation_stage = None

    _distance_to_surface = 576.2625
    _ticks_to_level = 8.1
    _ticks_per_revolution = 66

    _widget = None

    _homing_timer = None

    def get_custom_config(self):
        """
        Gets a pyforms BaseWidget to complete configuration for RotationAxis
        """

        if self._widget is None:
            widget = BaseWidget("Rotate Axis Config")

            widget.device_list = ControlCombo(
                label="Device"
            )

            widget.device_list += ('None', None)

            for device in DEVICES:
                widget.device_list += device

            if self._rotation_stage is not None:
                widget.value = self._rotation_stage.serial_number

            widget.device_list.current_index_changed_event = self._update_stage

            widget.distance_field = ControlNumber(
                label="Distance to Surface",
                default=1,
                minimum=0,
                maximum=float('inf'),
                decimals=5
            )

            widget.distance_field.key_pressed_event = self._update_distance_to_surface

            widget.formset = [
                'device_list',
                'distance_field',
                ''
            ]

            self._widget = widget

            self._update_stage(0)

        if self._rotation_stage is not None:
            self._rotation_stage.identify()

        return self._widget

    def _update_distance_to_surface(self):
        self._distance_to_surface = self._widget.distance_field.value

    def _update_stage(self, _):
        if not self._widget.device_list.value is None and self._widget.device_list.value != 'None':
            self._rotation_stage = thorlabs_apt.Motor(
                self._widget.device_list.value)
            self._rotation_stage.identify()
            self._value = self.get_current_value()
            if not self._rotation_stage.has_homing_been_completed:
                self.goto_home()

    def _write_value(self, value):
        if self._rotation_stage is not None:
            self._rotation_stage.move_to(self._distance_to_angle(value))

    def _distance_to_angle(self, distance):
        return (self._ticks_to_level
                + math.atan(distance / self._distance_to_surface)
                * self._ticks_per_revolution
                / (2 * math.pi))

    def _angle_to_distance(self, angle):
        return (self._distance_to_surface\
                * math.tan(
                    (angle - self._ticks_to_level)
                    * (2 * math.pi)
                    / self._ticks_per_revolution))

    def get_current_value(self):
        if self._rotation_stage is not None:
            return self._angle_to_distance(self._rotation_stage.position)
        else:
            return self.get_value()

    def _update_homing(self):
        if self.is_done():
            self._write_value(self._value)
            self._homing_timer.stop()
            self._homing_timer = None

    def goto_home(self):
        self._value = 0
        if self._rotation_stage is not None:
            self._rotation_stage.move_home()

            self._homing_timer = QTimer()
            self._homing_timer.timeout.connect(self._update_homing)
            self._homing_timer.start(500)

    def is_done(self):
        """
        Returns if the stage is done moving
        """
        if self._rotation_stage is not None:
            return not self._rotation_stage.is_in_motion
        else:
            return False
