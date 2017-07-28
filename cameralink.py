"""
Camera for a Cameralink Sensor
"""

import sys
import ctypes
import time

from PyQt5 import QtCore
from PyQt5 import Qt
from PyQt5.QtCore import QTimer, QObject, QThread

from pyforms import BaseWidget
from pyforms.Controls import ControlNumber, ControlPlayer, ControlDockWidget, ControlBase, ControlButton, ControlLabel, ControlSlider
from pyforms.gui.Controls.ControlPlayer.VideoGLWidget import VideoGLWidget

import cv2
import numpy as np
from framework import Sensor


class CameraLinkSensor(Sensor):
    """
    The camera that looks at the laser
    Uses a Thorlabs DCC1545M
    Attempts to measure position, power, and frequency, with mixed accuracy
    """

    _camera = None
    _camera_thread = None

    _widget = None
    _camera_window = None

    _data = []

    def __init__(self):
        # Begin making the GUI shown when this sensor is selected
        self._widget = BaseWidget()

        self._widget.threshold = ControlSlider(
            label="Threshold",
            default=18,
            min=0,
            max=255
        )
        self._widget.threshold.changed_event = self._update_params

        self._widget.min_size = ControlSlider(
            label="Minimum Size",
            default=50,
            min=0,
            max=200,
        )
        self._widget.min_size.changed_event = self._update_params

        self._widget.sample_radius = ControlSlider(
            label="Sample Radius",
            default=17,
            min=0,
            max=200
        )
        self._widget.sample_radius.changed_event = self._update_params

        self._widget.show_button = ControlButton(
            label="Show Camera"
        )
        self._widget.show_button.value = self._show_camera

        self._widget.before_close_event = self._hide_camera

    def __del__(self):
        if self._camera_window is not None:
            self._camera_window.close()

    def update_events(self, events):
        if 'close' in events:
            self._hide_camera()

    def get_custom_config(self):
        return self._widget

    def process_data(self, data, frame):
        if self._camera_window is not None:
            self._camera_window.update_frame(frame)
        self._data = data

    def _update_params(self):
        if self._camera_thread is not None and self._camera is not None:
            QtCore.QMetaObject.invokeMethod(self._camera, 'update_params', Qt.Qt.QueuedConnection, 
                QtCore.Q_ARG(int, self._widget.threshold.value), 
                QtCore.Q_ARG(int, self._widget.min_size.value),
                QtCore.Q_ARG(int, self._widget.sample_radius.value)
            )

    def _show_camera(self):
        """
        Shows the camera window
        """
        print("Showing Camera")
        if not isinstance(self._camera_window, CameraWindow):
            self._camera_window = CameraWindow()
            self._camera_window.before_close_event = self._hide_camera
        self._camera_window.show()

        if self._camera is None or self._camera_thread is None:
            self._camera_thread = QThread()

            self._camera = CameraThread()
            self._camera.frame_ready.connect(self.process_data)

            self._camera.moveToThread(self._camera_thread)

            self._camera_thread.started.connect(self._camera.start_processing)

        self._camera_thread.start()

    def _hide_camera(self):
        """
        Hides the camera window
        """
        print("Hiding Camera")
        self._camera.stop()
        if isinstance(self._camera_window, CameraWindow):
            self._camera_window.close()
        self._camera_window = None
        if self._camera_thread is not None and self._camera is not None:
            QtCore.QMetaObject.invokeMethod(
                self._camera, 'stop', Qt.Qt.QueuedConnection)

    def begin_measuring(self):
        self._power = 0
        if self._camera_window is None or not self._camera_window.visible:
            self._show_camera()

    def update(self):
        return self._data

    def finish_measuring(self):
        pass

    def get_headers(self):
        return ["Camera X", "Camera Y", "Camera Power", "Camera Frequency", "Camera FPS"]


class CameraWindow(BaseWidget):
    """
    Show a window with a CameraPlayer to view a camera
    """

    def __init__(self):
        super().__init__("Cameralink")

        self._camera = CameraPlayer()
        self.formset = [
            "Camera",
            '_camera'
        ]

    def update_frame(self, frame):
        """
        Update the shown image with a new frame
        """
        self._camera.update_frame(frame)


class CameraPlayer(ControlBase):
    """
    Displays some numpy arrarys as a camera feed
    """

    def init_form(self):
        self._form = VideoGLWidget()

    def update_frame(self, frame):
        """
        Update the frame displayed
        """
        if isinstance(frame, list):
            self._form.paint(frame)
        else:
            self._form.paint([frame])


class CameraThread(QObject):

    frame_ready = QtCore.pyqtSignal(list, np.ndarray)

    _clib = None
    _pdv = None

    _last_on = 0
    _on = False
    _freq_start = 0
    _last_frame = 0
    _fps = 0
    _frame = 0

    _power = 0
    _frequency = 0
    _xpos = 0
    _ypos = 0

    _timeouts = 0
    _recovering_timeout = False

    _threshold = 18
    _min_size = 50
    _sample_radius = 17

    _timer = None

    @QtCore.pyqtSlot()
    def start_processing(self):

        self._clib = ctypes.cdll.LoadLibrary('pdvlib.dll')
        self._pdv = self._clib.pdv_open(b'pdv', 0)
        self._clib.pdv_multibuf(self._pdv, 4)
        self._clib.pdv_wait_image.restype = np.ctypeslib.ndpointer(dtype=ctypes.c_uint8, shape=(512, 640))
        self._clib.pdv_image.restype = np.ctypeslib.ndpointer(dtype=ctypes.c_uint8, shape=(512, 640))

        self._timer = QTimer()
        self._timer.timeout.connect(self._process)
        self._timer.start()

        self._clib.pdv_start_images(self._pdv, 0)

    def _process(self):
        """
        Get a frame from the camera and process it for position, power, and frequency,
        then put those values on the frame
        """
        now = time.time()
        #print("Getting Frame")
        imgorg = self._clib.pdv_wait_image(self._pdv)
        #img = self._clib.pdv_image(self._pdv)

        #cv2.imwrite("out{}.png".format(self._frame), img)

        timeouts = self._clib.pdv_timeouts(self._pdv)
        if timeouts > self._timeouts:
            self._clib.pdv_timeout_restart(self._pdv, True)
            self._timeouts = timeouts
            self._recovering_timeout = True
            print("Timeout")
        elif self._recovering_timeout:
            self._clib.pdv_timeout_restart(self._pdv, True)
            self._recovering_timeout = False

        delta_time_fps = now - self._last_frame
        if delta_time_fps != 0:
            self._fps = 1 / delta_time_fps

        self._last_frame = now

        #cv2.imshow("img", img)
        #cv2.waitKey(1)
        
        img = cv2.blur(imgorg, (7, 7))

        img64 = cv2.Sobel(img, cv2.CV_64F, 1, 1, ksize=5)
        #img64 = cv2.Laplacian(img, cv2.CV_64F, ksize=5)

        img = np.uint8(np.absolute(img64))

        _, img = cv2.threshold(img, self._threshold, 255, cv2.THRESH_BINARY)
        _, contours, _ = cv2.findContours(
            img, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

        points = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w*h < self._min_size:
                continue
            #cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 0))

            points.append((int(x + w/2), int(y + h/2)))

        #print(len(points))

        if len(points) > 0:
            x, y, w, h = cv2.boundingRect(np.array(points))
            cv2.rectangle(imgorg, (x, y), (x + w, y + h), (255, 255, 0))

            self._xpos = x
            self._ypos = y
        

        '''
        # Put the measured values in the upper left of the frame
        cv2.putText(img, "Position: ({0}, {1})".format(self._xpos, self._ypos), (5, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness=2)
        cv2.putText(img, "Power: {0}".format(self._power), (5, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness=2)
        cv2.putText(img, "Frequency: {0}".format(self._frequency), (5, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness=2)
        cv2.putText(img, "FPS: {0}".format(self._fps), (5, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness=2)
        cv2.putText(img, "Timeouts: {0}".format(self._timeouts), (5, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness=2)
        '''

        self.frame_ready.emit(
            [self._xpos, self._ypos, self._power, self._frequency, self._fps], imgorg)

        self._frame += 1

    @QtCore.pyqtSlot()
    def stop(self):
        self._clib.pdv_start_images(self._pdv, 1)
        if self._timer is not None:
            self._timer.stop()

    @QtCore.pyqtSlot(int, int, int)
    def update_params(self, threshold, min_size, sample_radius):
        self._threshold = threshold
        self._min_size = min_size
        self._sample_radius = sample_radius
