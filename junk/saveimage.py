import time
import picamera
import mytimer
import sys

with picamera.PiCamera() as camera:
    filename = sys.argv[1]
    timer = mytimer.MyTimer()

    camera.resolution = (640, 480)
    camera.framerate = 15
    camera.start_preview()
    time.sleep(2)

    timer.stamp()
    camera.capture(filename, format='jpeg', use_video_port=False)
    timer.stamp("capture")

timer.printStamps()
print "saved to", filename
