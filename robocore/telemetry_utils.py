"""
A Telemetry Session is a dictionary, with mandatory keys:
"filename":    (str) terse filename
"_summary":     (str) human readable summary
"_start_time":  (float) start time in seconds since epoch
"_atoms":       (list(dict)) zero or more Telemetry Atoms

A Telemetry Atom is also a dictionary, with mandatory keys:
"image"         (images.*) original camera image, needed for camera replay

Any key beginning with "_" is special purpose
Any key beginning with "__" is private (not serialized nor displayed)
All other keys are considered serializable & general purpose telemetry
"""

import collections
import copy
import cPickle as pickle
import datetime
import io
import socket
import time

import images

def assert_session(session):
    assert isinstance(session, collections.OrderedDict), "session not a dict"
    assert isinstance(session["filename"], str), "invalid filename"
    assert isinstance(session["_summary"], str), "invalid summary"
    assert isinstance(session["_start_time"], float), "invalid start_time"
    assert isinstance(session["_atoms"], list), "invalid atoms"
    for atom in session["_atoms"]:
        assert_atom(atom)

def assert_atom(atom):
    assert isinstance(atom, collections.OrderedDict), "atom not a dict"
    assert isinstance(atom["image"], images.JpegImage) or isinstance(atom["image"], images.NumpyImage), "invalid camera image"

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

def create_session(filename=None, summary=None, start_time=None, atoms=[]):
    if not start_time:
        start_time = time.time()
    if not filename or not summary:
        hostname = socket.gethostname().split('.')[0]
        dt = datetime.datetime.fromtimestamp(start_time)
        if not filename:
            filename = "%s-%s.telemetry" % (hostname, dt.strftime("%Y-%m-%d-%H%M%S"))
        if not summary:
            summary = "%s %s" % (hostname, dt.strftime("%Y-%m-%d %H:%M:%S"))
    session = collections.OrderedDict(filename=filename, _summary=summary, _start_time=start_time, _atoms=atoms)
    assert_session(session)
    return session

def create_atom(image):
    atom = collections.OrderedDict(image=image)
    assert_atom(atom)
    return atom

def strip(items):
    """
    Return a copy of atom or session with private key-value pairs stripped,
    or return the original if no stripping required.
    Nested containers (only list, tuple, set & dict) are checked recursively.
    """
    stripped_items = _strip(items)
    return stripped_items if stripped_items else items

def _strip(items):
    """
    Return a copy of items with private key-value pairs stripped, or None if
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
            if isinstance(k, str) and k.startswith("__"):
                if result is None: result = copy.copy(items)
                result.pop(k)
            else:
                s_item = _strip(item)
                if s_item is not None:
                    if result is None: result = copy.copy(items)
                    result[k] = s_item
    return result

"""
Cpmpress numpy array images to jpeg images
"""
def compress_atom(atom):
    for key, numpy_image in atom.iteritems():
        if isinstance(numpy_image, images.NumpyImage):
            atom[key] = numpy_image.to_jpeg_image()

if __name__ == "__main__":
    image = images.JpegImage(b"123", time.time(), 0.0)

    atom = create_atom(image)
    atom["__hidden"] = "value"
    print atom
    print load_atom(dump_atom(atom))

    session = create_session(atoms=[atom])
    session["__hidden"] = "value"
    print session
    print load_session(dump_session(session))
