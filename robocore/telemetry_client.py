import io
import numpy
import PIL.Image
import Queue
import socket
import threading
import websocket

import vehicle_dynamics
import telemetry_utils
import util

class TelemetryClient:
    def __init__(self, server, config_contents):
        self.server = None
        if server: self.server = "ws://%s/api/telemetry" % server
        self.config_contents = config_contents
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

    def process_async(self, time, image, telemetry):
        if not self.running: return

        self.queue.put((time, image, telemetry))

    def _run(self):
        try:
            web_socket = websocket.create_connection(self.server)
        except socket.error:
            print "WARNING: failed to connect to telemetry server:", self.server
            self.running = False
            return

        session = telemetry_utils.create_session()
        session["config"] = self.config_contents
        web_socket.send_binary(telemetry_utils.dump_session(session))
        self.config_contents = None  # allow GC

        profiler = util.SectionProfiler()

        while self.running:
            time, image, telemetry = self.queue.get()

            if not self.running: break

            if self.queue.qsize() > 10:
                print "WARNING: telemetry is %d frames behind" % self.queue.qsize()

            with profiler:
                # camera_image.image is numpy.ndarray, dtype=uint8
                #TODO fix colors
                pil_image = PIL.Image.fromarray(image)
                image_io = io.BytesIO()
                pil_image.save(image_io, format='jpeg')
                jpeg_image = image_io.getvalue()  # bytearray

                atom = telemetry_utils.create_atom(time, jpeg_image)
                atom.update(telemetry)
                out = telemetry_utils.dump_atom(atom)

                web_socket.send_binary(out)

        web_socket.close()
        print "Telemetry Client Timing:", profiler
