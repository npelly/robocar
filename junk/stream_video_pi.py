import socket
import time
import picamera
import picamera.array
import io
import util

# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ("10.0.0.20", 1234)

# Make a file-like object out of the connection
#connection = client_socket.makefile('wb')

class UdpOutput():
    def __init__(self):
        self.timer = util.HistogramTimer()
    def write(self, s):
        self.timer.event()
        print "write", len(s)
        client_socket.sendto(s, server_address)
    def flush(self):
        print "flush"
        print self.timer.summary()


try:
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 24
        #camera.start_preview()
        time.sleep(2)

        camera.start_recording(UdpOutput(), format='h264', resize=(320,240), splitter_port=2)
        camera.annotate_text = "hello world"

        timer = util.HistogramTimer()

        with picamera.array.PiRGBArray(camera) as rawCapture:
            for _ in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
                timer.event()
                rawCapture.truncate(0)
                if timer.count >= 300:
                    break

        camera.stop_recording(splitter_port=2)
        print timer.summary(include_rate=True)
finally:
    pass
