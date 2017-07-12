
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlLabel, ControlCombo, ControlEmptyWidget, ControlButton, ControlText, ControlCheckBox, ControlNumber
from framework import ControlAxis, AxisType
from motion import LinearAxis, ControlAxis
from laser import LaserFequencyAxis, LaserPowerAxis


class AxisTab(BaseWidget):
    """
    The Axis Tab in the main GUI
    """

    _axis = []
    _xaxis = None
    _yaxis = None

    _update_function = None

    def __init__(self, update_function=None):
        super().__init__("Axis Tab")

        self._update_function = update_function

        self._axis_list = ControlList(
            label='Axis List',
            default='',
            add_function=self._on_add_axis,
            remove_function=self._on_remove_axis
        )

        self._axis_list.item_selection_changed_event = self._on_selection_changed
        self._axis_list.data_changed_event = self._on_data_changed
        self._axis_list.select_entire_row = True

        self._axis_hw_type = ControlLabel()

        self._min = ControlNumber(
            label="Minimum",
            minimum=-float('inf'),
            maximum=float('inf'),
            decimals=5
        )

        self._min.changed_event = self._on_min_changed
        self._min.hide()

        self._max = ControlNumber(
            label="Maximum",
            minimum=-float('inf'),
            maximum=float('inf'),
            decimals=5
        )

        self._max.changed_event = self._on_max_changed
        self._max.hide()

        self._special_axis = ControlEmptyWidget()

        self._axis_custom = ControlEmptyWidget()

        self.formset = [
            '_axis_list',
            '_axis_hw_type',
            ('_min', '_max'),
            '_special_axis',
            '_axis_custom'
        ]

    def _update_shown_axis(self):
        index = self._axis_list.selected_row_index
        if not index is None:
            axis = self._axis[index]
            assert isinstance(axis, ControlAxis)

            if not axis is None:
                self._axis_hw_type.value = type(axis).__name__

                self._min.show()
                self._min.value = axis.get_min()

                self._max.show()
                self._max.value = axis.get_max()

                special_axis = ControlCombo(label="Special Axis")
                special_axis.add_item('', '')
                special_axis.add_item("X Axis", 'xaxis')
                special_axis.add_item("Y Axis", 'yaxis')

                if axis == self._xaxis:
                    special_axis.value = 'xaxis'
                elif axis == self._yaxis:
                    special_axis.value = 'yaxis'

                def axis_changed(_):
                    """
                    Called when axis changed
                    """
                    if special_axis.value == 'xaxis':
                        self._xaxis = axis
                    elif special_axis.value == 'yaxis':
                        self._yaxis = axis
                    else:
                        if self._xaxis == axis:
                            self._xaxis = None
                        if self._yaxis == axis:
                            self._yaxis = None

                    self._send_events()

                special_axis.current_index_changed_event = axis_changed

                self._special_axis.value = special_axis

                self._axis_custom.value = axis.get_custom_config()
            else:
                self._axis_hw_type.value = ''
                self._min.hide()
                self._max.hide()
                self._special_axis.value = None
                self._axis_custom.value = None
        else:
            self._axis_hw_type.value = ''
            self._min.hide()
            self._max.hide()
            self._special_axis.value = None
            self._axis_custom.value = None


    def _send_events(self):
        if self._update_function is not None:
            self._update_function(
                {'axis': self._axis, 'xaxis': self._xaxis, 'yaxis': self._yaxis})

    def _on_add_axis(self):
        win = NewAxisWindow(self.add_axis)
        win.show()

    def _on_remove_axis(self):
        print("REMOVING")
        index = self._axis_list.selected_row_index
        if not index is None:
            axis = self._axis[index]
            assert isinstance(axis, ControlAxis)

            self._axis_list -= index
            self._axis.pop(index)

            if not axis is None:
                if axis == self._xaxis:
                    self._xaxis = None
                if axis == self._yaxis:
                    self._yaxis = None
            
            self._send_events()

    def add_axis(self, axis):
        """
        Add an axis to the list
        """
        if not axis is None:
            self._axis_list += [axis.get_name()]
            self._axis += [axis]
            self._update_shown_axis()
            self._send_events()

    def _on_selection_changed(self):
        self._update_shown_axis()

    def _on_data_changed(self, row, _, item):
        print("Data changed")
        if row < len(self._axis):
            axis = self._axis[row]
            if not axis is None:
                axis.set_name(item)
                self._update_shown_axis()
                self._send_events()

    def _on_min_changed(self):
        index = self._axis_list.selected_row_index
        if not index is None:
            axis = self._axis[index]
            assert isinstance(axis, ControlAxis)
            if axis is not None:
                if axis.get_min() != self._min.value:
                    axis.set_min(self._min.value)
                    self._send_events()

    def _on_max_changed(self):
        index = self._axis_list.selected_row_index
        if not index is None:
            axis = self._axis[index]
            assert isinstance(axis, ControlAxis)
            if axis is not None:
                if axis.get_max() != self._max.value:
                    axis.set_max(self._max.value)
                    self._send_events()

class NewAxisWindow(BaseWidget):
    """
    Create a new Axis
    """

    def __init__(self, done_function):
        super().__init__("New Axis")

        self._done_function = done_function

        self._axis_name = ControlText(
            label="Name"
        )

        self._axis_hw_type = ControlCombo(
            label="HW Type",
            default=None
        )

        for class_type in ControlAxis.__subclasses__():
            self._axis_hw_type.add_item(class_type.__name__, class_type)

        self._done_button = ControlButton(
            label="Done"
        )

        self._done_button.value = self._done

    def _done(self):
        hw_type = self._axis_hw_type.value
        if issubclass(hw_type, ControlAxis):
            name = self._axis_name.value
            axis = hw_type(name)
            self._done_function(axis)
            self.close()
