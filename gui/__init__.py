"""
GUI code
"""
import time
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QTimer
from pyforms import BaseWidget
from pyforms.Controls import ControlEmptyWidget, ControlLabel, ControlProgress
from gui.axis import AxisTab
from gui.jog import JogTab
from gui.lightsource import LightSourceTab
from gui.points import PointsTab
from gui.sensor import SensorTab
from gui.savedpoints import SavedPointsTab
from gui.canvas import Canvas
import motion
import laser


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
        self._canvas.form.setMinimumWidth(500)
        self._canvas.form.setMinimumHeight(500)
        self._canvas.value = Canvas()

        # Create a spot for the tabs with configuration
        self._tabs = ControlEmptyWidget()
        self._tabs.form.setSizePolicy(QSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.MinimumExpanding))
        self._tabs.form.setMinimumWidth(400)
        self._tabs.form.setMinimumHeight(500)
        # Create a tabs widget and give it the _update_events(event) function to call whenever there is an event
        self._tabs.value = TabWidget(self._update_events)

        # Create a progress bar
        self._progress = ControlProgress(
            label='%v/%m Steps | %p%',
            default=0,
            min=0,
            max=1
        )

        self.formset = [
            ('_tabs', '_canvas'),
            '_progress'
        ]

    def _update_events(self, events):
        """
        Update the events fired by other classes
        Current events:
        'axis': Whenever the list of axis changes. Carries the list of axis
        'xaxis': Whenever the X axis changes. Carries the current X axis
        'yaxis': Whenever the Y axis changes. Carries the current Y axis
        'lightsource': Whenever the lightsource device changes. Carries the current lightsource
        'sensor': Whenever the sensor changes. Carries the current sensor
        'scan': Whenever the scan state changes. Carries tuple of (AxisControllerState, step)
        'saved_points': Whenever the list of saved points changes
        'close': Whenever the main window is closed. Carries None
        """

        #print(events)
        # Distribute the events to the Canvas and Tabs
        if isinstance(self._tabs.value, TabWidget):
            self._tabs.value.update_events(events)

        if isinstance(self._canvas.value, Canvas):
            self._canvas.value.update_events(events)

        if 'scan' in events:
            self._progress.max = events['scan'][2]
            self._progress.value = events['scan'][1]

    def before_close_event(self):
        """
        Cleanup opened resources before closing
        """
        self._update_events({'close': None})
        motion.cleanup()
        laser.cleanup()


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

        self._lightsource_tab = ControlEmptyWidget()
        self._lightsource_tab.value = LightSourceTab(self._update_function)

        self._sensor_tab = ControlEmptyWidget()
        self._sensor_tab.value = SensorTab(self._update_function)

        self._saved_points_tab = ControlEmptyWidget()
        self._saved_points_tab.value = SavedPointsTab(self._update_function)

        # Define that the Controls should be shown as tabs.
        # See pyforms docs for details
        self.formset = [
            {
                "Axis": ['_axis_tab'],
                "Light Source": ['_lightsource_tab'],
                "Sensor": ['_sensor_tab'],
                "Points": ['_points_tab'],
                "Jog": ['_jog_tab'],
                "Saved Points": ['_saved_points_tab']
            }
        ]

    def update_events(self, events):
        """
        Updates events
        """
        if isinstance(self._axis_tab.value, AxisTab):
            self._axis_tab.value.update_events(events)
        if isinstance(self._jog_tab.value, JogTab):
            self._jog_tab.value.update_events(events)
        if isinstance(self._points_tab.value, PointsTab):
            self._points_tab.value.update_events(events)
        if isinstance(self._sensor_tab.value, SensorTab):
            self._sensor_tab.value.update_events(events)
        if isinstance(self._saved_points_tab.value, SavedPointsTab):
            self._saved_points_tab.value.update_events(events)
