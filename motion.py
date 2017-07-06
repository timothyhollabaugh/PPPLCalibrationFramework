import math
from framework import ControlAxis

class LinearAxis(ControlAxis):
    """
    A ControlAxis to control the mm to the laser
    """

    _linear_stage = None

    def __init__(self, min_value, max_value, steps, linear_stage):
        super().__init__(min_value, max_value, steps)
        self._linear_stage = linear_stage

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

    _rotation_stage = None

    _distance_to_surface = 576.2625
    _ticks_to_level = 8.1
    _ticks_per_revolution = 66

    def __init__(self, min_value, max_value, steps, rotation_stage):
        super().__init__(min_value, max_value, steps)
        self._rotation_stage = rotation_stage

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
