"""
The framework for stepping and scanning axis and measuring the sensor values
"""

import time
import csv
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

    An Axis is anything that gets changed while scanning.
    For example, The X/Y Axis of an area, the power of the laser, etc

    Each Axis has a list of points it goes to
    There should be the same number of points in every axis

    Must be subclassed for each actual axis being used
    Any subclasses that are imported into main.py will show up in the drop downs

    The _write_value(self, value) method must be overrided in the subclass to actually move the axis
    Everything else can be overrided if needed
    """

    points = None

    _value = 0
    _string_value = "0.0"
    _name = ""
    _type = None

    _max = 0
    _min = 0

    _norm_min = 0
    _norm_max = 1

    _saved_points = {}

    def __init__(self, name):
        self._name = name
        self.points = []

    # This method **must** be overrided in subclasses
    @abstractmethod
    def _write_value(self, value):
        """
        Write the value to the physical device
        Returns whether the write was successful
        """
        pass

    # These can be overrided if needed
    def update(self):
        """
        Gets called very quickly repeatedly while scanning
        """
        pass

    def is_done(self):
        """
        Returns whether the axis is done moving. Also gets called quickely while scanning
        """
        return True

    def get_custom_config(self):
        """
        Gets a custom pywidgets BaseWidget to display in the axis configuation area of the gui when this axis is selected
        """
        return None

    def goto_home(self):
        """
        Homes the axis to go to the endstop
        """
        self.goto_value(0)

    def update_events(self, events):
        """
        Call with new events when available
        """
        #print("Axis", events)
        if 'saved_points' in events:
            self._saved_points = events['saved_points']

    # These methods should not be overrided unless absolutly required
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

    def set_norm_min(self, min_value):
        """
        Sets the norm_min value
        """
        self._norm_min = min_value

    def set_norm_max(self, max_value):
        """
        Sets the norm_max value
        """
        self._norm_max = max_value

    def get_norm_min(self):
        """
        Gets the norm_min value
        """
        return self._norm_min

    def get_norm_max(self):
        """
        Gets the norm_max value
        """
        return self._norm_max

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

    def get_string_value(self):
        """
        Gets the current value as it was set (keep saved point names and percents)
        """
        return self._string_value

    def goto_value(self, value):
        """
        Gots to a specified value, clipping to the min and max
        Name of saved point => resolve value of saved point
        Number (54) => go to value with world units
        Percent (27%) => Go to normalized value
        Returns if successful
        """

        done_value, is_string = self.resolve_point(value)

        self._value = done_value

        if is_string:
            self._string_value = str(value)
        else:
            self._string_value = str(done_value)

        return self._write_value(done_value)

    def resolve_point(self, value):
        """
        Resovle a point in the form of a number, percent, or saved point into an actual point value
        """

        #print(value)

        working_value = str(value)
        done_value = None

        is_string = False

        try:
            # Try to convert to number immediately
            #print("Trying to convert", working_value, "to float")

            done_value = float(working_value)

            is_string = False

        except ValueError:
            assert isinstance(working_value, str)

            is_string = True

            # Resolve saved points to values
            if working_value in self._saved_points:
                working_value = self._saved_points[working_value]
                #print("Resolved to saved point")

            try:
                #print("Trying again to convert", working_value, "to float")

                if working_value.endswith('%'):
                    # Percent value
                    working_value = float(working_value[:-1])
                    done_value = (working_value / 100) * \
                        (self._norm_max - self._norm_min) + self._norm_min
                else:
                    done_value = float(working_value)

            except ValueError:
                #print("Could not convert", value, "to float")
                return
            

        # Clamp the actual value sent to device
        if done_value < self._min:
            done_value = self._min

        if done_value > self._max:
            done_value = self._max

        return done_value, is_string

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

    def get_units(self):

        """
        Return a string of the units used for this axis
        """
        return ""


class LightSource(ABC):
    """
    The thing that gets enabled when measuring

    This class must be subclassed for each lightsource device
    """

    @abstractmethod
    def set_enabled(self, enable=True):
        """
        Set the lightsource to enabled or disabled
        """
        pass

    def get_enabled(self):
        """
        Get enabled
        """
        return False

    def get_custom_config(self):
        """
        Get the GUI config for this lightsource device
        """
        return None


class Sensor:

    """
    The thing that is being calibrated

    This must be subclasses for each sensor
    """

    def get_custom_config(self):
        """
        Get the GUI config for this lightsource device
        """
        return None

    def update(self):
        """
        Gets called repeatedly while scanning
        Should return the most recent measurements
        """
        return []

    def begin_measuring(self):
        """
        Begin measuring during update()
        """
        pass

    def is_done(self):
        """
        Returns whether the sensor is done measuring
        """
        return True

    def get_headers(self):
        """
        Gets the headers for the data returned
        """
        return []

    def update_events(self, events):
        """
        Updates any events sent out
        """
        pass


class AxisControllerState(Enum):
    """
    The state for the AxisController
    """
    BEGIN_STEP = 'beginstep'
    WAIT_STEP = 'waitstep'
    BEGIN_ENABLE = 'beginsensor'
    WAIT_ENABLE = 'waitsensor'
    BEGIN_PRE_DELAY = 'beginpredelay'
    WAIT_PRE_DELAY = 'waitpredelay'
    BEGIN_POST_DELAY = 'beginpostdelay'
    WAIT_POST_DELAY = 'waitpostdelay'
    DONE = 'done'


class AxisController:
    """
    Controls many ControlAxis to scan a grid
    """

    _axis = []
    _sensor = None
    _lightsource = None

    _state = AxisControllerState.DONE

    _pre_delay = 0
    _post_delay = 0
    _start_delay = 0

    _saved_points = None

    _data = []

    _measuring = False

    _outfile = None

    _update_function = None

    _step = 0
    _total_steps = 0
    _timer = QTimer()

    def __init__(self, control_axis, sensor, lightsource, pre_delay, post_delay, saved_points=None, outfile=None, update_function=None):
        """
        Creates a new Axis Controller with a list of ControlAxis to control
        :param control_axis: a list of ControlAxis in the order that they should be controlled
        """

        self._axis = control_axis
        self._sensor = sensor
        self._lightsource = lightsource
        self._pre_delay = pre_delay
        self._post_delay = post_delay
        self._saved_points = saved_points
        self._outfile = outfile
        self._update_function = update_function

    def begin(self):
        """
        Starts scanning
        """
        if self._lightsource is not None:
            self._lightsource.set_enabled(False)
        self._step = 0
        self._total_steps = len(self._axis[0].points)

        headers = []

        headers.append("Time")

        for axis in self._axis:
            headers.append(axis)

        if isinstance(self._sensor, Sensor):
            headers.extend(self._sensor.get_headers())

        if isinstance(self._lightsource, LightSource):
            headers.append("Light Source Enabled")

        self._set_state(AxisControllerState.BEGIN_STEP)
        self._timer.timeout.connect(self._scan)
        self._timer.start()

    def stop(self):
        """
        Stops the current scan
        """
        self._timer.stop()
        self._set_state(AxisControllerState.DONE)
        if self._lightsource is not None:
            self._lightsource.set_enabled(False)

    def get_state(self):
        """
        Gets the current state
        """
        return self._state

    def _set_state(self, state):
        self._state = state
        if self._update_function is not None:
            self._update_function(
                {'scan': (self._state, self._step, self._total_steps)})

    def _scan(self):
        """
        Scans through all of the axis given in the constructor in order
        :return: Nothing
        """

        if (self._state == AxisControllerState.BEGIN_PRE_DELAY
                or self._state == AxisControllerState.WAIT_PRE_DELAY
                or self._state == AxisControllerState.BEGIN_ENABLE
                or self._state == AxisControllerState.WAIT_ENABLE
                or self._state == AxisControllerState.BEGIN_POST_DELAY
                or self._state == AxisControllerState.WAIT_POST_DELAY):
            datarow = [float(time.time())]
            for axis in self._axis:
                datarow.append(axis.get_current_value())

            if self._sensor is not None:
                datarow += self._sensor.update()

            if self._lightsource is not None:
                datarow += [1.0] if self._lightsource.get_enabled() else [0.0]

            self._data.append(datarow)

        # Begin Step
        if self._state == AxisControllerState.BEGIN_STEP:
            print("Moving to step:", self._step)
            done = True
            for axis in self._axis:
                if len(axis.points) > self._step:
                    value = axis.points[self._step]
                    axis.goto_value(value)
                    done = False

            if done:
                self._set_state(AxisControllerState.DONE)
            else:
                self._set_state(AxisControllerState.WAIT_STEP)

        # Wait Step
        elif self._state == AxisControllerState.WAIT_STEP:
            print('.', end='')
            done = True
            for axis in self._axis:
                if not axis.is_done():
                    done = False

            if done:
                print()
                self._set_state(AxisControllerState.BEGIN_PRE_DELAY)

        # Begin Pre Delay
        elif self._state == AxisControllerState.BEGIN_PRE_DELAY:
            print("Pre Delay")
            self._start_delay = time.time()
            self._set_state(AxisControllerState.WAIT_PRE_DELAY)

        # Wait Pre Delay
        elif self._state == AxisControllerState.WAIT_PRE_DELAY:
            print('.', end='')
            if time.time() - self._start_delay > self._pre_delay:
                print()
                self._set_state(AxisControllerState.BEGIN_ENABLE)

        # Begin Measuring
        elif self._state == AxisControllerState.BEGIN_ENABLE:
            print("Taking measurement")

            if self._lightsource is not None:
                self._lightsource.set_enabled(True)

            if self._sensor is not None:
                self._sensor.begin_measuring()

            self._set_state(AxisControllerState.WAIT_ENABLE)

        # Wait Measuring
        elif self._state == AxisControllerState.WAIT_ENABLE:
            print('.', end='')

            if self._sensor is None or self._sensor.is_done():
                print()

                self._set_state(AxisControllerState.BEGIN_POST_DELAY)
                if self._lightsource is not None:
                    self._lightsource.set_enabled(False)

        # Begin Post Delay
        elif self._state == AxisControllerState.BEGIN_POST_DELAY:
            print("Post Delay")
            self._start_delay = time.time()
            self._set_state(AxisControllerState.WAIT_POST_DELAY)

        # Wait Post Delay
        elif self._state == AxisControllerState.WAIT_POST_DELAY:
            print('.', end='')
            if time.time() - self._start_delay > self._post_delay:
                print()
                self._step += 1
                self._set_state(AxisControllerState.BEGIN_STEP)

        elif self._state == AxisControllerState.DONE:
            print("Done.")

            if self._outfile is not None and self._outfile is not '':
                with open(self._outfile, 'w', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                    csvwriter.writerows(self._data)

            self._timer.stop()
