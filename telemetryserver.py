"""Telemetry Server.

Robocars push telemetry data to this server, and users can view that data.

Usage:
  telemetryserver.py [--port=<PORT>] [--telemetry=<PATH>]

Options:
  -h --help         Print this help text
  --port PORT       Server port [DEFAULT: 7007]
  --telemetry PATH  Path to archive telemetry data [DEFAULT: .telemetry]
"""

import cPickle as pickle
import datetime
import docopt
import functools
import io
import os
import socket
import sys
import time
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.websocket

import robocore.telemetry

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    def get(self):
        self.render("session_list.html", sessions=self.telemetry_server.sessions)

class ImageHandler(tornado.web.RequestHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    def get(self, session_id=None, image_id=None):
        for session in self.telemetry_server.sessions:
            if session["id"] == int(session_id):
                image = session["atoms"][int(image_id)].image
                self.set_header("Content-type", "image/png")
                self.set_header("Content-length", len(image))
                self.write(image)
                return
        raise tornado.web.HTTPError(404, "Bad Session ID")

class SessionHandler(tornado.web.RequestHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    def get(self, session_id=None):
        for session in self.telemetry_server.sessions:
            if session["id"] == int(session_id):
                self.render("session.html", session=session)
                return
        raise tornado.web.HTTPError(404, "Bad Session ID")

class TelemetryHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    def open(self):
        start_time = time.time()
        print "Telemetry session started", start_time
        self.session = robocore.telemetry.TelemetrySession(start_time, {})
        self.id = session_to_id(self.session)
        self.atoms = []

    def on_message(self, message):
        atom = robocore.telemetry.load_atom(message)
        print ".",
        sys.stdout.flush()
        self.atoms.append(atom)

    def on_close(self):
        print "\nTelemetry session finished"
        if len(self.atoms) > 0:
            self.telemetry_server.save(self.session, self.atoms)

def session_to_id(telemetry_session):
    return int(telemetry_session.start_time)  # crappy hash

class TelemetryServer:
    def __init__(self, path):
        self.path = path
        self.sessions = self._load(path)   # list of dict()s

    def _load(self, path):
        sessions = []

        try:
            for file in os.listdir(path):
                filepath = os.path.join(path, file)
                if os.path.isfile(filepath) and filepath.endswith(".robo"):

                    sessions.append(self._loadFile(filepath))
        except (OSError, IOError):
            pass

        print "Loaded %d sessions from %s" % (len(sessions), os.path.abspath(path))
        return sessions

    def _loadFile(self, filepath):
        with io.open(filepath, 'rb') as file:
            session = robocore.telemetry.load_session(file)
            atoms = []
            try:
                while True:
                    atoms.append(robocore.telemetry.load_atom(file))
            except EOFError:
                pass
            print "Loaded telemetry %s (%d atoms)" % (filepath, len(atoms))
            return self._create_dict_session(session, atoms)

    def _create_dict_session(self, session, atoms):
        id = session_to_id(session)
        return {"id": id, "session": session, "atoms": atoms,
            "time_str": time_to_str(session.start_time)}

    def save(self, session, atoms):
        try:
            filename = time_to_str(session.start_time) + ".robo"
            filepath = os.path.join(self.path, filename)

            if not os.path.exists(self.path):
                os.makedirs(self.path)

            with io.open(filepath, 'wb') as file:
                file.write(session.dump())
                for atom in atoms:
                    file.write(atom.dump())

            print "Saved telemetry session to %s (%d atoms)" % (filepath, len(atoms))

        except (OSError, IOError):
            print "WARNING: failed to write %s" % filepath

        self.sessions.append(self._create_dict_session(session, atoms))

def time_to_str(time):
    return datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%d-%H%M%S")

if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    port = int(args["--port"])
    path = args["--telemetry"]

    telemetry_server = TelemetryServer(path)

    app = tornado.web.Application(
        [
            (r"/",              MainHandler, dict(telemetry_server=telemetry_server)),
            (r"/api/session/(?P<session_id>\w+)", SessionHandler, dict(telemetry_server=telemetry_server)),
            (r"/api/session/(?P<session_id>\w+)/(?P<image_id>\w+)", ImageHandler, dict(telemetry_server=telemetry_server)),
            (r"/api/telemetry", TelemetryHandler, dict(telemetry_server=telemetry_server)),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "robocore", "web"),
        static_path=os.path.join(os.path.dirname(__file__), "robocore", "web"),
        )
    app.listen(port)
    print "Listening at %s:%d" % (socket.gethostname(), port)

    def on_keyboard(io_loop, fd, events):
        io_loop.stop()
    io_loop = tornado.ioloop.IOLoop.current()
    callback = functools.partial(on_keyboard, io_loop)
    io_loop.add_handler(sys.stdin, callback, io_loop.READ)
    io_loop.start()
