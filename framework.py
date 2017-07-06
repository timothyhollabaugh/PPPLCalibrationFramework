from abc import ABC, abstractmethod
import time

class ControlAxis(ABC):

    """
    Controls a single axis used for calibration
    Must be subclassed for each actual axis being used
    """

    def __init__(self, steps, steps)

    @abstractmethod
    def get_name(self):
        """
        Get the human readable name of this axis
        """
        pass

    @abstractmethod
    def get_current_step(self):
        """
        Get the current step
        """
        pass

    @abstractmethod
    def get_current_value(self):
        """
        Get the current value
        """
        pass

    @abstractmethod
    def goto_step(self, step):
        """
        Go to a step
        """
        pass

    @abstractmethod
    def goto_value(self, value):
        """
        Go to a value
        """
        pass

    @abstractmethod
    def next_step(self):
        """
        Moves to the next step
        After the last step, it should roll over to the first step
        :return: True if this is not the last step, False if it is the last step
        """
        pass

    @abstractmethod
    def first_step(self):
        """
        Goes to the first step and resets to that state
        :return: nothing
        """

class Sensor(ABC):

    """
    The thing that is being calibrated
    """

    @abstractmethod
    def measure(self):
        pass


class AxisController:
    """
    Controls many ControlAxis to scan a grid
    """

    control_axis = []

    sensor = None

    def __init__(self, control_axis, sensor):
        """
        Creates a new Axis Controller with a list of ControlAxis to control
        :param control_axis: a list of ControlAxis in the order that they should be controlled
        """
    
        self.control_axis = control_axis
        self.sensor = sensor

    def add_control_axis(self, control_axis):
        """
        Adds a control axis to the list of axis to control
        :param control_axis: a ControlAxis to add
        :return: Nothing
        """
        self.control_axis.append(control_axis)

    def get_control_axis(self):
        """
        Gets the list of control axis
        :return: Nothing
        """
        return self.control_axis

    def set_sensor(self, sensor):
        """
        Set the sensor that is being calibrated
        :param sensor: The Sensor that is being calibrated
        :reutrn: Noting
        """
        self.sensor = sensor

    def get_sensor(self):
        """
        Get the sensor being calibrated
        :return: The Sensor being calibrated
        """
        return self.sensor

    def scan(self):
        """
        Scans through all of the axis given in the constructor in order
        :return: Nothing
        """

        for axis in self.control_axis:
            axis.first_step()

        done = False

        while not done:

            self.sensor.measure()
            time.sleep(0.5)

            done = True
            for axis in self.control_axis:
                if not axis.next_step():
                    done = False
                    break
