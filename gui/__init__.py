
import time
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlEmptyWidget, ControlLabel
from gui.axis import AxisTab
from gui.jog import JogTab
from gui.output import OutputTab
from gui.canvas import Canvas
import motion

class ControllerWindow(BaseWidget):
    """
    A window to list the controllers
    """

    _update_functions = []
    _timer = QTimer()

    def __init__(self):
        super().__init__("Calibration Controller")

        self._timer.timeout.connect(self._update_timer)
        self._timer.start(100)

        self._canvas = ControlEmptyWidget()
        self._canvas.form.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self._canvas.value = Canvas()

        self._tabs = ControlEmptyWidget()
        self._tabs.form.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding))
        self._tabs.value = TabWidget(self._update_events)

        self.formset = [
            ('_tabs', '_canvas')
        ]

    def add_update_function(self, event, function):
        """
        Add a function to be called when event 'event' happens
        Current events:
        'timer'
        'axis'
        'xaxis'
        'yaxis'
        'output'
        """
        self._update_functions += (event, function)

    def _update_events(self, events):
        #print(events)
        if isinstance(self._tabs.value, TabWidget):
            self._tabs.value.update_events(events)

        if isinstance(self._canvas.value, Canvas):
            self._canvas.value.update_events(events)

    def _update_timer(self):
        self._update_events({'timer': time.time()})

    def before_close_event(self):
        motion.cleanup()

class TabWidget(BaseWidget):
    """
    A Widget for all the tabs
    """

    _update_function = None

    def __init__(self, update_function=None):
        super().__init__("TABS")

        self._update_function = update_function

        self._axis_tab = ControlEmptyWidget(
            label='Axis Tab'
        )

        self._axis_tab.value = AxisTab(self._update_function)

        self._points_tab = ControlEmptyWidget(
            label='Points Tab'
        )

        self._jog_tab = ControlEmptyWidget(
            label='Jog Tab'
        )

        self._jog_tab.value = JogTab(self._update_function)

        self._output_tab = ControlEmptyWidget()
        self._output_tab.value = OutputTab(self._update_function)

        self.formset = [
            {
                "Axis": ['_axis_tab'],
                "Output": ['_output_tab'],
                "Points": ['_points_tab'],
                "Jog": ['_jog_tab']
            }
        ]

    def update_events(self, events):
        """
        Updates events
        """
        if isinstance(self._jog_tab.value, JogTab):
            self._jog_tab.value.update_events(events)

    def init_form(self):
        super().init_form()
