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

import robocore.telemetry_utils

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, server):
        self.server = server

class SessionListHandler(BaseHandler):
    def get(self):
        self.render("session_list.html", sessions=self.server.sessions)

class SessionListMoreHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        session_id = int(self.get_argument("session_id")) + 1
        while session_id >= len(self.server.sessions):
            yield self.server.wait_for_session()
        for session in self.server.sessions[session_id:]:
            self.render("session_list_item.html", session=session)
"""
class AtomHandler(tornado.web.RequestHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    @tornado.gen.coroutine
    def get(self, session_id=None, atom_id=None):
        session_id = int(session_id)
        atom_id = int(atom_id)
        try:
            session = self.telemetry_server.sessions[session_id]
            if atom_id >= len(session["atoms"]):
                yield self.telemetry_server.wait_for_atom(session_id, atom_id)
            self.render("session_atom.html", session=session, atom_id=atom_id)
        except KeyError:
            raise tornado.web.HTTPError(404, "Bad Session ID")

class NewSessionHandler(tornado.web.RequestHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    @tornado.gen.coroutine
    def get(self):
        session_id = yield self.telemetry_server.wait_for_session()
        session = self.telemetry_server.sessions[session_id]
        self.render("session_list_item.html", session=session)

class LiveSessionHandler(tornado.web.RequestHandler):
    def initialize(self, telemetry_server):
        self.telemetry_server = telemetry_server

    @tornado.gen.coroutine
    def get(self):
        (session_id, atom_id) yield self.telemetry_server.wait_for_atom()
        session = self.telemetry_server.sessions[session_id]
        self.render("session_atom.html", session=session, atom_id=atom_id)

class ImageHandler(tornado.web.RequestHandler):
    def initialize(self, server):
        self.server = server

    def get(self, session_id=None, atom_id=None):
        session_id = int(session_id)
        atom_id = int(atom_id)
        try:
            image = sessions[session_id]["atoms"][atom_id]["image"]
            self.set_header("Content-type", "image/jpeg")
            self.set_header("Content-length", len(image))
            self.write(image)
        except KeyError:
            raise tornado.web.HTTPError(404, "invalid session_id or atom_id")

class SessionHandler(tornado.web.RequestHandler):
    def initialize(self, server):
        self.server = server

    def get(self, session_id=None):
        session_id = int(session_id)
        try:
            session = self.server.sessions[session_id]
            self.render("session.html", session=session)
        except KeyError:
            raise tornado.web.HTTPError(404, "invalid session_id")

class LiveHandler(tornado.web.RequestHandler):
    def initialize(self, server):
        self.server = server

    def get(self):
        if self.server.live_session_id is not None:  #TODO: else
            try:
                session = self.server.sessions[self.server.live_session_id]
                self.render("session.html", session=session)
            except KeyError:
                raise tornado.web.HTTPError(404, "invalid session_id")

class LiveHandler(tornado.web.RequestHandler):
    def initialize(self, server):
        self.server = server

    def get(self, session_id=None, atom_id=None):
        session_id = int(session_id)
        atom_id = int(atom_id)

        for s_id in xrange(max(session_id, 0), len(self.server.sessions)):
            if s_id == session_id:  # send partial update
                start_atom_id = atom_id
            else:                  # send full page
                start_atom_id = -1
                # render HEADER
            for a_id in xrange(start_atom_id, )




        if session_id < len(self.server.sessions):
            # full sessions to update

        # if no session_id then wait/return new session
        # if closed session then wait/return new session
        if session_id in xrange(len(self.server.sessions)) and self.server.sessions[session_id][".live"]:
            # live session
            session = self.server.sessions[session_id]
            if atom_id < len(session["atoms"]):
                # atoms to return immediately
            else:
                # wait for atoms or closure



        if session_id <  or not self.sessions[session_id][".live"]


        # else live session
            # wait/return new atoms or close
"""


class TelemetryHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, server):
        self.server = server
        self.session_id = None

    def open(self):
        pass

    def on_message(self, message):
        if self.session_id is None:
            try:
                print "telemetry session started from %s" % self.request.remote_ip
                session = robocore.telemetry_utils.load_session(message)
                self.session_id = self.server.register_session(session)
            except AssertionError as e:
                print "WARNING: bad start of session:", e
                self.close()
        else:
            print ".",
            sys.stdout.flush()
            try:
                atom = robocore.telemetry_utils.load_atom(message)
                self.server.register_atom(self.session_id, atom)
            except AssertionError as e:
                print "WARNING: bad atom:", e
                self.close()

    def on_close(self):
        if self.session_id is not None:
            print "\nTelemetry session finished"
            self.server.close_session(self.session_id)
            self.session_id = None

def load_telemetry_directory(path):
    sessions = []
    try:
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)
            try:
                if os.path.isfile(filepath) and filepath.endswith(".robo"):
                    with io.open(filepath, 'rb') as file:
                        sessions.append(robocore.telemetry_utils.load_session(file))
            except (OSError, IOError, AssertionError):
                print "WARNING: failed to load telemetry file %s" % filepath
    except (OSError, IOError):
        print "WARNING: failed to access telemetry directory %s" % path

    return sessions

def save_telemetry(path, session):
    try:
        filename = session["name"] + ".robo"
        filepath = os.path.join(path, filename)

        if not os.path.exists(path):
            os.makedirs(path)

        with io.open(filepath, 'wb') as file:
            file.write(robocore.telemetry_utils.dump_session(session))
    except (OSError, IOError):
        print "WARNING: failed to write %s" % filepath

class TelemetryServer:
    def __init__(self, path):
        self.path = path

        sessions = load_telemetry_directory(path)
        self.sessions = sorted(sessions, key=lambda k: k["name"])
        for i, session in enumerate(self.sessions):
            self.sessions[i][".id"] = i

        self.session_futures = set()

    def register_session(self, session):
        id = len(self.sessions)
        session[".id"] = id
        self.sessions.append(session)

        for future in self.session_futures:
            future.set_result([])
        self.session_futures.clear()

        return id

    def register_atom(self, session_id, atom):
        self.sessions[session_id]["atoms"].append(atom)

    def close_session(self, session_id):
        save_telemetry(self.path, self.sessions[session_id])

    def wait_for_session(self):
        future = tornado.concurrent.Future()
        self.session_futures.add(future)
        return future
"""
    def wait_for_atom(self, session_id, atom_id):
        result_future = tornado.concurrent.Future()
        self.waiters.setdefault(session_id, {})
        self.waiters[session_id].setdefault(atom_id, [])
        self.waiters[session_id][atom_id].append(result_future)
        return result_future

    def wait_for_atom(self):  # any atom
        result_future = tornado.concurrent.Future()
        self.waiters.setdefault(0, [])
        self.waiters[0].append(result_future)
        return result_future


    def new_session(self, session):
        session = self._create_dict_session(session, [])
        session_id = session["id"]
        self.sessions[session_id] = session

        while len(self.new_session_waiters) > 0:
            self.new_session_waiters.pop().set_result(session_id)

        return session_id

    def new_atom(self, session_id, atom):
        session = self.sessions[session_id]
        atoms = session["atoms"]
        atom_id = len(atoms)
        atoms.append(atom)

        try:
            futures = self.waiters[session_id].pop(atom_id)
            for future in futures:
                future.set_result([])   #TODO clear futures in cleanup paths
        except KeyError:
            pass

        try:
            futures = self.waiters[0]
            for future in futures:
                future.set_result((session_id, atom_id))   #TODO clear futures in cleanup paths
        except KeyError:
            pass

        return atom_id
"""

if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    port = int(args["--port"])
    path = args["--telemetry"]

    server = TelemetryServer(path)

    app = tornado.web.Application(
        [
            # /                             non-blocking, returns full page. session_id = -1...
            # /more?session_id=[session_id] blocking, returns snippet to append and new session_id
            (r"/",                          SessionListHandler,     dict(server=server)),
            (r"/more",                      SessionListMoreHandler, dict(server=server)),

            # /session/0                        non-blocking, returns full page, atom_id = -1.... more=true/false
            # /session/0/image/0                non-blocking, returns image
#            (r"/session/(?P<session_id>\w+)", SessionHandler,     dict(server=server)),
#            (r"/session/(?P<session_id>\w+)/image/(?P<atom_id>\w+)", ImageHandler, dict(server=server)),

            # /session/live                 non-blocking, return full page of current session if exists
            # /session/live/more?session_id=[session_id]&atom_id=[atom_id]
#            (r"/session/live",       LiveHandler,     dict(server=server)),
#            (r"/session/live/more",  LiveMoreHandler, dict(server=server)),

            # Websocket
            (r"/api/telemetry", TelemetryHandler, dict(server=server)),
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
