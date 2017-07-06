import time
from framework import ControlAxis


class Laser:
    """
    Controls the laser and holds the LaserPowerAxis and Laser Frequency Axis
    """

    power_resource = None
    signal_resource = None

    power_channel = 0

    enabled_voltage = 8
    disabled_voltage = 0
    max_current = 0.5

    off_signal = -0.7

    offset = off_signal
    frequency = 1
    enabled = False

    def __init__(self, power_resource, power_channel, signal_resource):
        """
        Create a Laser
        :param power_resource: The pyvisa resource for the laser power supply (Must be a GPD-4303S for now)
        :param power_channel: The channel on the power supply to use
        :param signal_resource: The pyvisa resource for the laser signal generator (Must be an AFG-3021 for now)
        """

        self.power_resource = power_resource
        self.power_channel = power_channel
        self.signal_resource = signal_resource

        # Turn on the outputs
        self.power_resource.write('OUT1')

        # Set the voltage to 8 volts
        self.power_resource.write('VSET{0}:8'.format(self.power_channel))

        # Set the current to 0.5 amps
        self.power_resource.write('ISET{0}:0.5'.format(self.power_channel))

        # Turn on the signal
        self.signal_resource.write('OUTPUT ON')

        self.update_laser()
    
    def __del__(self):
        self.enabled = False
        self.offset = self.off_signal
        self.update_laser()

    def update_laser(self):
        if self.enabled:
            self.signal_resource.write("SOURCE1:APPLY:SQUARE {0}HZ,{1},{2}".format(self.frequency, 1.1, self.offset))
        else:
            self.signal_resource.write("SOURCE1:APPLY:SQUARE {0}HZ,{1},{2}".format(self.frequency, 1.1, self.off_signal))

    def set_enabled(self, enable=True):
        """
        Enables or disables the power supply
        :param enable: Enables if True, disables if false
        :return: nothing
        """
        self.enabled = enable
        time.sleep(0.1)
        self.update_laser()

    def set_frequency(self, frequency):
        """
        Sets the frequency to pulse the laser at
        :param frequency: The frequency in hertz
        :return: nothing
        """
        self.frequency = frequency
        self.update_laser()

    def set_power(self, power):
        """
        Sets the power to the laser by adjusting the amplitude and DC offset of the signal
        :param power: The power to apply between 0.0 and 1.0
        :return: nothing
        """
        self.offset = power * -self.off_signal + self.off_signal
        self.update_laser()


class LaserPowerAxis(ControlAxis):
    """
    A ControlAxis to control the power to the laser
    """

    laser = None

    steps = 0
    step_power = 0
    start_power = 0

    current_step = 0
    current_power = 0

    def __init__(self, laser, steps, step_power, start_power):
        """
        Create a LaserPowerAxis
        :param laser: The Laser to control
        :param steps: The number of steps to step through
        :param step_power: The power per step
        :param start_power: The power to start the first step at
        """

        self.laser = laser

        self.steps = steps
        self.step_power = step_power
        self.start_power = start_power

        self.current_step = 0
        self.current_power = self.start_power

    def get_current_step(self):
        return self.current_step

    def get_current_value(self):
        return self.current_power

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
        self.current_power = self.start_power
        self.next_step()

    def next_step(self):
        """
        Move to the next step, and rolls back to the first if it hits the end
        :return: Whether this was the first step (the previous step rolled over)
        """

        print("Laser Power Step {0}".format(self.current_step))
        self.laser.set_power(self.current_power)

        self.current_step += 1
        self.current_power += self.step_power

        if self.current_step >= self.steps:
            self.current_step = 0
            self.current_power = self.start_power

        return self.current_step == 1

class LaserFequencyAxis(ControlAxis):
    """
    A ControlAxis to control the frequency to the laser
    """

    laser = None

    steps = 0
    step_frequency = 0
    start_frequency = 0

    current_step = 0
    current_frequency = 0

    def __init__(self, laser, steps, step_frequency, start_frequency):
        """
        Create a LaserPowerAxis
        :param laser: The Laser to control
        :param steps: The number of steps to step through
        :param step_frequency: The frequency per step
        :param start_frequency: The frequency to start the first step at
        """

        self.laser = laser

        self.steps = steps
        self.step_frequency = step_frequency
        self.start_frequency = start_frequency

        self.current_step = 0
        self.current_frequency = self.start_frequency

    def get_current_step(self):
        return self.current_step

    def get_current_value(self):
        return self.current_frequency

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
        self.current_frequency = self.start_frequency
        self.next_step()

    def next_step(self):
        """
        Move to the next step, and rolls back to the first if it hits the end
        :return: Whether the next step will go back to the beginning
        """

        print("Laser Frequency Step {0}".format(self.current_step))
        self.laser.set_frequency(self.current_frequency)

        self.current_step += 1
        self.current_frequency += self.step_frequency

        if self.current_step >= self.steps:
            self.current_step = 0
            self.current_frequency = self.start_frequency

        return self.current_step == 1
