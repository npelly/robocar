import picamera
import picamera.array
import time
import cv2
import motorcontrol
import processimage
import select
import sys
import Queue
import threading
import mytimer

class Pi:
    _motor = motorcontrol.MotorControl()
    _cancel = False
    _motorInstructions = Queue.Queue(maxsize = 1)

    def __init__(self):
        threading.Thread(target=self._cameraThread).start()
        threading.Thread(target=self._motorThread).start()
        self._keyboardCancelThread()

    def _keyboardCancelThread(self):
        sys.stdin.read(1)
        self._cancel = True
        try:
            self._motorInstructions.get(block=False)
        except Queue.Empty:
            pass
        self._motorInstructions.put((0, 0, 0), block=False)

    def _cameraThread(self):
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.framerate = 30
            camera.start_preview()
            time.sleep(2)


            with picamera.array.PiRGBArray(camera) as rawCapture:
                frame = 0
                t = mytimer.MyTimer()
                t.stamp()
                for _ in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
                    image = rawCapture.array
                    (left, right, duration) = processimage.process(image)
                    try:
                        self._motorInstructions.get(block=False) # clear old instruction
                    except Queue.Empty:
                        pass
                    self._motorInstructions.put((left, right, duration), block=False)
                    rawCapture.seek(0);

                    frame += 1
                    if frame % 30 == 0:
                        t.stamp("frame %d" % frame)

                    if self._cancel:
                        t.printStamps()
                        break


            while not self._cancel:
                t = mytimer.MyTimer()
                t.stamp()
                with picamera.array.PiRGBArray(camera) as rawCapture:
                    t.stamp("open rawCapture")
                    camera.capture(rawCapture, format='bgr', use_video_port=True)
                    t.stamp("capture()")
                    image = rawCapture.array
                    print image.shape
                    (left, right, duration) = processimage.process(image)
                t.stamp("processImage()")
                self._motorInstructions.put((left, right, duration), block=True)
                t.stamp("push instruc")

                t.printStamps()

    def _motorThread(self):
        while not self._cancel:
            (left, right, duration) = self._motorInstructions.get(block=True)
            if (self._cancel):
                break
            self._motor.drive(left, right)
            time.sleep(duration)
            self._motor.stop()
        self._motor.close()


if __name__ == "__main__":
    pi = Pi()
