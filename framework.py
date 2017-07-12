"""
The framework for stepping and scanning axis and measuring the sensor values
"""

from enum import Enum, auto
from abc import ABC, abstractmethod
from pyforms import BaseWidget
from pyforms.Controls import ControlCombo, ControlLabel

import cv2

class AxisType(Enum):
    """
    A type of axis as used for movement
    """
    X_Axis = "X Axis"
    Y_Axis = "Y Axis"
    Auxiliary_Axis = "Aux Axis"

class ControlAxis(ABC):

    """
    Controls a single axis used for calibration
    Must be subclassed for each actual axis being used
    """

    _value = 0
    _name = ""
    _type = None

    _max = 0
    _min = 0

    def __init__(self, name):
        self._name = name

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

    def is_done(self):
        """
        Returns whether the axis is done moving
        """
        return True

    def get_custom_config(self):
        """
        Gets a custom pywidgets BaseWidget to display in the axis configuation area of the gui when this axis is selected
        """
        return None

    def set_min(self, min_value):
        """
        Sets the min value
        """
        self._min = min_value

    def set_max(self, max_value):
        """
        Sets the max value
        """
        self._max = max_value

    def get_min(self):
        """
        Gets the min value
        """
        return self._min

    def get_max(self):
        """
        Gets the max value
        """
        return self._max

    def get_value(self):
        """
        Gets the target value
        """
        return self._value

    def get_current_value(self):
        """
        Gets the current value (may not be the target)
        """
        return self._value

    def goto_value(self, value):
        """
        Gots to a specified value, regardless of what the step is
        Returns if successful
        """
        if value < self._min:
            value = self._min

        if value > self._max:
            value = self._max

        self._value = value
        return self._write_value(self._value)

    def goto_home(self):
        """
        Homes the axis to go to the endstop
        """
        self.goto_value(0)

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

class OutputDevice(ABC):
    """
    The thing that gets enabled when measuring
    """

    @abstractmethod
    def set_enabled(self, enable=True):
        """
        Set the output to enabled or disabled
        """
        pass

    def get_custom_config(self):
        """
        Get the GUI config for this output device
        """
        return None

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
