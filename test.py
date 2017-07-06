import time
import visa
import thorlabs_apt.core as apt_core
import thorlabs_apt as apt

try:
    print("Loading Axis")
    from framework import AxisController
    from laser import Laser, LaserFequencyAxis, LaserPowerAxis
    from motion import LinearAxis, RotateAxis
    from camera import CameraSensor

    print("Opening Laser")
    resource_manager = visa.ResourceManager()
    power = resource_manager.open_resource('ASRL5::INSTR')
    signal = resource_manager.open_resource('ASRL6::INSTR')

    laser = Laser(power, 1, signal)
    print("Done Opening Laser")

    print("Opening Motion Stages")
    linear = apt.Motor(45869584)
    rotate = apt.Motor(40869426)
    print("Done Opening Motion Stages")

    def step():
        print("============================================================")
        #print("Stepping")
        #print("Enabling Laser")
        laser.set_enabled(enable=True)
        time.sleep(1)
        #print("Disabling Laser")
        laser.set_enabled(enable=False)
        time.sleep(0.5)

    print("Constructing Axis")
    frequency_axis = LaserFequencyAxis(laser, 2, 8, 11)
    power_axis = LaserPowerAxis(laser, 2, 0.7, 0.2)
    linear_axis = LinearAxis(linear, 5, 25.4, 0)
    rotate_axis = RotateAxis(rotate, 5, 25.4, 0, 576.2625)

    camera_calibrated = CameraSensor(laser, 5, 0.05)

    controller = AxisController([frequency_axis, power_axis, rotate_axis, linear_axis], camera_calibrated)
    print("Done Constructing Axis")

    import IPython
    IPython.embed()

    #controller.scan()

finally:
    print("Cleaning Up")
    apt_core._cleanup()
