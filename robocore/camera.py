import time
import os
import sys
import numpy
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import Queue
import threading
import cv2
import argparse
import socket

import util

if util.isRaspberryPi():
    import picamera
    import picamera.array

DEBUG = True

class CameraImage:
    def __init__(self, image, image_time, image_time_delta):
        self.image = image
        self.time = image_time
        self.time_delta = image_time_delta

    def __str__(self):
        (y, x, c) = self.image.shape
        return "%dx%dx%d@%.3f" % (x, y, c, self.time)

class UdpSink:
    # Receive with
    # /Applications/VLC.app/Contents/MacOS/VLC --demux h264 udp://:8002
    def __init__(self, server_address):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = server_address
        print server_address
    def write(self, out):
        self.udp_socket.sendto(out, self.server_address)

class PiCamera:
    def __init__(self, resolution, framerate, stream=None):
        self.cancel = False
        self.framerate = framerate
        self.resolution = resolution
        self.stream = stream

    def __enter__(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self._run).start()
        return self.queue

    def __exit__(self, type, value, traceback):
        self.cancel = True

    def _run(self):
        with picamera.PiCamera() as camera:
            camera.resolution = self.resolution
            camera.framerate = self.framerate
            time.sleep(0.9)   # camera power on and AWB settle time

            image_timing = util.LoopProfiler()

            if self.cancel: return

            if self.stream: camera.start_recording(UdpSink(self.stream), format='h264', splitter_port=2)

            with picamera.array.PiRGBArray(camera) as rawCapture:
                for _ in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
                    delta_time, cumulative_time = image_timing.time()

                    if self.cancel: break

                    image = rawCapture.array

                    if not self.queue.empty(): self.queue.get(block=False)  # clear queue
                    self.queue.put(CameraImage(image, cumulative_time, delta_time))

                    rawCapture.truncate(0)

            if self.stream: camera.stop_recording(splitter_port=2)
            print "Camera image timing:", image_timing

class DummyCamera:
    def __init__(self, resolution, framerate, stream=None):
        self.cancel = False
        self.framerate = framerate
        self.resolution = resolution

    def __enter__(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self._run).start()
        return self.queue

    def __exit__(self, type, value, traceback):
        self.cancel = True

    def _run(self,):
        (X, Y) = self.resolution
        loop = util.ConstantRateLoop(self.framerate)
        loop_profiler = util.LoopProfiler()

        pil_image = PIL.Image.new("RGB", (X, Y))
        fnt = PIL.ImageFont.load_default()
        draw = PIL.ImageDraw.Draw(pil_image)
        draw.text((1, 1), "<dummy camera>", font=fnt, fill=(255, 255, 255))

        while not self.cancel:
            loop.sleep()
            delta_time, cumulative_time = loop_profiler.time()

            if self.cancel: break

            draw.rectangle([(1, 20), (X, Y)], fill=(0, 0, 0))
            draw.text((1, 20), str(cumulative_time), font=fnt, fill=(255, 255, 255))
            image = numpy.asarray(pil_image)

            if not self.queue.empty(): self.queue.get(block=False)  # clear queue
            self.queue.put(CameraImage(image, cumulative_time, delta_time))

        print "Camera timing:", loop_profiler
"""
if __name__ == "__main__":
    print "ENTER to stop (and show last image)"

    parser = argparse.ArgumentParser()
    parser.add_argument("--stream_address", help="UDP stream HOST")
    args = parser.parse_args()
    if args.stream_address:
        (host, port) = args.stream_address.split(":")
        stream_address = host, int(port)
    else:
        stream_address = None

    with get_camera(stream_address) as camera_image_queue:
        while not util.check_stdin():
            camera_image = camera_image_queue.get()

    print camera_image
    cv2.imshow('camera test', camera_image.image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
"""
