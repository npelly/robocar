import cv2
import io
import numpy
import PIL.Image

FORMAT_NUMPY_BGR = "numpy_bgr"
FORMAT_JPEG_BYTES = "bytearray_jpeg"

"""
data        (ndarray) numpy data array, dtype uint8
                shape (Y, X, 3)  -> bgr
                shape (Y, X)     -> greyscale
time        (float) source timestamp of image (seconds)
time_delta  (float) delta time between previous image and this image (seconds)
"""
class NumpyImage:
    def __init__(self, data, time, time_delta):
        assert type(data) == numpy.ndarray, "not a numpy array"
        if len(data.shape) == 3: assert data.shape[2] == 3, "3-dim must be 3-channel"
        assert data.dtype == numpy.uint8, "not 8-bit"

        self.data = data
        self.time = time
        self.time_delta = time_delta

    def __str__(self):
        (y, x, c) = self.data.shape
        return "%dx%dx%d@%.3f(%.3f)" % (x, y, c, self.time, self.time_delta)

    def to_jpeg_image(self):
        if len(self.data.shape) == 3:
            data = cv2.cvtColor(self.data, cv2.COLOR_BGR2RGB)
        else:
            data = self.data
        pil_image = PIL.Image.fromarray(data)
        image_io = io.BytesIO()
        pil_image.save(image_io, format='jpeg', subsampling=0, quality=95)
        jpeg_image = image_io.getvalue()  # bytearray
        return JpegImage(jpeg_image, self.time, self.time_delta)

class JpegImage:
    def __init__(self, data, time, time_delta):
        self.data = data
        self.time = time
        self.time_delta = time_delta

    def __str__(self):
        return "%dB@%.3f(%.3f)" % (len(self.data), self.time, self.time_delta)

    def to_numpy_image(self):
        image_io = io.BytesIO(self.data)
        pil_image = PIL.Image.open(image_io)
        image_array_rgb = numpy.array(pil_image)
        image_array_bgr = cv2.cvtColor(image_array_rgb, cv2.COLOR_RGB2BGR)
        return NumpyImage(image_array_bgr, self.time, self.time_delta)
