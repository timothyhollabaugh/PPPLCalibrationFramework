
import csv
from PyQt5.QtWidgets import QFileDialog
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlText, ControlButton, ControlFile


class SavedPointsTab(BaseWidget):
    """
    The Saved Points tab
    """

    _saved_points = {}

    _update_function = None

    def __init__(self, update_function=None):
        super().__init__("Saved Points")

        self._update_function = update_function

        self._open_file = ControlFile(
            label="Saved Points File"
        )
        self._open_file.changed_event = self._on_open_file

        self._save_file = ControlButton(
            label="Save"
        )
        self._save_file.value = self._on_save_file

        self._saved_points_list = ControlList(
            label="Saved Points",
            add_function=self._add_saved_point,
            remove_function=self._remove_saved_point
        )
        self._saved_points_list.data_changed_event = self._change_point

        self._saved_points_list.horizontal_headers = ["Name", "Value"]

        self.formset = [
            ('_open_file', '_save_file'),
            '_saved_points_list'
        ]

    def update_events(self, events):
        pass

    def _send_events(self):
        if self._update_function is not None:
            self._update_function({'saved_points': self._saved_points})

    def _update_saved_points(self):
        self._saved_points_list.clear()

        for name, value in self._saved_points.items():
            self._saved_points_list += [name, value]

    def add_saved_point(self, name):
        if not name in self._saved_points:
            self._saved_points[name] = 0.0
            self._update_saved_points()
            self._send_events()
            return True
        else:
            return False

    def _add_saved_point(self):
        window = NewPointWindow(self.add_saved_point)
        window.show()

    def _remove_saved_point(self):
        index = self._saved_points_list.selected_row_index
        if index is not None:
            name = self._saved_points_list.get_value(0, index)
            self._saved_points.pop(name)

        self._update_saved_points()
        self._send_events()

    def _change_point(self, row, col, item):
        name = self._saved_points_list.get_value(0, row)
        if col == 1:
            # The data was edited
            self._saved_points[name] = item
            self._send_events()
        else:
            # Something else (name) was edited and needs to be changed back
            if not name in self._saved_points:
                self._update_saved_points()

    def _on_open_file(self):
        if self._open_file.value is not None and self._open_file.value != '':
            with open(self._open_file.value, newline='') as csvfile:
                try:
                    csvreader = csv.reader(csvfile)

                    self._saved_points = {}

                    for point in csvreader:
                        self._saved_points[point[0]] = point[1]
                except:
                    print("Failed to read file")
                
            self._update_saved_points()

    def _on_save_file(self):
        points_file = QFileDialog.getSaveFileName(caption = "Save Points", filter = 'CSV Files (*.csv)')

        out_points = []
        for name, value in self._saved_points.items():
            out_points.append([name, value])

        with open(points_file[0], 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerows(out_points)


class NewPointWindow(BaseWidget):
    """
    The window for adding a new point
    """

    _update_function = None

    def __init__(self, update_function):
        super().__init__("New Saved Point")

        self._update_function = update_function

        self._text = ControlText(
            label="Name"
        )

        self._done_button = ControlButton(
            label="Done"
        )

        self._done_button.value = self._done

    def _done(self):
        if self._update_function is not None:
            if self._update_function(self._text.value):
                self.close()
        else:
            self.close()
