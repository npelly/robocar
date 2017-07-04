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
        self.close = False
        self.queue = Queue.Queue()

    def __enter__(self):
        if not self.server: return
        threading.Thread(target=self._run).start()

    def __exit__(self, type, value, traceback):
        self.close = True

    def process_async(self, telemetry):
        if not self.server: return
        telemetry_utils.compress_atom(telemetry)  # compress immediately to free image buffer
        self.queue.put(telemetry)

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

        while not self.close or self.queue.qsize() > 0 :
            try:
                telemetry = self.queue.get(timeout=1.0)
            except Queue.Empty:
                continue

            if self.queue.qsize() > 10:
                print "WARNING: telemetry is %d frames behind" % self.queue.qsize()

            with profiler:
                #telemetry_utils.compress_atom(telemetry)

                out = telemetry_utils.dump_atom(telemetry)

                web_socket.send_binary(out)

        web_socket.close()
        print "Telemetry Client Timing:", profiler
