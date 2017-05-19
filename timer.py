import time
import numpy

class Timer:
    _stamps = []

    def __init__(self):
        self._stamps = []
        self.stamp()

    def stamp(self, desc=None):
        self._stamps.append((time.time(), desc))

    def print_stamps(self):
        if len(self._stamps) < 2: return
        start, _ = self._stamps[0]
        prev = start
        for (stamp, desc) in self._stamps[1:]:
            delta = stamp - prev
            delta_cum = stamp - start
            print "%-16s %4dms (%4dms)" % (desc, delta * 1000, delta_cum * 1000)
            prev = stamp

    def print_summary(self):
        if len(self._stamps) < 2: return
        prev, _ = self._stamps[0]
        deltas = []
        max = 0
        for (stamp, _) in self._stamps[1:]:
            delta = int(round((stamp - prev) * 1000))
            deltas.append(delta)
            if delta > max: max = delta
            prev = stamp
        avg = numpy.average(deltas)
        mean = numpy.mean(deltas)
        print "avg %dms (%dHZ) mean %dms (%dHZ)" % \
                (avg, int(round(1000.0/avg)), mean, int(round(1000.0/mean)))
        (counts, bins) = numpy.histogram(deltas, xrange(0, max + 5, 5))
        for (count, bin) in zip(counts, bins):
            if count == 0: continue
            print "[%4dms,%4dms): %d" % (bin, bin+5, count)

    def clear(self):
        self._stamps= []

class HistogramTimer:
    def __init__(self):
        self.histogram = {}
        self.count = 0
        self.average = 0.0

    def enter(self):
        self.enter_time = time.time()

    def exit(self):
        delta = round(1000*(time.time() - self.enter_time))
        self.average = (self.count * self.average + delta) / (self.count + 1)
        self.count += 1

        bin = int(delta / 5)
        old = self.histogram.get(bin)
        if old:
            self.histogram[bin] = old + 1
        else:
            self.histogram[bin] = 1

    def print_summary(self):
        if self.count < 1:
            print ""
            return
        if self.average == 0: self.average = 0.0000000001
        print "avg %dms" % (self.average)
        for bin, count in self.histogram.iteritems():
            print "[%4dms,%4dms): %d" % (bin*5, bin*5+5, count)

"""
Keep to a regular timing period.
Resets the timing period if missed
"""
class TimedLoop:
    _target_time = 0.0

    def __init__(self, hertz):
        self._target_period = 1.0 / hertz

    def wait(self):
        if self._target_time == 0.0:  # first run
            self._target_time = time.time() + self._target_period
        current_time = time.time()
        if current_time > self._target_time:
            print "warning: missed timing (%dms slow)" % ((current_time - self._target_time) * 1000)
            self._target_time = current_time + self._target_period
        else:
            time.sleep(self._target_time - current_time)
        self._target_time += self._target_period

if __name__ == "__main__":
    timer = Timer()
    timed_loop = TimedLoop(10)
    for i in range(10):
        timed_loop.wait()
        timer.stamp(i)
    timer.print_stamps()
    timer.print_summary()

    timer = HistogramTimer()
    timed_loop = TimedLoop(10)
    histogram_timer = HistogramTimer()
    for i in range(10):
        histogram_timer.enter()
        timed_loop.wait()
        histogram_timer.exit()
    histogram_timer.print_summary()
