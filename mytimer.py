import time

class MyTimer:
    _stamps = []

    def __init__(self):
        self._stamps = []

    def stamp(self, desc=None):
        self._stamps.append((time.time(), desc))

    def printStamps(self):
        start, _ = self._stamps[0]
        prev = start
        for (stamp, desc) in self._stamps[1:]:
            print "%-16s %4dms (%4dms)" % (desc, (stamp-prev) * 1000, (stamp-start) * 1000)
            prev = stamp

    def clear(self):
        self._stamps= []
