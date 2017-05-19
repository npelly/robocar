import picamera
import picamera.array
import mytimer
import time

with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    camera.framerate = 30
    camera.start_preview()
    time.sleep(2)

    t = mytimer.MyTimer()
    t.stamp()
    i = 0
    with picamera.array.PiRGBArray(camera) as rawCapture:
        t.stamp("open rawCapture")
        for foo in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
            t.stamp("%d" % i)
            i += 1
            if (i >= 120): break
            rawCapture.seek(0)

    t.printStamps()

with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    camera.framerate = 30
    camera.start_preview()
    time.sleep(2)

    t = mytimer.MyTimer()
    t2 = mytimer.MyTimer()
    t.stamp()
    t2.stamp()
    i = 0
    for i in range(120):
        with picamera.array.PiRGBArray(camera) as rawCapture:
            camera.capture(rawCapture, format='bgr', use_video_port=True)
            t.stamp("%d" % i)

    t2.stamp("done")
    t.printStamps()
    t2.printStamps()
