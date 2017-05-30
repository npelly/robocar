import sys
import threading
import socket
import Queue
import os

import cv2
import base64

import tornado.ioloop
import tornado.web
import tornado.gen


PORT = 8888


class CameraImageFuture:
    def __init__(self):
        self.waiters = set()

    def wait_for_fresh_image(self):
        # Construct a Future to return to our caller.  This allows
        # wait_for_fresh_image to be yielded from a coroutine even though
        # it is not a coroutine itself.  We will set the result of the
        # Future when results are available.
        result_future = tornado.concurrent.Future()
        self.waiters.add(result_future)
        return result_future

    def cancel_wait(self, future):
        self.waiters.remove(future)
        # Set an empty result to unblock any coroutines waiting.
        future.set_result([])

    def new_image(self, camera_image):
        (result, data) = cv2.imencode(".png", camera_image.image)
        b64 = base64.encodestring(data)

        for future in self.waiters:
            future.set_result(b64)
        self.waiters = set()

camera_image_future = CameraImageFuture()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class ImageHandler(tornado.web.RequestHandler):
##    def initialize(self, queue):
#       self.queue = queue
    @tornado.gen.coroutine
    def get(self):
        print "waiting..."
        b64 = yield camera_image_future.wait_for_fresh_image()
        print "got it"
        self.write(b64)

    def on_connection_close(self):
        pass

class TelemetryServer:
    def __init__(self):
        pass

    def __enter__(self):
    #    self.camera_image_queue = Queue.Queue(maxsize=1)

        app = tornado.web.Application(
            [
                (r"/", MainHandler),
                (r"/image", ImageHandler),
            ],
            template_path=os.path.join(os.path.dirname(__file__), "web"),
            static_path=os.path.join(os.path.dirname(__file__), "web"),
            )
        app.listen(PORT)
        print "server running at %s:%d" % (socket.gethostname(), PORT)
        threading.Thread(target=self.loop).start()

    def loop(self):
        ioloop = tornado.ioloop.IOLoop.current()
        ioloop.start()

    def __exit__(self, type, value, traceback):
        tornado.ioloop.IOLoop.current().stop()

    def send(self, camera_image, observations, instructions):
        camera_image_future.new_image(camera_image)


if __name__ == "__main__":
    with TelemetryServer():
        sys.stdin.readline()
