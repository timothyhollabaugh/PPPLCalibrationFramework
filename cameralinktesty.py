
import ctypes
import numpy as np
import cv2

clib = ctypes.cdll.LoadLibrary('pdvlib.dll')

pdv = clib.pdv_open(b'pdv', 0)

print(clib.pdv_get_width(pdv))
print(clib.pdv_get_height(pdv))


# Set up the 'optimal' 4 buffers to use
clib.pdv_multibuf(pdv, 4)

#clib.pdv_image.restype = np.ctypeslib.ndpointer(dtype=ctypes.c_uint8, shape=(512, 640, 1))
#img = clib.pdv_image(pdv)

#cv2.imshow('img', img)
#cv2.waitKey(0)
np.set_printoptions(formatter={'int':hex})

clib.pdv_wait_image.restype = np.ctypeslib.ndpointer(dtype=ctypes.c_uint16, shape=(512, 1280, 1))

clib.pdv_start_images(pdv, 0)

while True:
    img = clib.pdv_wait_image(pdv)
    img = img[:, ::2]
    img = np.left_shift(img, 2)
    #print(img)
    cv2.imshow('img', img)
    if cv2.waitKey(1) == 27:
        break  # esc to quit

clib.pdv_start_images(pdv, 1)
