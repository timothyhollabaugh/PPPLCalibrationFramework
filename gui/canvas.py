
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QTransform
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
    _margins = QPointF(10.0, 10.0)
    _timer = QTimer()

    def __init__(self):
        super().__init__("Canvas")
        self._points = [(0, 0)]
        self._timer.timeout.connect(self._form.update)
        self._timer.start()

    def init_form(self):
        self._form = QWidget()
        self._form.paintEvent = self._paint_event

    def _paint_event(self, event):
        if self._xaxis is not None and self._yaxis is not None and self._xaxis.get_max() - self._xaxis.get_min() != 0 and self._yaxis.get_max() - self._yaxis.get_min() != 0:
            assert isinstance(self._xaxis, ControlAxis)
            assert isinstance(self._yaxis, ControlAxis)

            widget_min = QPointF(0.0, 0.0)
            widget_max = QPointF(self._form.width(), self._form.height())

            display_min = widget_min + self._margins
            display_max = widget_max - self._margins

            world_min = QPointF(self._xaxis.get_min(), self._yaxis.get_min())
            world_max = QPointF(self._xaxis.get_max(), self._yaxis.get_max())

            transform = QTransform()
            transform.translate(display_min.x(), display_max.y())
            transform.scale((display_max.x() - display_min.x()) / (world_max.x() - world_min.x()),
                           -(display_max.y() - display_min.y()) / (world_max.y() - world_min.y()))
            transform.translate(-world_min.x(), -world_min.y())

            position = transform.map(
                QPointF(self._xaxis.get_current_value(), self._yaxis.get_current_value()))

            origin = transform.map(QPointF(0.0, 0.0))

            painter = QPainter()
            painter.begin(self._form)

            painter.setRenderHint(QPainter.Antialiasing)

            painter.fillRect(QRectF(display_min, display_max), QColor(255, 255, 255))

            axis_pen = QPen()
            axis_pen.setColor(QColor(128, 128, 128))
            axis_pen.setWidthF(2.0)

            position_pen = QPen()
            position_pen.setColor(QColor(0, 0, 0))
            position_pen.setWidthF(2.0)

            point_pen = QPen()
            point_pen.setColor(QColor(0, 0, 0))
            point_pen.setWidthF(2.0)

            painter.setPen(axis_pen)
            painter.drawLine(QPointF(widget_min.x(), origin.y()),
                             QPointF(widget_max.x(), origin.y()))
            painter.drawLine(QPointF(origin.x(), widget_min.y()),
                             QPointF(origin.x(), widget_max.y()))

            painter.setPen(position_pen)
            painter.drawLine(QPointF(position.x()-10, position.y()),
                             QPointF(position.x()+10, position.y()))
            painter.drawLine(QPointF(position.x(), position.y()+10),
                             QPointF(position.x(), position.y()-10))

            painter.setPen(point_pen)

            for i in range(0, max(len(self._xaxis.points), len(self._yaxis.points))):
                point = transform.map(QPointF(self._xaxis.points[i], self._yaxis.points[i]))
                painter.drawLine(QPointF(point.x()-10, point.y()-10),
                                 QPointF(point.x()+10, point.y()+10))

                painter.drawLine(QPointF(point.x()+10, point.y()-10),
                                 QPointF(point.x()-10, point.y()+10))

            painter.end()

    def update_events(self, event):
        if 'xaxis' in event:
            self._xaxis = event['xaxis']

        if 'yaxis' in event:
            self._yaxis = event['yaxis']

        if 'timer' in event:
            if isinstance(self._xaxis, ControlAxis) and isinstance(self._yaxis, ControlAxis):
                self._points.append(
                    (self._xaxis.get_current_value(), self._yaxis.get_current_value()))
            self._form.update()
