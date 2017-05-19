import time
import os
import sys
import numpy
import Queue
import threading
if os.uname()[1] == "pi":
    import picamera
    import picamera.array

import timer

DEBUG = True

CAMERA_RESOLUTION = (160, 128)
CAMERA_FRAMERATE = 30

class PiCamera:
    def __init__(self):
        self.cancel = False

    def start(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self._run).start()
        return self.queue

    def close(self):
        self.cancel = True

    def _run(self):
        with picamera.PiCamera() as camera:
            camera.resolution = CAMERA_RESOLUTION
            camera.framerate = CAMERA_FRAMERATE
            camera.start_preview()
            time.sleep(2)

            if self.cancel: return

            t = timer.Timer()
            with picamera.array.PiRGBArray(camera) as rawCapture:
                for _ in camera.capture_continuous(rawCapture, format='rgb', use_video_port=True):
                    image = rawCapture.array
                    if self.cancel: break
                    if not self.queue.empty(): self.queue.get(block=False)  # clear queue
                    self.queue.put(image)
                    rawCapture.truncate(0);
                    t.stamp()

            print "Camera timing:"
            t.print_summary()

class DummyCamera:
    def __init__(self):
        self.cancel = False

    def start(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self._run).start()
        return self.queue

    def close(self):
        self.cancel = True

    def _run(self,):
        (X, Y) = CAMERA_RESOLUTION
        t = timer.Timer()
        image = numpy.zeros((Y, X, 3), numpy.uint8)
        while not self.cancel:
            time.sleep(1.0 / CAMERA_FRAMERATE)
            if self.cancel: break
            if not self.queue.empty(): self.queue.get(block=False)  # clear queue
            self.queue.put(image)
            t.stamp()
        print "Camera timing:",
        t.print_summary()

def describe(image):
    (y, x, c) = image.shape
    return "%dx%dx%d" % (x, y, c)

def get_camera():
    if os.uname()[1] == "pi":
        return PiCamera()
    else:
        return DummyCamera()

def test():
    camera = get_camera()

    queue = camera.start()
    raw_input("Capturing, ENTER to finish")
    print describe(queue.get())
    camera.close()


if __name__ == "__main__":
    test()
