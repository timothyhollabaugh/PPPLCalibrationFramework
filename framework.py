"""
The framework for stepping and scanning axis and measuring the sensor values
"""

import time
from enum import Enum, auto
from abc import ABC, abstractmethod
from PyQt5.QtCore import QTimer
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

    points = None

    _value = 0
    _name = ""
    _type = None

    _max = 0
    _min = 0

    def __init__(self, name):
        self._name = name
        self.points = []

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

    def get_enabled(self):
        """
        Get enabled
        """
        return False

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

    def get_custom_config(self):
        """
        Get the GUI config for this output device
        """
        return None

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
    BEGIN_STEP = 'beginstep'
    WAIT_STEP = 'waitstep'
    BEGIN_MEASURING = 'beginsensor'
    WAIT_MEASURING = 'waitsensor'
    BEGIN_DELAY = 'begindelay'
    WAIT_DELAY = 'waitdelay'
    DONE = 'done'


class AxisController:
    """
    Controls many ControlAxis to scan a grid
    """

    _axis = []
    _sensor = None
    _output = None

    _state = AxisControllerState.BEGIN_STEP

    _step_delay = 0
    _start_delay = 0

    _step = 0
    _timer = QTimer()

    def __init__(self, control_axis, sensor, output, step_delay):
        """
        Creates a new Axis Controller with a list of ControlAxis to control
        :param control_axis: a list of ControlAxis in the order that they should be controlled
        """

        self._axis = control_axis
        self._sensor = sensor
        self._output = output
        self._step_delay = step_delay

    def begin(self):
        """
        Starts scanning
        """
        self._step = 0
        self._state = AxisControllerState.BEGIN_STEP
        self._timer.timeout.connect(self._scan)
        self._timer.start()

    def _scan(self):
        """
        Scans through all of the axis given in the constructor in order
        :return: Nothing
        """

        print("Scanning: ", self._step, self._state.value)

        for axis in self._axis:
            axis.update()

        self._sensor.update()

        # Begin Step
        if self._state == AxisControllerState.BEGIN_STEP:
            done = True
            for axis in self._axis:
                if len(axis.points) > self._step:
                    axis.goto_value(axis.points[self._step])
                    done = False

            if done:
                self._state = AxisControllerState.DONE
            else:
                self._state = AxisControllerState.WAIT_STEP

        # Wait Step
        elif self._state == AxisControllerState.WAIT_STEP:
            done = True
            for axis in self._axis:
                if not axis.is_done():
                    done = False

            if done:
                self._state = AxisControllerState.BEGIN_MEASURING

        # Begin Measuring
        elif self._state == AxisControllerState.BEGIN_MEASURING:
            self._output.set_enabled(True)
            self._sensor.begin_measuring()
            self._state = AxisControllerState.WAIT_MEASURING

        # Wait Measuring
        elif self._state == AxisControllerState.WAIT_MEASURING:
            if self._sensor.is_done():
                self._state = AxisControllerState.BEGIN_DELAY
                self._output.set_enabled(False)

        # Begin Delay
        elif self._state == AxisControllerState.BEGIN_DELAY:
            self._start_delay = time.time()
            self._state = AxisControllerState.WAIT_DELAY

        # Wait Delay
        elif self._state == AxisControllerState.WAIT_DELAY:
            if time.time() - self._start_delay > self._step_delay:
                self._step += 1
                self._state = AxisControllerState.BEGIN_STEP

        elif self._state == AxisControllerState.DONE:
            self._timer.stop()

        cv2.waitKey(1)
