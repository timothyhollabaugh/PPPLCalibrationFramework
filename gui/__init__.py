"""
GUI code
"""
import time
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlEmptyWidget, ControlLabel
from gui.axis import AxisTab
from gui.jog import JogTab
from gui.output import OutputTab
from gui.points import PointsTab
from gui.sensor import SensorTab
from gui.canvas import Canvas
import motion


class ControllerWindow(BaseWidget):
    """
    The main window of the application
    """

    def __init__(self):
        super().__init__("Calibration Controller")

        # Create a spot for the canvas to show the points and location
        self._canvas = ControlEmptyWidget()
        self._canvas.form.setSizePolicy(QSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self._canvas.value = Canvas()

        # Create a spot for the tabs with configuration
        self._tabs = ControlEmptyWidget()
        self._tabs.form.setSizePolicy(QSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.MinimumExpanding))
        # Create a tabs widget and give it the _update_events(event) function to call whenever there is an event
        self._tabs.value = TabWidget(self._update_events)

        self.formset = [
            ('_tabs', '_canvas')
        ]
        self.has_progress = True


    def _update_events(self, events):
        """
        Update the events fired by other classes
        Current events:
        'axis': Whenever the list of axis changes. Carries the list of axis
        'xaxis': Whenever the X axis changes. Carries the current X axis
        'yaxis': Whenever the Y axis changes. Carries the current Y axis
        'output': Whenever the output device changes. Carries the current output
        'sensor': Whenever the sensor changes. Carries the current sensor
        """
        # Distribute the events to the Canvas and Tabs
        if isinstance(self._tabs.value, TabWidget):
            self._tabs.value.update_events(events)

        if isinstance(self._canvas.value, Canvas):
            self._canvas.value.update_events(events)

    def before_close_event(self):
        """
        Cleanup the Thorlabs stages before closing
        """
        motion.cleanup()


class TabWidget(BaseWidget):
    """
    A Widget for all the tabs
    """

    _update_function = None

    def __init__(self, update_function=None):
        super().__init__("TABS")

        self._update_function = update_function

        self._axis_tab = ControlEmptyWidget()
        self._axis_tab.value = AxisTab(self._update_function)

        self._points_tab = ControlEmptyWidget()
        self._points_tab.value = PointsTab(self._update_function)

        self._jog_tab = ControlEmptyWidget()
        self._jog_tab.value = JogTab(self._update_function)

        self._output_tab = ControlEmptyWidget()
        self._output_tab.value = OutputTab(self._update_function)

        self._sensor_tab = ControlEmptyWidget()
        self._sensor_tab.value = SensorTab(self._update_function)

        # Define that the Controls should be shown as tabs. 
        # See pyforms docs for details
        self.formset = [
            {
                "Axis": ['_axis_tab'],
                "Output": ['_output_tab'],
                "Sensor": ['_sensor_tab'],
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
        if isinstance(self._points_tab.value, PointsTab):
            self._points_tab.value.update_events(events)
