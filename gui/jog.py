
from PyQt5.QtWidgets import QSizePolicy
from pyforms import BaseWidget
from pyforms.Controls import ControlButton, ControlSlider

class JogTab(BaseWidget):

    def __init__(self):
        super().__init__("Jog Tab")

        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self._up_button = ControlButton(
            label="^"
        )

        self._up_button.form.setSizePolicy(size_policy)

        self._down_button = ControlButton(
            label="v"
        )

        self._down_button.form.setSizePolicy(size_policy)

        self._left_button = ControlButton(
            label="<"
        )

        self._left_button.form.setSizePolicy(size_policy)

        self._right_button = ControlButton(
            label=">"
        )

        self._right_button.form.setSizePolicy(size_policy)

        self.formset = [
            (''            , '_up_button'  , ''             ),
            ('_left_button', ''            , '_right_button'),
            (''            , '_down_button', ''             )
        ]
