
from pyforms import BaseWidget
from pyforms.Controls import ControlList, ControlLabel, ControlCombo, ControlEmptyWidget, ControlButton, ControlText
from framework import ControlAxis, AxisType
from motion import LinearAxis, ControlAxis
from laser import LaserFequencyAxis, LaserPowerAxis

class AxisTab(BaseWidget):
    """
    The Axis Tab in the main GUI
    """

    _axis = []

    def __init__(self):
        super().__init__("Axis Tab")

        self._axis_list = ControlList(
            label='Axis List',
            default='',
            add_function=self._on_add_axis,
            remove_function=self._on_remove_axis,
        )

        self._axis_list.item_selection_changed_event = self._on_selection_changed
        self._axis_list.data_changed_event = self._on_data_changed
        self._axis_list.select_entire_row = True

        self._axis_name = ControlLabel()
        self._axis_hw_type = ControlLabel()
        self._axis_custom = ControlEmptyWidget()

        self.formset = ('_axis_list', '||', [
            ('_axis_name', '', '_axis_hw_type'),
            '=',
            '_axis_custom',
            ''
        ])

    def _update_shown_axis(self):
        index = self._axis_list.selected_row_index
        if not index is None:
            axis = self._axis[index]
            assert isinstance(axis, ControlAxis)

            self._axis_name.value = self._axis_list.get_value(0, index)

            if not axis is None:
                self._axis_hw_type.value = type(axis).__name__
                self._axis_custom.value = axis.get_custom_config()
            else:
                self._axis_hw_type.value = ''
                self._axis_custom.value = None
        else:
            self._axis_name.value = ''
            self._axis_hw_type.value = ''
            self._axis_custom.value = None


    def _on_add_axis(self):
        win = NewAxisWindow(self.add_axis)
        win.show()

    def add_axis(self, axis):
        if not axis is None:
            self._axis_list += [axis.get_name()]
            self._axis += [axis]
            self._update_shown_axis()

    def _on_remove_axis(self):
        pass

    def _on_selection_changed(self):
        self._update_shown_axis()

    def _on_data_changed(self, row, _, item):
        if row < len(self._axis):
            axis = self._axis[row]
            if not axis is None:
                axis.set_name(item)
                self._update_shown_axis()


class NewAxisWindow(BaseWidget):

    def __init__(self, done_function):
        super().__init__("New Axis")

        self._done_function = done_function

        self._axis_name = ControlText(
            label = "Name"
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
