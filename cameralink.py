"""
Camera for a Cameralink Sensor
"""

import time
import ctypes

from PyQt5 import QtCore
from PyQt5 import Qt
from PyQt5.QtCore import QTimer, QObject, QThread

from pyforms import BaseWidget
from pyforms.Controls import ControlBase, ControlButton, ControlSlider, ControlBoundingSlider,\
    ControlCheckBox
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
    _save_dir = ''

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

        self._widget.on_threshold = ControlSlider(
            label="Frequency Threshold",
            default=17,
            min=0,
            max=255
        )
        self._widget.on_threshold.changed_event = self._update_params

        self._widget.x_bounds = ControlBoundingSlider(
            label="X Bounds",
            default=[0, 640],
            min=0,
            max=640,
            horizontal=True
        )
        self._widget.x_bounds.convert_2_int = True
        self._widget.x_bounds.changed_event = self._update_params

        self._widget.y_bounds = ControlBoundingSlider(
            label="Y Bounds",
            default=[0, 512],
            min=0,
            max=512,
            horizontal=True
        )
        self._widget.y_bounds.convert_2_int = True
        self._widget.y_bounds.changed_event = self._update_params

        self._widget.recording = ControlCheckBox(
            label="Record"
        )
        self._widget.recording.changed_event = self._update_params

    def __del__(self):
        if self._camera_window is not None:
            self._camera_window.close()

    def update_events(self, events):
        if 'close' in events:
            self._hide_camera()

    def get_custom_config(self):
        return self._widget

    def process_data(self, data, frame):
        """
        Updates the latest frame with the newest frame
        """
        if self._camera_window is not None:
            self._camera_window.update_frame(frame)
        self._data = data

    def _update_params(self):
        if self._camera_thread is not None and self._camera is not None:
            QtCore.QMetaObject.invokeMethod(self._camera, 'update_params', Qt.Qt.QueuedConnection,
                                            QtCore.Q_ARG(
                                                int, self._widget.threshold.value),
                                            QtCore.Q_ARG(
                                                int, self._widget.min_size.value),
                                            QtCore.Q_ARG(
                                                int, self._widget.on_threshold.value),
                                            QtCore.Q_ARG(
                                                int, self._widget.x_bounds.value[0]),
                                            QtCore.Q_ARG(
                                                int, self._widget.x_bounds.value[1]),
                                            QtCore.Q_ARG(
                                                int, self._widget.y_bounds.value[0]),
                                            QtCore.Q_ARG(
                                                int, self._widget.y_bounds.value[1]),
                                            QtCore.Q_ARG(
                                                str, self._save_dir))

    def _show_camera(self):
        """
        Shows the camera window
        """
        print("Showing Camera")
        if not isinstance(self._camera_window, CameraWindow):
            self._camera_window = CameraWindow()
            self._camera_window.before_close_event = self._hide_camera
        self._camera_window.show()

    def _hide_camera(self):
        """
        Hides the camera window
        """
        print("Hiding Camera")
        if isinstance(self._camera_window, CameraWindow):
            self._camera_window.close()
        self._camera_window = None

    def _start_camera(self):
        """
        Starts the camera processing
        """
        print("Starting Camera")
        if self._camera is None or self._camera_thread is None:
            self._camera_thread = QThread()

            self._camera = CameraThread()

            self._camera.moveToThread(self._camera_thread)

            self._camera.frame_ready.connect(self.process_data)
            self._camera_thread.started.connect(self._camera.init)
            self._camera_thread.start()

        QtCore.QMetaObject.invokeMethod(
            self._camera, 'start_processing', Qt.Qt.QueuedConnection)
        
        self._update_params()

    def _stop_camera(self):
        """
        Stops the camera processing
        """
        print("Stopping Camera")
        if self._camera_thread is not None and self._camera is not None:
            QtCore.QMetaObject.invokeMethod(
                self._camera, 'stop', Qt.Qt.QueuedConnection)

    def begin_live_data(self):
        print("Starting live camera")
        self._save_dir = ''
        self._show_camera()
        self._start_camera()

    def get_live_data(self):
        return self._data

    def stop_live_data(self):
        print("Stopping live camera")
        self._stop_camera()
        self._hide_camera()

    def begin_measuring(self, save_dir):
        print("Camera Beginning measuring")
        self._save_dir = save_dir
        self._hide_camera()
        self._start_camera()

    def finish_measuring(self):
        print("Camera fininshing measuring")
        self._save_dir = ''
        self._stop_camera()

    def get_live_headers(self):
        return ["Camera X", "Camera Y", "Camera Power", "Camera Frequency", "Camera FPS",
                "Camera Frame"]


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
    """
    Runs a thread to capture camera
    """

    frame_ready = QtCore.pyqtSignal(list, np.ndarray)

    _clib = None
    _pdv = None

    _freq_start = 0
    _last_frame = 0
    _fps = 0
    _frame = 0

    _power = 0
    _frequency = 0
    _xpos = 0
    _ypos = 0

    _on = False
    _last_on = False

    _cycle_start = 0

    _timeouts = 0
    _recovering_timeout = False

    _threshold = 18
    _min_size = 50
    _on_threshold = 17
    _x_min = 0
    _x_max = 640
    _y_min = 0
    _y_max = 512
    _save_dir = None

    _timer = None

    @QtCore.pyqtSlot()
    def init(self):
        """
        Does one time initing of the dll
        """
        self._clib = ctypes.cdll.LoadLibrary('pdvlib.dll')
        self._pdv = self._clib.pdv_open(b'pdv', 0)
        self._clib.pdv_multibuf(self._pdv, 4)

        self._clib.pdv_wait_image.restype = np.ctypeslib.ndpointer(
            dtype=ctypes.c_uint16, shape=(512, 1280))
        self._clib.pdv_image.restype = np.ctypeslib.ndpointer(
            dtype=ctypes.c_uint16, shape=(512, 1280))

    @QtCore.pyqtSlot()
    def start_processing(self):
        """
        Begins processing
        """
        print("Camera Thread Beginning")

        self._clib.pdv_start_images(self._pdv, 0)

        self._timer = QTimer()
        self._timer.timeout.connect(self._process)
        self._timer.start()

        print("Camera thread began")

    def _process(self):
        """
        Get a frame from the camera and process it for position, power, and frequency,
        then put those values on the frame
        """
        imggrey = self._clib.pdv_wait_image(self._pdv)
        #imggrey = self.timeouts = self._clib.pdv_timeouts(self._pdv)
        #imggrey = np.zeros(dtype=ctypes.c_uint16, shape=(512, 1280))

        timeouts = self._clib.pdv_timeouts(self._pdv)
        if timeouts > self._timeouts:
            self._clib.pdv_timeout_restart(self._pdv, True)
            self._timeouts = timeouts
            self._recovering_timeout = True
            print("Cameralink Timeout")
        elif self._recovering_timeout:
            self._clib.pdv_timeout_restart(self._pdv, True)
            self._recovering_timeout = False_clib.pdv_image(self._pdv)

        imggrey = imggrey[:, ::2]

        now = time.time()

        if self._save_dir is not None and self._save_dir != '':
            # Scanning mode, save but no processing
            imgsave = np.uint8(imggrey)
            cv2.imwrite("{}/{}-{}.png".format(self._save_dir,
                                              self._frame, now), imgsave)
        else:
            # Live mode, process but don't save
            imgorg = cv2.cvtColor(imggrey, cv2.COLOR_GRAY2RGB)

            delta_time_fps = now - self._last_frame
            if delta_time_fps != 0:
                self._fps = 1 / delta_time_fps

            self._last_frame = now

            if self._x_max - self._x_min <= 0:
                if self._x_max < 640:
                    self._x_max += 1
                if self._x_min > 0:
                    self._x_min -= 1

            if self._y_max - self._y_min <= 0:
                if self._y_max < 512:
                    self._y_max += 1
                if self._y_min > 0:
                    self._y_min -= 1

            cv2.rectangle(imgorg, (self._x_min, self._y_min),
                          (self._x_max, self._y_max), (0, 0, 255))

            img = imggrey[self._y_min:self._y_max, self._x_min:self._x_max]

            img = np.uint8(img)

            self._power = int(np.amax(img))

            _, img = cv2.threshold(img, self._threshold,
                                   255, cv2.THRESH_BINARY)

            _, contours, _ = cv2.findContours(
                img, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

            #imgorg[self._y_min:self._y_max, self._x_min:self._x_max, 2] = img

            points = []

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                if w * h < self._min_size:
                    continue

                x += self._x_min
                y += self._y_min

                cv2.rectangle(imgorg, (x, y), (x + w, y + h), (255, 255, 0))

                # points.append((int(x + w/2), int(y + h/2)))
                points.extend(contour)

            # print(len(points))

            if len(points) > 0:
                nppoints = np.array(points)

                x, y, w, h = cv2.boundingRect(nppoints)

                x += self._x_min
                y += self._y_min

                cv2.rectangle(imgorg, (x, y), (x + w, y + h), (255, 0, 0))

                self._xpos = x
                self._ypos = y

                #self._power = cv2.contourArea(nppoints)
            else:
                self._xpos = 0
                self._ypos = 0

                self._power = 0

            self._on = self._power > self._on_threshold

            if self._on and not self._last_on:
                delta_time = now - self._cycle_start
                if delta_time != 0:
                    self._frequency = 1 / delta_time
                    self._cycle_start = now

            self._last_on = self._on

            self.frame_ready.emit(
                [self._xpos, self._ypos, self._power,
                 self._frequency, self._fps, self._frame],
                imgorg)

        self._frame += 1

    @QtCore.pyqtSlot()
    def stop(self):
        """
        Stops the camerza
        """
        self._clib.pdv_start_images(self._pdv, 1)
        if self._timer is not None:
            self._timer.stop()

    @QtCore.pyqtSlot(int, int, int, int, int, int, int, str)
    def update_params(self, threshold, min_size, on_threshold, x_min, x_max, y_min, y_max,
                      save_dir):
        """
        Updates the parameters used for processing
        """
        print("Updating Paramaters")
        self._threshold = threshold
        self._min_size = min_size
        self._on_threshold = on_threshold
        self._x_min = x_min
        self._x_max = x_max
        self._y_min = y_min
        self._y_max = y_max
        self._save_dir = save_dir
