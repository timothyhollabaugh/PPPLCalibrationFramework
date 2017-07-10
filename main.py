
import pyforms
from gui import ControllerWindow
import motion

try:
    pyforms.start_app(ControllerWindow)
finally:
    motion.cleanup()
