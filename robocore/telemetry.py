import cPickle as pickle
import io

def load_atom(input):
    """Load from bytearray or IO Stream"""
    if not isinstance(input, io.IOBase):
        input = io.BytesIO(input)

    time = pickle.load(input)
    image = pickle.load(input)
    data = pickle.load(input)
    return TelemetryAtom(time, image, data)

class TelemetryAtom:
    def __init__(self, time, image, data):
        assert isinstance(time, float)
        assert isinstance(image, str)
        assert isinstance(data, dict)

        self.time = time    # (float) local timestamp in seconds
        self.image = image  # (bytes) PNG image
        self.data = data    # (dict) key-value telemetry

    def dump(self):
        """Dump to bytearray"""
        output = io.BytesIO()
        pickle.dump(self.time, output, protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.image, output, protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.data, output, protocol=pickle.HIGHEST_PROTOCOL)
        return output.getvalue()

def load_session(input):
    """Load from bytearray or IO Stream"""
    if not isinstance(input, io.IOBase):
        input = io.BytesIO(input)

    start_time = pickle.load(input)
    data = pickle.load(input)
    return TelemetrySession(start_time, data)

class TelemetrySession:
    def __init__(self, start_time, data):
        assert isinstance(start_time, float)
        assert isinstance(data, dict)

        self.start_time = start_time  # (float) local timestamp in seconds
        self.data = data              # (dict) key-value session data

    def dump(self):
        """Dump to bytearray"""
        output = io.BytesIO()
        pickle.dump(self.start_time, output, protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump(self.data, output, protocol=pickle.HIGHEST_PROTOCOL)
        return output.getvalue()
