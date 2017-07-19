"""
A controller for scan multiple axis through many points and measure the result with a sensor

Points to scan can be imported from a csv file or entered manually
Scanned results can be exported to a csv file
"""

import pyforms
from gui import ControllerWindow

# Import all subclasses of ControlAxis so they appear in drop downs
import motion
import laser

# Import all subclasses of Sensor so they appear in drop downs
import camera
import pda36a

try:
    pyforms.start_app(ControllerWindow)
finally:
    # Need to release the Thorlabs stages, or they get stuck and need to be restarted
    motion.cleanup()
