"""
Camera for the DCC1545M
"""

import sys
import ctypes
import time

from PyQt5.QtCore import QTimer

from pyforms import BaseWidget
from pyforms.Controls import ControlNumber, ControlPlayer, ControlDockWidget, ControlBase, ControlButton, ControlLabel, ControlSlider
from pyforms.gui.Controls.ControlPlayer.VideoGLWidget import VideoGLWidget

import cv2
import numpy as np
from qcamera import Camera
from framework import Sensor


class CameraSensor(Sensor):
    """
    The camera that looks at the laser
    Uses a Thorlabs DCC1545M
    Attempts to measure position, power, and frequency, with mixed accuracy
    """

    _camera = None
    _start_time = 0

    _widget = None
    _camera_window = None

    _timer = QTimer()

    _frame = 0

    _power = 0
    _frequency = 0
    _xpos = 0
    _ypos = 0

    _freq_start = 0
    _last_on = False

    def __init__(self):
        self._camera = ThorlabsDCx()
        self._measuring = False

        # Begin making the GUI shown when this sensor is selected
        self._widget = BaseWidget()

        self._widget.measure_time = ControlNumber(
            label="Measure Time (s)",
            default=1,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._widget.frame_time = ControlNumber(
            label="Frame Delay (s)",
            default=0.05,
            minimum=0,
            maximum=float('inf'),
            decimals=5
        )

        self._widget.threshold = ControlSlider(
            label="Threshold",
            default=18,
            min=0,
            max=255
        )

        self._widget.min_size = ControlSlider(
            label="Minimum Size",
            default=50,
            min=0,
            max=200,
        )

        self._widget.sample_radius = ControlSlider(
            label="Sample Radius",
            default=17,
            min=0,
            max=200
        )

        self._widget.show_button = ControlButton(
            label="Show Camera"
        )
        self._widget.show_button.value = self._show_camera

        self._timer.timeout.connect(self._get_frame)

    def __del__(self):
        self._camera.close()
        self._timer.stop()

    def get_custom_config(self):
        return self._widget

    def _show_camera(self):
        """
        Shows the camera window
        """
        print("Showing Camera")
        self._camera.start()
        if not isinstance(self._camera_window, CameraWindow):
            self._camera_window = CameraWindow()
            self._camera_window.before_close_event = self._hide_camera
        self._camera_window.show()
        self._timer.start(1000 / 60)

    def _hide_camera(self):
        """
        Hides the camera window
        """
        print("Hiding Camera")
        self._camera.stop()
        if isinstance(self._camera_window, CameraWindow):
            self._camera_window.hide()
        self._camera_window = None
        self._timer.stop()

    def _get_frame(self):
        """
        Get a frame from the camera and process it for position, power, and frequency,
        then put those values on the frame
        """
        img = self._camera.acquire_image_data()

        ret, thres = cv2.threshold(
            img, self._widget.threshold.value, 255, cv2.THRESH_BINARY)
        _, contours, _ = cv2.findContours(
            thres, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

        valid_countors = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < self._widget.min_size.value or w < self._widget.min_size.value:
                continue
            valid_countors += 1
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 0))

            # Position Calculation
            self._xpos = x + w / 2
            self._ypos = y + h / 2

            # Power Calculation
            mask = np.zeros(img.shape, np.uint8)
            cv2.circle(mask, (int(self._xpos), int(self._ypos)),
                       self._widget.sample_radius.value, (255, 255, 255), thickness=-1)
            self._power = cv2.mean(img, mask)[0]

        # Draw power circle
        cv2.circle(img, (int(self._xpos), int(self._ypos)),
                   self._widget.sample_radius.value, (255, 255, 255), thickness=1)

        # Frequency Calculation
        on = valid_countors > 0
        if on:
            if not self._last_on:
                delta_time = time.time() - self._freq_start
                self._frequency = 1 / delta_time
                self._freq_start = time.time()
        self._last_on = on

        # Put the measured values in the upper left of the frame
        cv2.putText(img, "Position: ({0}, {1})".format(self._xpos, self._ypos), (5, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), thickness=2)
        cv2.putText(img, "Power: {0}".format(self._power), (5, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), thickness=2)
        cv2.putText(img, "Frequency: {0}".format(self._frequency), (5, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), thickness=2)

        #cv2imwrite("{}.jpeg".format(self._frame), img)
        self._frame += 1

        # Update the GUI with the new frame
        if self._camera_window is not None:
            self._camera_window.update_frame(img)

    def begin_measuring(self):
        self._power = 0
        self._show_camera()
        self._start_time = time.time()

    def update(self):
        return [self._xpos, self._ypos, self._power, self._frequency]

    def is_done(self):
        return time.time() - self._start_time > self._widget.measure_time.value


class CameraWindow(BaseWidget):
    """
    Show a window with a CameraPlayer to view a camera
    """

    def __init__(self):
        super().__init__("Thorlabs Camera")

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


# Stuff for Thorlabs camera
# From qcamera, but modified for video rather than still images

def _chk(msg):
    """Check for errors from the C library."""
    if msg:
        if msg == 127:
            print("Out of memory, probably because of a memory leak!!!")
        if msg == 125:
            print("125: IS_INVALID_PARAMETER: One of the submitted " +
                  "parameters is outside the valid range or is not " +
                  "supported for this sensor or is not available in " +
                  "this mode.")
        if msg == 159:
            print(
                "159: IS_INVALID_BUFFER_SIZE: The image memory has an " +
                "inappropriate size to store the image in the desired format.")
        if msg == 178:
            raise RuntimeError("ThorlabsDCx: Transfer error: 178")
        if msg == 1:
            raise RuntimeError("Invalid camera handle.")
        if msg == -1:
            raise RuntimeError(
                "General error message: Likely the camera was disconnected!")
        print(
            "Unhandled error number: {}. \
            See DCx_User_and_SDK_Manual.pdf for details".format(msg))


# Structures used by the ctypes code:
class ImageFileParams(ctypes.Structure):
    _fields_ = [
        ("pwchFileName", ctypes.c_wchar_p),
        ("nFileType", ctypes.c_uint),
        ("nQuality", ctypes.c_uint),
        ("ppcImageMem;", ctypes.c_void_p),
        ("pnImageID", ctypes.c_uint),
        ("reserved", ctypes.c_byte * 32)
    ]


class IS_RECT(ctypes.Structure):
    _fields_ = [
        ("s32x", ctypes.c_int),
        ("s32y", ctypes.c_int),
        ("s32Width", ctypes.c_int),
        ("s32Height", ctypes.c_int)
    ]


class CamInfo(ctypes.Structure):
    _fields_ = [
        ("SerNo", ctypes.c_char * 12),
        ("ID", ctypes.c_char * 20),
        ("Version", ctypes.c_char * 10),
        ("Date", ctypes.c_char * 12),
        ("Select", ctypes.c_byte),
        ("Type", ctypes.c_byte),
        ("Reserved", ctypes.c_char)
    ]


class ThorlabsDCx(Camera):
    """Class for Thorlabs DCx series cameras."""

    def initialize(self, **kwargs):
        """Initialize the camera."""
        # Load the library.
        if 'win' in sys.platform:
            try:
                self.clib = ctypes.cdll.uc480_64
            except:
                self.clib = ctypes.cdll.uc480
        else:
            self.clib = ctypes.cdll.LoadLibrary('libueye_api.so')

        # Initialize the camera. The filehandle being 0 initially
        # means that the first available camera will be used. This is
        # not really the right way of doing things if there are
        # multiple cameras installed, but it's good enough for a lot
        # of cases.
        number_of_cameras = ctypes.c_int(0)
        _chk(self.clib.is_GetNumberOfCameras(ctypes.byref(number_of_cameras)))
        if number_of_cameras.value < 1:
            raise RuntimeError("No camera detected!")
        self.filehandle = ctypes.c_int(0)
        _chk(self.clib.is_InitCamera(
            ctypes.pointer(self.filehandle)))

        # Resolution of camera. (height, width)
        AOI = self.get_roi()
        print("Width, Height =%d, %d" % (AOI.s32Width, AOI.s32Height))
        self.shape = (AOI.s32Width, AOI.s32Height)
        self.props.load('thorlabs_dcx.json')

        # Allocate memory:
        # Declare variables for storing memory ID and memory start location:
        self.pid = ctypes.c_int()
        self.ppcImgMem = ctypes.c_char_p()

        # Setting monocrome 8 bit color mode
        # (otherwise we would get several identical readings per pixel!)
        _chk(self.clib.is_SetColorMode(self.filehandle, 6))

        # Allocate the right amount of memory:
        bitdepth = 8  # Camera is 8 bit.
        _chk(self.clib.is_AllocImageMem(
            self.filehandle, self.shape[0], self.shape[1], bitdepth,
            ctypes.byref(self.ppcImgMem),  ctypes.byref(self.pid)))

        # Tell the driver to use the newly allocated memory:
        _chk(self.clib.is_SetImageMem(
            self.filehandle, self.ppcImgMem, self.pid))

        # Enable autoclosing. This allows for safely closing the
        # camera if it is disconnected.
        _chk(self.clib.is_EnableAutoExit(self.filehandle, 1))

    def close(self):
        """Close the camera safely."""
        _chk(self.clib.is_ExitCamera(self.filehandle))

    def start(self):
        _chk(self.clib.is_CaptureVideo(self.filehandle, ctypes.c_int(100)))

    def stop(self):
        _chk(self.clib.is_StopLiveVideo(self.filehandle, ctypes.c_int(1)))

    def set_acquisition_mode(self, mode):
        """Set the image acquisition mode."""

    def get_display_mode(self):
        return self.clib.is_SetDisplayMode(self.filehandle, 0x8000)

    def acquire_image_data(self):
        """Code for getting image data from the camera should be
        placed here.

        """
        # Allocate memory for image:
        img_size = self.shape[0] * self.shape[1] / self.bins**2
        c_array = ctypes.c_char * int(img_size)
        c_img = c_array()

        # Take one picture: wait time is waittime * 10 ms:
        #waittime = c_int(100)
        #_chk(self.clib.is_FreezeVideo(self.filehandle, waittime))
        #_chk(self.clib.is_CaptureVideo(self.filehandle, waittime))

        # Copy image data from the driver allocated memory to the memory that we
        # allocated.
        _chk(self.clib.is_CopyImageMem(
            self.filehandle, self.ppcImgMem, self.pid, c_img))

        # Pythonize and return.
        img_array = np.frombuffer(c_img, dtype=ctypes.c_ubyte)
        img_array.shape = (1024, 1280)  # FIXME
        return img_array

    def get_trigger_mode(self):
        """Query the current trigger mode."""

    def set_trigger_mode(self, mode):
        """Setup trigger mode."""

    def trigger(self):
        """Send a software trigger to take an image immediately."""

    def open_shutter(self):
        """Open the shutter."""
        self.shutter_open = True

    def close_shutter(self):
        """Close the shutter."""
        self.shutter_open = False

    def update_exposure_time(self, t, units='ms'):
        """Set the exposure time."""
        IS_EXPOSURE_CMD_SET_EXPOSURE = 12
        nCommand = IS_EXPOSURE_CMD_SET_EXPOSURE
        Param = ctypes.c_double(t)
        SizeOfParam = 8
        _chk(self.clib.is_Exposure(
            self.filehandle, nCommand, ctypes.byref(Param), SizeOfParam))

    def get_gain(self):
        """Query the current gain settings."""

    def set_gain(self, gain, **kwargs):
        """Set the camera gain."""

    def get_roi(self):
        """Define the region of interest."""
        rectAOI = IS_RECT()
        _chk(self.clib.is_AOI(self.filehandle, 2, ctypes.pointer(rectAOI), 4 * 4))
        return rectAOI

    def save_image(self):
        size = ctypes.sizeof(ImageFileParams)
        params = ImageFileParams()
        params.nQuality = 0
        params.pwchFileName = u"mypic.bmp"
        params.ppcImageMem = None
        print("size", size)
        _chk(self.clib.is_ImageFile(self.filehandle, 2, ctypes.pointer(params), size))

    def get_parameters(self):
        _chk(self.clib.is_ParameterSet(self.filehandle, 4, "file.ini", None))
