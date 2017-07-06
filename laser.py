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
        """
        Updates the laser to current power, frequency, and enabled
        """
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

    _laser = None

    def __init__(self, minValue, maxValue, steps, laser):
        super().__init__(minValue, maxValue, steps)
        self._laser = laser

    def _write_value(self, value):
        self._laser.set_power(value)
        print("Setting laser power to: {}".format(value))

class LaserFequencyAxis(ControlAxis):
    """
    A ControlAxis to control the frequency to the laser
    """

    _laser = None

    def __init__(self, minValue, maxValue, steps, laser):
        super().__init__(minValue, maxValue, steps)
        self._laser = laser

    def _write_value(self, value):
        self._laser.set_frequency(value)
        print("Setting laser frequency to: {}".format(value))
