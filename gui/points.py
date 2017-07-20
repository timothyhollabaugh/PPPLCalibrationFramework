
import csv
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlNumber, ControlButton, ControlEmptyWidget, ControlFile, ControlText
from framework import ControlAxis, AxisController, AxisControllerState


class PointsTab(BaseWidget):
    """
    A Tab for a list of points
    """

    _axis = []

    _update_function = None

    _controller = None
    _sensor = None
    _lightsource = None

    def __init__(self, update_function=None):
        super().__init__("Points")

        self._update_function = update_function

        self._open_file = ControlFile(
            label="Points File: "
        )
        self._open_file.changed_event = self._on_open_file2

        self._points_list = ControlList(
            label="Points",
            add_function=self._add_point,
            remove_function=self._remove_point
        )
        self._points_list.data_changed_event = self._change_point
        self._points_list.horizontal_headers = [
            axis.get_name() for axis in self._axis]

        self._pre_delay_time = ControlNumber(
            label="Pre Delay Time",
            default=1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._post_delay_time = ControlNumber(
            label="Post Delay Time",
            default=1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._out_file = ControlText(
            label="Output File: "
        )

        self._scan_button = ControlButton(
            label="Scan"
        )
        self._scan_button.value = self._begin_scan

    def update_events(self, events):
        """
        Updates all events
        """

        # Update the points with the most recent axis
        if 'axis' in events:
            self._axis = events['axis']
            self._update_lists()

        if 'sensor' in events:
            self._sensor = events['sensor']

        if 'lightsource' in events:
            self._lightsource = events['lightsource']

        if 'scan' in events:
            state = events['scan'][0]
            if state == AxisControllerState.DONE:
                self._scan_button.label = "Scan"
            else:
                self._scan_button.label = "Stop"

    def _update_lists(self):
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

    def _max_axis_len(self):
        """
        Get the number of points in the axis that has the most points
        """
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
        self._update_lists()

    def _remove_point(self):
        index = self._points_list.selected_row_index
        if index is not None:
            for axis in self._axis:
                assert isinstance(axis, ControlAxis)
                axis.points.pop(index)

        self._update_lists()

    def _change_point(self, row, col, item):
        if len(self._axis) > col and len(self._axis[col].points) > row:
            self._axis[col].points[row] = item

    def _begin_scan(self):
        """
        Create an AxisController and begin scanning
        """
        if self._controller is None or self._controller.get_state() == AxisControllerState.DONE:
            self._controller = AxisController(
                self._axis, self._sensor, self._lightsource, self._pre_delay_time.value,
                self._post_delay_time.value, self._out_file.value, self._update_function)
            self._controller.begin()
        else:
            self._controller.stop()

    def _on_open_file(self):
        """
        Open a csv file and read it into the points lists
        """
        print("Opening File:", self._open_file.value)

        if self._open_file.value is not None and self._open_file.value != '':

            with open(self._open_file.value, newline='') as csvfile:

                try:
                    csvreader = csv.reader(
                        csvfile, quoting=csv.QUOTE_NONNUMERIC)

                    for axis in self._axis:
                        if isinstance(axis, ControlAxis):
                            axis.points.clear()
                    self._points_list.clear()

                    for row in csvreader:
                        print(row)
                        self._points_list += [0.0] * len(self._axis)
                        for index, data in enumerate(row):
                            if index < len(self._axis):
                                axis = self._axis[index]
                                if isinstance(axis, ControlAxis):
                                    axis.points.append(data)
                                    self._points_list.set_value(
                                        index, len(axis.points) - 1, data)

                except (UnicodeDecodeError, ValueError):
                    print("Could not parse file")
                    return

    def _on_open_file2(self):
        """
        Open a csv file and rearange columns accoring to header
        """

        print("Opening File:", self._open_file.value)

        if self._open_file.value is not None and self._open_file.value != '':

            with open(self._open_file.value, newline='') as csvfile:

                try:
                    csvreader = csv.reader(csvfile)

                    for axis in self._axis:
                        if isinstance(axis, ControlAxis):
                            axis.points.clear()
                    self._points_list.clear()

                    points = []

                    for row in csvreader:
                        for index, data in enumerate(row):
                            if len(points) <= index:
                                points.append([])
                            points[index].append(data)

                    print(points)

                    for points_list in points:
                        print(points_list[0])
                        if isinstance(points_list[0], str):
                            for axis in self._axis:
                                if points_list[0] == axis.get_name():
                                    axis.points = [float(point) for point in points_list[1:]]
                                    print(axis.get_name(), axis.points)

                    self._update_lists()

                except:
                    print("Failed to read file")
