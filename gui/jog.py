
from numbers import Number
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QSizePolicy, QGridLayout, QPushButton, QWidget, QVBoxLayout, QFrame
from pyforms import BaseWidget
from pyforms.Controls import ControlButton, ControlSlider, ControlEmptyWidget, ControlBase, ControlNumber, ControlCheckBox, ControlLabel, ControlCombo, ControlTree, ControlText
import qtawesome as qta
from framework import ControlAxis, LightSource


class JogTab(BaseWidget):

    _saved_points = {}
    _lightsource = None
    _timer = QTimer()

    def __init__(self, update_function=None):
        super().__init__("Jog Tab")

        self._update_function = update_function

        self._timer.timeout.connect(self._timer_update)
        self._timer.start(200)

        self._xy_panel = ControlEmptyWidget()
        self._xy_panel.setSizePolicy(QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed))
        self._xy_panel.value = ControlJog()

        self._aux_panel = ControlEmptyWidget()
        self._aux_panel.form.setSizePolicy(QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed))

        self._space = ControlEmptyWidget()

        self._enable_button = ControlButton(
            label='Enable LightSource'
        )
        self._enable_button.value = self._enable_lightsource

        self._disable_button = ControlButton(
            label='Disable LightSource'
        )
        self._disable_button.value = self._disable_lightsource

        self.formset = [
            '_xy_panel',
            '_aux_panel',
            '_space',
            ('_enable_button', '_disable_button')
        ]

    def update_events(self, event):
        if isinstance(self._xy_panel.value, ControlJog):
            self._xy_panel.value.update_event(event)

        if isinstance(self._aux_panel.value, list):
            for aux_axis in self._aux_panel.value:
                aux_axis.update_events(event)

        if 'saved_points' in event:
            self._saved_points = event['saved_points']

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
                    aux_jog = AuxJog(axis)
                    aux_jog.update_events({'saved_points': self._saved_points})
                    aux_axis.append(aux_jog)
            self._aux_panel.value = aux_axis

        if 'lightsource' in event:
            self._lightsource = event['lightsource']

    def _timer_update(self):
        if isinstance(self._aux_panel.value, list):
            for aux_axis in self._aux_panel.value:
                aux_axis.timer_update()

    def _send_events(self):
        if callable(self._update_function):
            self._update_function(
                {'lightsource_enable': self._enable_lightsource.value})

    def _enable_lightsource(self):
        if isinstance(self._lightsource, LightSource):
            self._lightsource.set_enabled(True)

    def _disable_lightsource(self):
        if isinstance(self._lightsource, LightSource):
            self._lightsource.set_enabled(False)


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

    def _down(self):
        if isinstance(self._yaxis, ControlAxis):
            self._yaxis.goto_value(self._yaxis.get_value() - self._step.value)

    def _left(self):
        if isinstance(self._xaxis, ControlAxis):
            self._xaxis.goto_value(self._xaxis.get_value() - self._step.value)

    def _right(self):
        if isinstance(self._xaxis, ControlAxis):
            self._xaxis.goto_value(self._xaxis.get_value() + self._step.value)

    def _home(self):
        if isinstance(self._xaxis, ControlAxis):
            self._xaxis.goto_home()

        if isinstance(self._yaxis, ControlAxis):
            self._yaxis.goto_home()

    def load_form(self, data, path=None):
        pass

    def save_form(self, data, path=None):
        pass


class AuxJog(BaseWidget):
    """
    A Widget to jog aux axis
    """

    _last_set_value = 0
    label = ""

    def __init__(self, axis):
        super().__init__("Aux Jog")

        assert isinstance(axis, ControlAxis)

        self._axis = axis

        self.label = axis.get_name()

        self._value_field = ControlText(
            label="Target",
            default=str(axis.get_value())
        )

        self._set_button = ControlButton(
            label="Go to target"
        )
        self._set_button.value = self._update_value

        self._saved_point_field = ControlCombo(
            label="Saved Point"
        )

        self._saved_point_button = ControlButton(
            label="Go to saved point"
        )
        self._saved_point_button.value = self._update_saved_point

        self._current_field = ControlLabel(
            label="Current Value ({})".format(axis.get_units())
        )

        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))

        self.set_margin(10)

        self.formset = [
            ("info:{0} ({1}):".format(axis.get_name(),
                                      axis.get_units()), '', '', '_current_field'),
            ('_value_field', '_set_button'),
            ('_saved_point_field', '_saved_point_button')
        ]

    def _update_value(self):
        value = self._value_field.value
        self._axis.goto_value(value)

    def _update_saved_point(self):
        self._axis.goto_value(self._saved_point_field.value)

    def update_events(self, events):
        #print("Aux Event:", events)
        if 'saved_points' in events:
            self._saved_point_field.clear()
            for key, value in events['saved_points'].items():
                self._saved_point_field += (key, key)

    def timer_update(self):
        self._current_field.value = "{0:.5f}".format(
            self._axis.get_current_value())

        if self._axis.get_string_value() != self._last_set_value:
            self._value_field.value = self._axis.get_string_value()
            self._last_set_value = self._axis.get_string_value()
