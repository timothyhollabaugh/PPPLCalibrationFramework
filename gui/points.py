
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlNumber, ControlButton, ControlCombo, ControlEmptyWidget
from camera import CameraSensor
from framework import ControlAxis, AxisController


class PointsTab(BaseWidget):
    """
    A Tab for a list of points
    """

    _axis = []

    _update_function = None

    _controller = None
    _sensor = None
    _output = None

    def __init__(self, update_function=None):
        super().__init__("Points")

        self._update_function = update_function

        self._points_list = ControlList(
            label="Points",
            add_function=self._add_point,
            remove_function=self._remove_point
        )
        self._points_list.data_changed_event = self._change_point
        self._points_list.horizontal_headers = [
            axis.get_name() for axis in self._axis]

        self._delay_time = ControlNumber(
            label="Delay Time",
            default=1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._scan_button = ControlButton(
            label="Scan"
        )
        self._scan_button.value = self._begin_scan

    def update_events(self, events):
        """
        Updates all events
        """
        if 'axis' in events:
            self._axis = events['axis']
            self._points_list.clear()
            self._points_list.horizontal_headers = [
                axis.get_name() for axis in self._axis]
            self._points_list.resize_rows_contents()

            length = self._max_axis_len()
            for i in range(0, length):
                point = []
                for axis in self._axis:
                    assert isinstance(axis, ControlAxis)
                    if len(axis.points) <= i:
                        for j in range(len(axis.points) - 1, i):
                            axis.points.append(axis.get_min())
                    point.append(axis.points[i])
                self._points_list += point

        if 'sensor' in events:
            self._sensor = events['sensor']

        if 'output' in events:
            self._output = events['output']

    def _max_axis_len(self):
        max_len = 0
        for axis in self._axis:
            assert isinstance(axis, ControlAxis)
            if len(axis.points) > max_len:
                max_len = len(axis.points)
        return max_len

    def _add_point(self):
        for axis in self._axis:
            assert isinstance(axis, ControlAxis)
            axis.points.append(0.0)
        self._points_list += [0.0] * len(self._axis)

    def _remove_point(self):
        index = self._points_list.selected_row_index
        if index is not None:
            self._points_list -= index
            for axis in self._axis:
                assert isinstance(axis, ControlAxis)
                axis.points.pop(index)

    def _change_point(self, row, col, item):
        if len(self._axis) > col and len(self._axis[col].points) > row:
            self._axis[col].points[row] = item

    def print_axis(self):
        for axis in self._axis:
            print(axis.get_name(), axis.points)

    def _begin_scan(self):
        self._controller = AxisController(
            self._axis, self._sensor, self._output, self._delay_time.value)
        self._controller.begin()
