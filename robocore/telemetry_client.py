import io
import numpy
import PIL.Image
import Queue
import socket
import threading
import websocket

import telemetry_utils
import util

class TelemetryClient:
    def __init__(self, server):
        self.server = "ws://%s/api/telemetry" % server
        self.running = False

    def __enter__(self):
        if not self.server: return

        self.queue = Queue.Queue()
        self.running = True
        threading.Thread(target=self._run).start()

    def __exit__(self, type, value, traceback):
        if not self.running: return

        self.running = False
        self.queue.put((None, None, None))  # unblock thread

    def process(self, camera_image, observation, instruction):
        if not self.running: return

        self.queue.put((camera_image, observation, instruction))

    def _run(self):
        try:
            web_socket = websocket.create_connection(self.server)
        except socket.error:
            print "WARNING: failed to connect to telemetry server:", self.server
            self.running = False
            return

        session = telemetry_utils.create_session()
        web_socket.send_binary(telemetry_utils.dump_session(session))

        profiler = util.SectionProfiler()

        while self.running:
            camera_image, observation, instruction = self.queue.get()

            if not self.running: break

            if self.queue.qsize() > 10:
                print "WARNING: telemetry is %d frames behind" % self.queue.qsize()

            with profiler:
                time = camera_image.time

                # camera_image.image is numpy.ndarray, dtype=uint8
                pil_image = PIL.Image.fromarray(camera_image.image)
                image_io = io.BytesIO()
                pil_image.save(image_io, format='jpeg')
                image = image_io.getvalue()  # bytearray

                atom = telemetry_utils.create_atom(time, image)
                atom["time_delta"] = camera_image.time_delta
                atom["cross_track_error"] = observation.cross_track_error
                atom["visible"] = observation.visible
                atom["left_power"] = instruction.left_power
                atom["right_power"] = instruction.right_power

                out = telemetry_utils.dump_atom(atom)

                web_socket.send_binary(out)

        web_socket.close()
        print "Telemetry Client Timing:", profiler