"""
The framework for stepping and scanning axis and measuring the sensor values
"""

from abc import ABC, abstractmethod
from enum import Enum, auto

import cv2


class ControlAxis(ABC):

    """
    Controls a single axis used for calibration
    Must be subclassed for each actual axis being used
    """

    _step = -1
    _value = 0
    _min_value = 0
    _max_value = 0
    _steps = 0
    _name = ""

    def __init__(self, min_value, max_value, steps, name, devices):
        self._step = -1
        self._value = min_value
        self._min_value = min_value
        self._max_value = max_value
        self._steps = steps
        self._name = name
        self.set_devices(devices)

    @staticmethod
    @abstractmethod
    def get_devices():
        """
        Return a list of available hardware devices that can be used
        The devices are in a tuple of
        (name, identifier)
        The name is shown to the user
        """
        pass

    @abstractmethod
    def set_devices(self, devices):
        """
        Set the devices used by this axis
        """
        pass

    @staticmethod
    @abstractmethod
    def get_devices_needed():
        """
        Return the number of devices needed
        """
        pass

    @abstractmethod
    def _write_value(self, value):
        """
        Write the value to the physical device
        Returns whether the write was successful
        """
        pass

    def update(self):
        """
        Gets called very quickly repeatedly while scanning
        """
        pass

    def get_value_per_step(self):
        """
        Returns the value that gets moved per step
        """
        return (self._max_value - self._min_value) / self._steps

    def get_step(self):
        """
        Gets the current step that this axis is at
        """
        return self._step

    def goto_step(self, step):
        """
        Goes to a specified step
        Returns whether the move was successful
        """
        if step >= 0 and step < self._steps:
            self._step = step
            return self.goto_value(self._min_value + step * self.get_value_per_step())
        else:
            print("goto_step {} failed! {}".format(step, type(self).__name__))
            return False

    def is_done(self):
        """
        Returns whether the axis is done moving
        """
        return True

    def get_value(self):
        """
        Gets the current value that this axis is at
        """
        return self._value

    def goto_value(self, value):
        """
        Gots to a specified value, regardless of what the step is
        Returns if successful
        """
        if value <= self._max_value and value >= self._min_value:
            self._value = value
            return self._write_value(self._value)
        else:
            print("goto_value {} failed! {}".format(value, type(self).__name__))
            return False

    def get_min_value(self):
        """
        Gets the current min value
        """
        return self._min_value

    def set_min_value(self, min_value, move_to=False):
        """
        Gets the new minimum value and optionally moves to
        it and sets the step to 0 if the current value is now too low
        """
        self._min_value = min_value
        if move_to:
            self.goto_value(min_value)
            self._step = 0

    def get_max_value(self):
        """
        Gets the current max value
        """
        return self._max_value

    def set_max_value(self, max_value, move_to=False):
        """
        Gets the new maximum value and optionally moves to
        it and sets the step to 0 if the current value is now too low
        """
        self._max_value = max_value
        if move_to:
            self.goto_value(max_value)
            self._step = 0

    def get_steps(self):
        """
        Get the number of steps
        """
        return self._steps

    def set_steps(self, steps):
        """
        Set the number of steps
        """
        self._steps = steps

    def reset(self):
        """
        Resets axis to not scanning
        """
        self._step = -1

    def get_name(self):
        """
        Gets the name of this axis
        """
        return self._name

    def set_name(self, name):
        """
        Sets the name of this axis
        """
        self._name = name


class Sensor(ABC):

    """
    The thing that is being calibrated
    """

    _measuring = False

    def update(self):
        """
        Gets called repeatedly while scanning
        """
        self._measuring = False

    def begin_measuring(self):
        """
        Begin measuring during update()
        """
        self._measuring = True

    def is_done(self):
        """
        Returns whether the sensor is done measuring
        """
        return not self._measuring


class AxisControllerState(Enum):
    """
    The state for the AxisController
    """
    START = auto()
    START_WAIT = auto()
    BEGIN_STEP = auto()
    WAIT_STEP = auto()
    NEXT_AXIS = auto()
    BEGIN_MEASURING = auto()
    WAIT_MEASURING = auto()
    DONE = auto()


class AxisController:
    """
    Controls many ControlAxis to scan a grid
    """

    _control_axis = []
    _sensor = None

    _current_axis_index = 0
    _state = AxisControllerState.START

    _step_delay = 0

    def __init__(self, control_axis, sensor, step_delay):
        """
        Creates a new Axis Controller with a list of ControlAxis to control
        :param control_axis: a list of ControlAxis in the order that they should be controlled
        """

        self._control_axis = control_axis
        self._sensor = sensor
        self._step_delay = step_delay

    def scan(self):
        """
        Scans through all of the axis given in the constructor in order
        :return: Nothing
        """

        for axis in self._control_axis:
            axis.update()

        self._sensor.update()

        # Start
        if self._state == AxisControllerState.START:
            for axis in self._control_axis:
                axis.goto_step(0)

            self._state = AxisControllerState.START_WAIT

        # Start Wait
        elif self._state == AxisControllerState.START_WAIT:
            done = True
            for axis in self._control_axis:
                if not axis.is_done():
                    done = False

            if done:
                self._state = AxisControllerState.BEGIN_MEASURING

        # Begin Step
        elif self._state == AxisControllerState.BEGIN_STEP:
            axis = self._control_axis[self._current_axis_index]

            print("Stepping Axis {}".format(type(axis).__name__))

            next_step = axis.get_step() + 1

            if next_step < axis.get_steps():
                print("Axis Stepped")
                axis.goto_step(next_step)
                self._current_axis_index = 0
                self._state = AxisControllerState.WAIT_STEP
            else:
                print("Axis did not step")
                axis.goto_step(0)
                self._state = AxisControllerState.NEXT_AXIS

        # Wait Step
        elif self._state == AxisControllerState.WAIT_STEP:
            done = True
            for axis in self._control_axis:
                if not axis.is_done():
                    done = False

            if done:
                self._state = AxisControllerState.BEGIN_MEASURING

        # Next Axis
        elif self._state == AxisControllerState.NEXT_AXIS:
            next_index = self._current_axis_index + 1

            #print("Current index {0}, next index {1}".format(self._current_axis_index, next_index))

            if next_index < len(self._control_axis):
                #print("Moving to next axis")
                self._current_axis_index = next_index
                self._state = AxisControllerState.BEGIN_STEP
            else:
                print("Done Scanning")
                return True

        # Begin Measuring
        elif self._state == AxisControllerState.BEGIN_MEASURING:
            self._sensor.begin_measuring()
            self._state = AxisControllerState.WAIT_MEASURING

        # Wait Measuring
        elif self._state == AxisControllerState.WAIT_MEASURING:
            if self._sensor.is_done():
                self._state = AxisControllerState.BEGIN_STEP

        elif self._state == AxisControllerState.DONE:
            for axis in self._control_axis:
                axis.reset()

        cv2.waitKey(1)

        return False
