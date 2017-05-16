import io
import time
import picamera


"""
Basic Capture.
destination can be
    filename
    stream (socket, BytesIO, open file etc)
"""
def basicCapture(destination):
    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.start_preview()
        time.sleep(2)
        camera.capture(destination, format='jpeg')  # flushes to file/stream


"""
Capture to numpy array / OpenCV image
"""
def captureToNumpy(nparray):
    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.start_preview()
        time.sleep(2)
        with picamera.array.PiRGBArray(camera) as stream:
            camera.capture(stream, format='bgr')
            image = stream.array  # OpenCV image (numpy array in BGR order)


"""
Resize.
More efficient for Pi's GPU to do it. Use resize=(x, y) in capture().
"""

"""
Consistency
exposure time: shutter_speed. try querying exposure_speed
exposure gains: analog_gain, digital_gain. Let them settle to reasonable
                values (>1) then set exposure_mode to 'off'
white balance: set awb_mode to 'off' then set awb_gains to a (red, blue) tuple
optionally set iso to fixed value. [100,200] for daytime. [400,800] low light
"""
with picamera.PiCamera() as camera:
    camera.resolution = (1280, 720)
    camera.framerate = 30
    # Wait for analog gain to settle on a higher value than 1
    while camera.analog_gain <= 1:
        time.sleep(0.1)
    # Now fix the values
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
    # Finally, take several photos with the fixed settings
    camera.capture_sequence(['image%02d.jpg' % i for i in range(10)])


# Capture to Stream
myStream = io.BytesIO()
with picamera.PiCamera() as camera:
    camer


# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
rawCapture = PiRGBArray(camera)

# allow the camera to warmup
time.sleep(0.1)

# grab an image from the camera
camera.capture("test-video-image-2.jpg", use_video_port=False)
image = rawCapture.array

# display the image on screen and wait for a keypress
#print "captured image ", image.shape
#cv2.imshow("Image", image)
#cv2.waitKey(0)
