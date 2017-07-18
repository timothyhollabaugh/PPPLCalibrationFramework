
import pyforms
from gui import ControllerWindow

# Import all subclasses of ControlAxis and Sensor so they appear in drop downs
import motion
import laser

import camera
import pda36a

try:
    pyforms.start_app(ControllerWindow)
finally:
    motion.cleanup()
