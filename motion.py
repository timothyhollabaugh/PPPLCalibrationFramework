"""
ControlAxis for motion control of Thorlabs stages
"""
import math
import thorlabs_apt
from framework import ControlAxis


def get_devices():
    """
    Get the thorlabs hardware stages that can be used with LinearAxis and RotateAxis in a tuple
    (human readable name, serial number)
    """
    serial_numbers = thorlabs_apt.list_available_devices()
    devices = {"Stage": []}
    for number in serial_numbers:
        info = thorlabs_apt.hardware_info(number[1])
        devices["Stage"].append(( "{} {} S / N: {}".format(info[2].decode("utf - 8"), info[0].decode("utf - 8"), number[1]), number[1]))
    return devices

def cleanup():
    thorlabs_apt.core._cleanup()

class LinearAxis(ControlAxis):
    """
    A ControlAxis to control the mm to the laser
    """

    _linear_stage=None

    @staticmethod
    def get_devices():
        """
        Returns a list of Thorlabs motion stages that can be used
        """
        return get_devices()

    def set_devices(self, devices):
        """
        Sets the thorlabs stage used for this axis
        """
        if 'Stage' in devices and not devices['Stage'] is None:
            self._linear_stage=thorlabs_apt.Motor(devices['Stage'][1])
            return True
        else:
            return False

    @staticmethod
    def get_devices_needed():
        """
        Returns the number of thorlabs stages needed for this axis
        """
        return ["Stage"]

    def _write_value(self, value):
        self._linear_stage.move_to(value)
        print("Setting linear position to: {}".format(value))

    def is_done(self):
        """
        Returns if the stage is done moving
        """
        return not self._linear_stage.is_in_motion


class RotateAxis(ControlAxis):
    """
    Axis to control a rotational axis pointed at a surface
    """

    _rotation_stage=None

    _distance_to_surface=576.2625
    _ticks_to_level=8.1
    _ticks_per_revolution=66

    @staticmethod
    def get_devices():
        """
        Returns a list of Thorlabs motion stages that can be used
        """
        return get_devices()

    def set_devices(self, devices):
        """
        Sets the thorlabs stage used for this axis
        """
        if 'Stage' in devices and not devices['Stage'] is None:
            self._linear_stage=thorlabs_apt.Motor(devices['Stage'][1])
            return True
        else:
            return False

    @staticmethod
    def get_devices_needed():
        """
        Returns the number of thorlabs stages needed for this axis
        """
        return ["Stage"]

    def _write_value(self, value):
        self._rotation_stage.move_to(self._distance_to_angle(value))
        print("Setting rotation position to: {}".format(value))

    def _distance_to_angle(self, distance):
        return self._ticks_to_level \
            + math.atan(distance / self._distance_to_surface) \
            * self._ticks_per_revolution \
            / (2 * math.pi) 

    def is_done(self):
        """
        Returns if the stage is done moving
        """
        return not self._rotation_stage.is_in_motion
