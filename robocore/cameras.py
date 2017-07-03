import io
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

import telemetry_utils
import util

class CameraImage:
    def __init__(self, image, image_time, image_time_delta):
        self.image = image
        self.time = image_time
        self.time_delta = image_time_delta
    def __str__(self):
        (y, x, c) = self.image.shape
        return "%dx%dx%d@%.3f" % (x, y, c, self.time)
    def to_telemetry_dict(self):
        return dict(time_delta=self.time_delta)

"""
Base class to manage Camera thread.
Sub-classes just need to impl ...
"""
class CameraBase:
    def __init__(self, config):
        config = config["Camera"]
        self.FRAMERATE = config.getint("FRAMERATE")
        self.RESOLUTION = (config.getint("RESOLUTION_WIDTH"), config.getint("RESOLUTION_HEIGHT"))
        self.FLIP = config.getboolean("FLIP")
        self.cancel = False

    def __enter__(self):
        self.queue = Queue.Queue(maxsize=1)
        threading.Thread(target=self.worker_thread).start()
        return self.queue

    def __exit__(self, type, value, traceback):
        self.cancel = True

    def wait_for_next_image(self, break_func):
        while not break_func():
            try:
                camera_image = self.queue.get(block=True, timeout=1.1)
                return camera_image, dict(time_delta=camera_image.time_delta)
            except Queue.Empty:
                print "warning: delayed camera image"
                continue
        return None, None

class PiCamera(CameraBase):
    def __init__(self, config):
        try:
            import picamera
            import picamera.array
        except ImportError:
            raise EnvironmentError

        CameraBase.__init__(self, config)

    def worker_thread(self):
        with picamera.PiCamera() as camera:
            if self.FLIP:
                camera.vflip = True
                camera.hflip = True
            camera.resolution = self.RESOLUTION
            camera.framerate = self.FRAMERATE
            time.sleep(0.9)   # camera power on and AWB settle time

            image_timing = util.LoopProfiler()

            if self.cancel: return

            with picamera.array.PiRGBArray(camera) as rawCapture:
                for _ in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
                    delta_time, cumulative_time = image_timing.time()

                    if self.cancel: break

                    image = rawCapture.array

                    if not self.queue.empty: self.queue.get_nowait()  # clear queue
                    self.queue.put(CameraImage(image, cumulative_time, delta_time))

                    rawCapture.truncate(0)

            print "Camera image timing:", image_timing

class DummyCamera(CameraBase):
    def worker_thread(self):
        loop = util.ConstantRateLoop(self.FRAMERATE)
        loop_profiler = util.LoopProfiler()

        pil_image = PIL.Image.new("RGB", self.RESOLUTION)
        fnt = PIL.ImageFont.load_default()
        draw = PIL.ImageDraw.Draw(pil_image)
        draw.text((1, 1), "<dummy camera>", font=fnt, fill=(255, 255, 255))

        while not self.cancel:
            loop.sleep()
            delta_time, cumulative_time = loop_profiler.time()

            if self.cancel: break

            draw.rectangle([(1, 20), self.RESOLUTION], fill=(0, 0, 0))
            draw.text((1, 20), str(cumulative_time), font=fnt, fill=(255, 255, 255))
            image = numpy.asarray(pil_image)

            if not self.queue.empty: self.queue.get_nowait()  # clear queue
            self.queue.put(CameraImage(image, cumulative_time, delta_time))

        print "Camera image timing:", loop_profiler


class ReplayCamera(CameraBase):
    def __init__(self, config, telemetry_session_path):
        CameraBase.__init__(self, config)

        try:
            with io.open(telemetry_session_path, 'rb') as file:
                self.telemetry_session = telemetry_utils.load_session(file)
        except (OSError, IOError, AssertionError):
            self.telemetry_session = None
            print "ERROR: failed to load telemetry file %s" % telemetry_session_path

    def worker_thread(self):
        if not self.telemetry_session: return

        for atom in self.telemetry_session["atoms"]:
            if self.cancel: break

            image = atom["image"]
            image_io = io.BytesIO(image)
            pil_image = PIL.Image.open(image_io)
            image_array = numpy.array(pil_image)

            camera_image = CameraImage(image_array, atom["time"], atom["time_delta"])

            if self.cancel: break

            self.queue.put(camera_image)  # will block until queue ready
