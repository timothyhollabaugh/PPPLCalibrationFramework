
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import QWidget
from pyforms.Controls import ControlBase
import numpy as np
from framework import ControlAxis

class Canvas(ControlBase):
    """
    The canvas to show points and location
    """

    _xaxis = None
    _yaxis = None

    def __init__(self):
        super().__init__("Canvas")
        self._points = [(0, 0)]

    def init_form(self):
        self._form = QWidget()
        self._form.paintEvent = self._paint_event

    def _paint_event(self, event):
        print("Painting")
        painter = QPainter()
        painter.begin(self._form)
        painter.setPen(QColor(255, 0, 0))
        painter.setFont(QFont("Arial", 30))
        painter.drawText(50, 50, "Hello, World!")
        for point in self._points:
            painter.drawPoint(point[0], point[1])
        painter.end()

    def update_events(self, event):
        if 'xaxis' in event:
            self._xaxis = event['xaxis']

        if 'yaxis' in event:
            self._yaxis = event['yaxis']

        if 'timer' in event:
            if isinstance(self._xaxis, ControlAxis) and isinstance(self._yaxis, ControlAxis):
                self._points.append((self._xaxis.get_current_value(), self._yaxis.get_current_value()))
            self._form.update()
