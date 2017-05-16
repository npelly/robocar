import picamera
import picamera.array
import PIL.Image
import time
import cv2

with picamera.PiCamera() as camera:
    camera.resolution = (640, 480)
    camera.framerate = 32
    while (1):
        with picamera.array.PiRGBArray(camera) as rawCapture:
            camera.capture(rawCapture, format='bgr')
            image = rawCapture.array
            print "."

            cv2.imshow("Image", image)
            cv2.waitKey(0)
