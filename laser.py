"""
ControlAxis for use with a laser controlled by a power supply and a signal generator
"""
import time
import visa
from visa import VisaIOError
from framework import ControlAxis

LASERS = []


def get_devices():
    """
    Gets pyvisa resources to be used for a laser
    """
    resource_manager = visa.ResourceManager()
    resources = resource_manager.list_resources()

    devices = []

    for laser in LASERS:
        power_supply = laser.get_power_supply().query("*IDN?")
        signal_generator = laser.get_signal_generator().query("*IDN?")
        devices.append(("Laser PS {} SG {}".format(
            power_supply, signal_generator), laser))

    for resource in resources:

        found_laser = None

        # Look for this resource in lasers already defined
        for laser in LASERS:
            assert isinstance(laser, Laser)
            if laser.get_power_supply().resource_info[0].resource_name == resource \
                    or laser.get_signal_generator().resource_info[0].resource_name == resource:
                found_laser = laser
                break

        # If found, we do not want to use it again
        if found_laser is None:
            try:
                open_resource = resource_manager.open_resource(resource)
                open_resource.timeout = 100
                name = open_resource.query("*IDN?").strip()
                open_resource.close()
            except VisaIOError as err:
                print("Could not talk to", resource)
                print(err)
                continue

            # Only add if it is a known power supply or signal generator
            if 'AFG-3021' in name or 'GPD-4303S' in name:
                devices.append((name, resource))

    resource_manager.close()

    return devices


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
        self.power_resource.close()
        self.signal_resource.close()

    def update_laser(self):
        """
        Updates the laser to current power, frequency, and enabled
        """
        if self.enabled:
            self.signal_resource.write("SOURCE1:APPLY:SQUARE {0}HZ,{1},{2}".format(
                self.frequency, 1.1, self.offset))
        else:
            self.signal_resource.write("SOURCE1:APPLY:SQUARE {0}HZ,{1},{2}".format(
                self.frequency, 1.1, self.off_signal))

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

    def get_signal_generator(self):
        """
        Returns the signal generator resource in use
        """
        return self.signal_resource

    def get_power_supply(self):
        """
        Returns the power supply resource in use
        """
        return self.power_resource


class LaserPowerAxis(ControlAxis):
    """
    A ControlAxis to control the power to the laser
    """

    _laser = None

    @staticmethod
    def get_devices():
        """
        Get the lasers / visa resources that can be used for lasers
        """
        return get_devices()

    def set_devices(self, devices):
        if len(devices == 0):
            return False

        if isinstance(devices[0], Laser):
            self._laser = devices[0]
            return True

        else:
            if len(devices) != 2:
                return False

            resource_manager = visa.ResourceManager()
            power_supply = None
            signal_generator = None

            for device in devices:
                try:
                    open_resource = resource_manager.open_resource(device)
                    name = open_resource.query("*IDN?")
                    if 'AFG-3021' in name:
                        signal_generator = open_resource
                    elif 'GPD-4303S' in name:
                        power_supply = open_resource
                    else:
                        open_resource.close()
                except(VisaIOError):
                    print("Could not talk to", device)

            resource_manager.close()

            if not power_supply is None and not signal_generator is None:
                self._laser = Laser(power_supply, 1, signal_generator)
                return True
            else:
                return False

    @staticmethod
    def get_devices_needed():
        """
        Returns the max number of devices needed
        """
        return 2

    def _write_value(self, value):
        self._laser.set_power(value)
        print("Setting laser power to: {}".format(value))


class LaserFequencyAxis(ControlAxis):
    """
    A ControlAxis to control the frequency to the laser
    """

    _laser = None

    @staticmethod
    def get_devices():
        """
        Get the lasers / visa resources that can be used for lasers
        """
        return get_devices()

    def set_devices(self, devices):
        if len(devices == 0):
            return False

        if isinstance(devices[0], Laser):
            self._laser = devices[0]
            return True

        else:
            if len(devices) != 2:
                return False

            resource_manager = visa.ResourceManager()
            power_supply = None
            signal_generator = None

            for device in devices:
                open_resource = resource_manager.open_resource(device)
                name = open_resource.query("*IDN?")
                if 'AFG-3021' in name:
                    signal_generator = open_resource
                elif 'GPD-4303S' in name:
                    power_supply = open_resource
                else:
                    open_resource.close()
            resource_manager.close()

            if not power_supply is None and not signal_generator is None:
                self._laser = Laser(power_supply, 1, signal_generator)
                return True
            else:
                return False

    @staticmethod
    def get_devices_needed():
        """
        Returns the max number of devices needed
        """
        return 2

    def _write_value(self, value):
        self._laser.set_frequency(value)
        print("Setting laser frequency to: {}".format(value))
