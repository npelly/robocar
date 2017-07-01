"""
A Telemetry Session is a dictionary, with mandatory keys:
"name":         (str) terse name, suitable for filenames etc
"description":  (str) verbose human readable description
"start_time":   (float) start time in seconds since epoch
"atoms":        (list(dict)) zero or more Telemetry Atoms

A Telemetry Atom is also a dictionary, with mandatory keys:
"time"          (float) local time in seconds
"image"         (bytearray/str) JPEG image

Any key beginning with "." is considered hidden and not serialized.
"""

import copy
import cPickle as pickle
import datetime
import io
import socket
import time

def assert_session(session):
    assert isinstance(session, dict), "session not a dict"
    assert isinstance(session["name"], str), "invalid name"
    assert isinstance(session["description"], str), "invalid description"
    assert isinstance(session["start_time"], float), "invalid start_time"
    assert isinstance(session["atoms"], list), "invalid atoms"
    for atom in session["atoms"]:
        assert_atom(atom)

def assert_atom(atom):
    assert isinstance(atom, dict), "atom not a dict"
    assert isinstance(atom["time"], float), "invalid time"
    assert isinstance(atom["image"], str), "invalid image"

def load_session(input):
    """Load from bytearray or IO Stream"""
    if not isinstance(input, io.IOBase):
        input = io.BytesIO(input)  # convert to stream

    session = pickle.load(input)
    assert_session(session)
    return session

def load_atom(input):
    """Load from bytearray or IO Stream"""
    if not isinstance(input, io.IOBase):
        input = io.BytesIO(input)  # convert to stream

    atom = pickle.load(input)
    assert_atom(atom)
    return atom

def dump_session(session):
    """Dump to bytearray"""
    assert_session(session)
    session = strip(session)
    output = io.BytesIO()
    pickle.dump(session, output, protocol=pickle.HIGHEST_PROTOCOL)
    return output.getvalue()

def dump_atom(atom):
    """Dump to bytearray"""
    assert_atom(atom)
    atom = strip(atom)
    output = io.BytesIO()
    pickle.dump(atom, output, protocol=pickle.HIGHEST_PROTOCOL)
    return output.getvalue()

def create_session(name=None, description=None, start_time=None, atoms=[]):
    if not start_time:
        start_time = time.time()
    if not name or not description:
        hostname = socket.gethostname().split('.')[0]
        dt = datetime.datetime.fromtimestamp(start_time)
        if not name:
            name = "%s-%s" % (hostname, dt.strftime("%Y-%m-%d-%H%M%S"))
        if not description:
            description = "%s %s" % (hostname, dt.strftime("%Y-%m-%d %H:%M:%S"))
    session = dict(name=name, description=description, start_time=start_time, atoms=atoms)
    assert_session(session)
    return session

def create_atom(time, image):
    atom = dict(time=time, image=image)
    assert_atom(atom)
    return atom

def strip(items):
    """
    Return a copy of atom or session with hidden key-value pairs stripped,
    or return the original if no stripping required.
    Nested containers (only list, tuple, set & dict) are checked recursively.
    """
    stripped_items = _strip(items)
    return stripped_items if stripped_items else items

def _strip(items):
    """
    Return a copy of items with hidden key-value pairs stripped, or None if
    there are none. Nested containers (only list, tuple, set & dict)
    are checked recursively.
    """
    result = None  # stripped result (if necessary)
    if isinstance(items, list) or isinstance(items, tuple) or isinstance(items, set):
        for i, item in enumerate(items):
            s_item = _strip(item)
            if s_item is not None:
                if result is None: result = copy.copy(items)
                if isinstance(items, list) or isinstance(items, tuple):
                    result[i] = s_item
                elif isinstance(items, set):
                    result.remove(item)
                    result.add(s_item)
    elif isinstance(items, dict):
        for k, item in items.iteritems():
            if isinstance(k, str) and k.startswith("."):
                if result is None: result = copy.copy(items)
                result.pop(k)
            else:
                s_item = _strip(item)
                if s_item is not None:
                    if result is None: result = copy.copy(items)
                    result[k] = s_item
    return result

if __name__ == "__main__":
    atom = create_atom(time.time(), b"123")
    atom[".hidden"] = "value"
    print atom
    print load_atom(dump_atom(atom))

    session = create_session(atoms=[atom])
    session[".hidden"] = "value"
    print session
    print load_session(dump_session(session))
