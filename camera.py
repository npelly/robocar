import time
import os
import sys
import numpy
import Queue
import threading
import cv2

import util
import timer

DEBUG = True

CAMERA_RESOLUTION = (160, 128)
#CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 30

class CameraImage:
    def __init__(self, image, image_time, image_time_delta):
        self.image = image
        self.image_time = image_time
        self.image_time_delta = image_time_delta

    def __str__(self):
        (y, x, c) = self.image.shape
        return "%dx%dx%d@%.3f" % (x, y, c, self.timestamp)

class PiCamera:
    def __init__(self):
        import picamera
        import picamera.array
        self.cancel = False

    def __enter__(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self._run).start()
        return self.queue

    def __exit__(self, type, value, traceback):
        self.cancel = True

    def _run(self):
        with picamera.PiCamera() as camera:
            camera.resolution = CAMERA_RESOLUTION
            camera.framerate = CAMERA_FRAMERATE
            camera.start_preview()
            time.sleep(2)

            t = timer.Timer()
            first_timestamp = -1.0
            prev_timestamp = -1.0

            if self.cancel: return

            with picamera.array.PiRGBArray(camera) as rawCapture:
                for _ in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
                    timestamp = time.time()
                    if self.cancel: break

                    if first_timestamp < 0:
                        first_timestamp = timestamp
                        prev_timestamp = timestamp

                    image = rawCapture.array
                    if not self.queue.empty(): self.queue.get(block=False)  # clear queue
                    self.queue.put(CameraImage(image, timestamp - first_timestamp, timestamp - prev_timestamp))

                    rawCapture.truncate(0);
                    prev_timestamp = timestamp
                    t.stamp()

            print "Camera timing:"
            t.print_summary()

class DummyCamera:
    def __init__(self):
        self.cancel = False

    def __enter__(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self._run).start()
        return self.queue

    def __exit__(self, type, value, traceback):
        self.cancel = True

    def _run(self,):
        (X, Y) = CAMERA_RESOLUTION
        t = timer.Timer()
        image = numpy.zeros((Y, X, 3), numpy.uint8)
        first_timestamp = -1.0
        prev_timestamp = -1.0

        while not self.cancel:
            time.sleep(1.0 / CAMERA_FRAMERATE)
            if self.cancel: break
            if not self.queue.empty(): self.queue.get(block=False)  # clear queue
            self.queue.put(CameraImage(image, time.time() - base_timestamp))
            t.stamp()
        print "Camera timing:",
        t.print_summary()

def get_camera():
    if util.isRaspberryPi():
        return PiCamera()
    else:
        return DummyCamera()

def test():
    with get_camera() as camera_image_queue:
        camera_image = camera_image_queue.get()

    print camera_image
    cv2.imshow('camera test', camera_image.image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test()
