import io
import numpy
import PIL.Image
import Queue
import socket
import threading
import websocket

import telemetry
import util

class TelemetryProducer:
    def __init__(self, server):
        self.server = server
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

        profiler = util.SectionProfiler()

        while self.running:
            camera_image, observation, instruction = self.queue.get()

            if not self.running: break

            with profiler:
                time = camera_image.time

                # camera_image.image is numpy.ndarray, dtype=uint8
                pil_image = PIL.Image.fromarray(camera_image.image)
                image_io = io.BytesIO()
                pil_image.save(image_io, format='png')
                image = image_io.getvalue()  # bytearray

                data = dict()
                data["time_delta"] = camera_image.time_delta
                data["cross_track_error"] = observation.cross_track_error
                data["visible"] = observation.visible
                data["left_power"] = instruction.left_power
                data["right_power"] = instruction.right_power

                telemetry_atom = telemetry.TelemetryAtom(time, image, data)

                out = telemetry_atom.dump()

                web_socket.send_binary(out)

        web_socket.close()
        print "Telemetry Producer timing:", profiler
