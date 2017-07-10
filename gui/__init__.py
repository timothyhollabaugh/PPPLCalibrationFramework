
from pyforms import BaseWidget
from pyforms.Controls import ControlEmptyWidget, ControlLabel
from gui.axis import AxisTab
import motion

class ControllerWindow(BaseWidget):
    """
    A window to list the controllers
    """

    _control_axis = []

    def __init__(self):
        super().__init__("Calibration Controller")

        self._label = ControlLabel(
            label='Hello'
        )

        self._axis_tab = ControlEmptyWidget(
            label='Axis Tab'
        )

        self._axis_tab.value = AxisTab()

        self._points_tab = ControlEmptyWidget(
            label='Points Tab'
        )

        self._jog_tab = ControlEmptyWidget(
            label='Jog Tab'
        )

        self.formset = [
            '_label',
            {
                "Axis": ['_axis_tab'],
                "Points": ['_points_tab'],
                "Jog": ['_jog_tab']
            }
        ]

    def before_close_event(self):
        motion.cleanup()
