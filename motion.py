import math
from framework import ControlAxis

class LinearAxis(ControlAxis):
    """
    A ControlAxis to control the mm to the laser
    """

    linear = None

    steps = 0
    step_mm = 0
    start_mm = 0

    current_step = 0
    current_mm = 0

    def __init__(self, linear, steps, step_mm, start_mm):
        """
        Create a LaserPowerAxis
        :param linear: The stage to control
        :param steps: The number of steps to step through
        :param step_mm: The mm per step
        :param start_mm: The mm to start the first step at
        """

        self.linear = linear

        self.steps = steps
        self.step_mm = step_mm
        self.start_mm = start_mm

        self.current_step = 0
        self.current_mm = self.start_mm

        linear.move_home(True)

    def get_current_step(self):
        return self.current_step

    def get_current_value(self):
        return self.current_mm

    def goto_step(self, step):
        pass

    def goto_value(self, value):
        pass

    def first_step(self):
        """
        Move to the first step
        :return: nothing
        """
        self.current_step = 0
        self.current_mm = self.start_mm
        self.next_step()

    def next_step(self):
        """
        Move to the next step, and rolls back to the first if it hits the end
        :return: Whether the next step will go back to the beginning
        """
        print("Linear move step {0}".format(self.current_step))
        self.linear.move_to(self.current_mm, blocking=True)

        self.current_step += 1
        self.current_mm += self.step_mm

        if self.current_step >= self.steps:
            self.current_step = 0
            self.current_mm = self.start_mm

        return self.current_step == 1


class RotateAxis(ControlAxis):
    """
    Axis to control a rotational axis pointed at a surface
    """

    rotate = None

    steps = 0
    step_mm = 0
    start_mm = 0

    current_step = 0
    current_mm = 0
    current_angle = 0

    mm_to_surface = 1
    ticks_to_level = 8.01
    ticks_per_revolution = 66

    def __init__(self, rotate, steps, step_mm, start_mm, mm_to_surface):
        """
        Create a LaserPowerAxis
        :param rotate: The stage to control
        :param steps: The number of steps to step through
        :param step_mm: The mm per step
        :param start_mm: The mm to start the first step at
        """

        self.rotate = rotate

        self.steps = steps
        self.step_mm = step_mm
        self.start_mm = start_mm

        self.current_step = 0
        self.current_mm = self.start_mm

        self.mm_to_surface = mm_to_surface

        rotate.move_home(True)
        rotate.move_to(self.ticks_to_level, True)

    def first_step(self):
        """
        Move to the first step
        :return: nothing
        """
        self.current_step = 0
        self.current_mm = self.start_mm
        self.current_angle = self.mm_angle(self.current_mm)
        self.next_step()

    def next_step(self):
        """
        Move to the next step, and rolls back to the first if it hits the end
        :return: Whether the next step will go back to the beginning
        """
        print("Rotate move step {0}".format(self.current_step))
        self.rotate.move_to(self.current_angle + self.ticks_to_level, blocking=True)

        self.current_step += 1
        self.current_mm += self.step_mm
        self.current_angle = self.mm_angle(self.current_mm)

        if self.current_step >= self.steps:
            self.current_step = 0
            self.current_mm = self.start_mm
            self.current_angle = self.mm_angle(self.current_mm)

        return self.current_step == 1

    def mm_angle(self, mm):
        return math.atan(mm / self.mm_to_surface) * self.ticks_per_revolution / (2 * math.pi)
