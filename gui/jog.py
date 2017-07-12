
from PyQt5.QtWidgets import QSizePolicy, QGridLayout, QPushButton, QWidget, QVBoxLayout
from pyforms import BaseWidget
from pyforms.Controls import ControlButton, ControlSlider, ControlEmptyWidget, ControlBase, ControlNumber, ControlCheckBox
import qtawesome as qta
from framework import ControlAxis, OutputDevice

class JogTab(BaseWidget):

    _output = None

    def __init__(self, update_function = None):
        super().__init__("Jog Tab")

        self._update_function = update_function

        self._xy_panel = ControlEmptyWidget()
        self._xy_panel.setSizePolicy(QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed))
        self._xy_panel.value = ControlJog()

        self._aux_panel = ControlEmptyWidget()
        self._aux_panel.setSizePolicy(QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed))

        self._space = ControlEmptyWidget()

        self._enable_output = ControlCheckBox(
            label="Output Enabled"
        )

        self.formset = [
            '_xy_panel',
            '_aux_panel',
            '_space',
            '_enable_output'
        ]

        self._enable_output.changed_event = self._on_enable_change

    def update_events(self, event):
        if isinstance(self._xy_panel.value, ControlJog):
            self._xy_panel.value.update_event(event)

        xaxis = None
        yaxis = None

        if 'xaxis' in event:
            xaxis = event['xaxis']

        if 'yaxis' in event:
            yaxis = event['yaxis']

        if 'axis' in event:
            aux_axis = []
            for axis in event['axis']:
                if axis is not None:
                    aux_axis.append(AuxJog(axis))
            self._aux_panel.value = aux_axis

        if 'output' in event:
            self._output = event['output']

    def _send_events(self):
        if callable(self._update_function):
            self._update_function({'output_enable': self._enable_output.value})

    def _on_enable_change(self):
        if isinstance(self._output, OutputDevice):
            self._output.set_enabled(enable=self._enable_output.value)


class ControlJog(ControlBase):
    """
    A Control to jog two axis
    """

    _xaxis = None
    _yaxis = None
    _step = 10

    def __init__(self, label='', default=None, helptext=None):
        super().__init__(label=label, default=default, helptext=helptext)

    def init_form(self):
        buttons_layout = QGridLayout()

        button_size_policy = QSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred)

        up_icon = qta.icon('fa.arrow-up')
        up_button = QPushButton(up_icon, '')
        up_button.setSizePolicy(button_size_policy)
        up_button.clicked[bool].connect(self._up)

        down_icon = qta.icon('fa.arrow-down')
        down_button = QPushButton(down_icon, '')
        down_button.setSizePolicy(button_size_policy)
        down_button.clicked[bool].connect(self._down)

        left_icon = qta.icon('fa.arrow-left')
        left_button = QPushButton(left_icon, '')
        left_button.setSizePolicy(button_size_policy)
        left_button.clicked[bool].connect(self._left)

        right_icon = qta.icon('fa.arrow-right')
        right_button = QPushButton(right_icon, '')
        right_button.setSizePolicy(button_size_policy)
        right_button.clicked[bool].connect(self._right)

        home_icon = qta.icon('fa.home')
        home_button = QPushButton(home_icon, '')
        home_button.setSizePolicy(button_size_policy)
        home_button.clicked[bool].connect(self._home)

        buttons_layout.addWidget(up_button, 0, 1)
        buttons_layout.addWidget(down_button, 2, 1)
        buttons_layout.addWidget(left_button, 1, 0)
        buttons_layout.addWidget(right_button, 1, 2)
        buttons_layout.addWidget(home_button, 1, 1)

        layout = QVBoxLayout()

        self._step = ControlNumber(
            label="Step Size",
            default=self._step,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        layout.addLayout(buttons_layout)
        layout.addWidget(self._step.form)

        self._form = QWidget()
        self._form.setLayout(layout)

        self.label = self._label

    def update_event(self, event):
        """
        Update the event
        """
        if 'xaxis' in event:
            self._xaxis = event['xaxis']
        if 'yaxis' in event:
            self._yaxis = event['yaxis']

    def _up(self):
        if isinstance(self._yaxis, ControlAxis):
            self._yaxis.goto_value(self._yaxis.get_value() + self._step.value)
        print("UP")

    def _down(self):
        if isinstance(self._yaxis, ControlAxis):
            self._yaxis.goto_value(self._yaxis.get_value() - self._step.value)
        print("DOWN")

    def _left(self):
        if isinstance(self._xaxis, ControlAxis):
            self._xaxis.goto_value(self._xaxis.get_value() - self._step.value)
        print("LEFT")

    def _right(self):
        if isinstance(self._xaxis, ControlAxis):
            self._xaxis.goto_value(self._xaxis.get_value() + self._step.value)
        print("RIGHT")

    def _home(self):
        if isinstance(self._xaxis, ControlAxis):
            self._xaxis.goto_home()

        if isinstance(self._yaxis, ControlAxis):
            self._yaxis.goto_home()

        print("HOME")

    def load_form(self, data, path=None):
        pass

    def save_form(self, data, path=None):
        pass


class AuxJog(BaseWidget):
    """
    A Widget to jog aux axis
    """

    def __init__(self, axis):
        super().__init__("Aux Jog")

        assert isinstance(axis, ControlAxis)

        self._axis = axis

        self._value_field = ControlNumber(
            label=axis.get_name(),
            default=axis.get_value(),
            minimum=axis.get_min(),
            maximum=axis.get_max(),
            decimals=5
        )

        self._value_field.changed_event = self._update_value

    def _update_value(self):
        value = self._value_field.value
        print(value)
        self._axis.goto_value(value)
