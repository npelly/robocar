"_id""""Telemetry Server.

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
    def render_without_finish(self, template_name, **kwargs):
        self.write(self.render_string(template_name, **kwargs))

class SessionListHandler(BaseHandler):
    def get(self):
        self.render("session_list.html", sessions=self.server.sessions)

class SessionListMoreHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            session_id = int(self.get_argument("session_id")) + 1
        except (ValueError, TypeError):
            raise tornado.web.HTTPError(400, "invalid session_id parameter")
        while session_id >= len(self.server.sessions):
            yield self.server.wait_for_session()
        for session in self.server.sessions[session_id:]:
            self.render_without_finish("session_list_item.html", session=session)
        self.finish()

class SessionHandler(BaseHandler):
    def get(self, session_id=None):
        try:
            session_id = int(session_id)
            session = self.server.sessions[session_id]
        except (IndexError, ValueError, TypeError):
            raise tornado.web.HTTPError(404, "invalid session_id (%s)" % str(session_id))
        self.render("session.html", session=session)

class ImageHandler(BaseHandler):
    def get(self, session_id=None, atom_id=None):
        try:
            session_id = int(session_id)
            atom_id = int(atom_id)
            image = self.server.sessions[session_id]["atoms"][atom_id]["image"]
        except (IndexError, ValueError, TypeError):
            raise tornado.web.HTTPError(404, "invalid session_id (%s) or atom_id (%s)" % (str(session_id), str(atom_id)))
        self.set_header("Content-type", "image/jpeg")
        self.set_header("Content-length", len(image))
        self.write(image)
        self.finish()

class LiveHandler(BaseHandler):
    def get(self):
        self.render("live.html", sessions=self.server.sessions)

class LiveMoreHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        try:
            session_id = int(self.get_argument("session_id"))
            atom_id = int(self.get_argument("atom_id"))
        except (ValueError, TypeError):
            raise tornado.web.HTTPError(400, "invalid session_id or atom_id parameter")

        if session_id in xrange(len(self.server.sessions)) and self.server.sessions[session_id].get("__live", False):
            # current session is live, look for new atoms
            session = self.server.sessions[session_id]
            atom_id += 1
            if atom_id >= len(session["atoms"]):
                yield self.server.wait_for_atom(session_id)
            for id, atom in list(enumerate(session["atoms"]))[atom_id:]:
                self.render_without_finish("atom.html", session=session, atom_id=id, atom=atom)
        elif session_id in xrange(len(self.server.sessions)):
            # session_id is valid, but session is no longer live
            session = self.server.sessions[session_id]
            # send remaining atoms
            atom_id += 1
            for id, atom in list(enumerate(session["atoms"]))[atom_id:]:
                self.render_without_finish("atom.html", session=session, atom_id=id, atom=atom)
            # tell client to search a new session
            self.write("<script>var session_id = -1; var atom_id = -1;</script>")
        else:  # session_id == -1
            # look for live session
            session_id +=1
            for id, session in list(enumerate(self.server.sessions))[session_id:]:
                if session.get("__live", False):
                    session_id = id
            else:  # no live sessions, wait for one
                session_id = yield self.server.wait_for_session()
            # session_id now live
            session = self.server.sessions[session_id]
            self.render_without_finish("session_header.html", session=session)
            for id, atom in session["atoms"]:
                self.render_without_finish("atom.html", session=session, atom_id=id, atom=atom)
        self.finish()

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
            self.sessions[i]["__id"] = i

        self.session_futures = set()

    def register_session(self, session):
        id = len(self.sessions)
        session["__id"] = id
        session["__live"] = True
        self.sessions.append(session)

        for future in self.session_futures:
            future.set_result(id)
        self.session_futures.clear()

        return id

    def register_atom(self, session_id, atom):
        self.sessions[session_id]["atoms"].append(atom)
        for future in self.sessions[session_id].pop(".futures", set()):
            future.set_result([])

    def close_session(self, session_id):
        self.sessions[session_id].pop("__live")
        for future in self.sessions[session_id].pop(".futures", set()):
            future.set_result([])
        save_telemetry(self.path, self.sessions[session_id])

    def wait_for_session(self):
        future = tornado.concurrent.Future()
        self.session_futures.add(future)
        return future

    def wait_for_atom(self, session_id):
        """
        Wait for another atom on this session, or for the session to end.
        Session must be live.
        """
        future = tornado.concurrent.Future()
        self.sessions[session_id].setdefault(".futures", set())
        self.sessions[session_id][".futures"].add(future)
        return future

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
            (r"/session/(?P<session_id>\w+)", SessionHandler,     dict(server=server)),
            (r"/session/(?P<session_id>\w+)/image/(?P<atom_id>\w+)", ImageHandler, dict(server=server)),

            # /live                 non-blocking, return full page of current session if exists
            # /live/more?session_id=[session_id]&atom_id=[atom_id]
            (r"/live",       LiveHandler,     dict(server=server)),
            (r"/live/more",  LiveMoreHandler, dict(server=server)),

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
