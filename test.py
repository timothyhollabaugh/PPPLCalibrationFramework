import time
import visa
import thorlabs_apt.core as apt_core
import thorlabs_apt as apt
from framework import AxisController
from laser import Laser, LaserFequencyAxis, LaserPowerAxis
from motion import LinearAxis, RotateAxis
from camera import CameraSensor

def test():
    try:
        print("Opening Laser")
        resource_manager = visa.ResourceManager()
        power = resource_manager.open_resource('ASRL5::INSTR')
        signal = resource_manager.open_resource('ASRL6::INSTR')

        laser = Laser(power, 1, signal)
        print("Done Opening Laser")

        print("Opening Motion Stages")
        linear = apt.Motor(45869584)
        rotate = apt.Motor(40869426)
        linear.move_home(True)
        rotate.move_home(True)
        print("Done Opening Motion Stages")

        #linear = None
        #rotate = None
        #laser = None

        print("Constructing Axis")
        frequency_axis = LaserFequencyAxis(8.0, 11.0, 2, laser)
        power_axis = LaserPowerAxis(0.2, 0.8, 2, laser)
        linear_axis = LinearAxis(0.0, 25.4*3, 3, linear)
        rotate_axis = RotateAxis(0.0, 25.4*3, 3, rotate)

        camera_sensor = CameraSensor(laser, 0.5, 0.05)

        controller = AxisController([frequency_axis, power_axis, rotate_axis, linear_axis], camera_sensor, 1)
        print("Done Constructing Axis")

        import IPython
        IPython.embed()

        #controller.scan()

    finally:
        print("Cleaning Up")
        apt_core._cleanup()

test()