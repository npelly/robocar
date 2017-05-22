import os
import time

def isRaspberryPi():
    """Return True if running on a Raspberry Pi, False otherwise."""
    try:
        return os.uname()[1] == "pi"
    except NameError:
        return False

class HistogramTimer:
    """Track aggregate timing of a repeated event and present as histogram.

    If the timing is absolute (such as frame rate) use repeated calls to event().
    If the timing is relative (profiling a critical section) use repeated calls
    to the context manager (with syntax).

    Do not mix absolute/relative usage.
    """
    def __init__(self, bin_size = 5):
        """Constructor.

        Arguments:
            bin_size (int): histogram bin size, in ms. Default: 5
        """
        self.bin_size = bin_size
        self.histogram = {} # tracked in ms
        self.count = 0
        self.average = 0.0  # tracked in seconds
        self.prev_time = 0.0

    def event(self):
        current_time = time.time()
        if self.prev_time:
            self._update(current_time - self.prev_time)
        self.prev_time = current_time

    def __enter__(self):
        self.prev_time = time.time()

    def __exit__(self, type, value, traceback):
        self._update(time.time() - self.prev_time)

    def _update(self, delta):
        self.average = (self.count * self.average + delta) / (self.count + 1)
        self.count += 1

        bin = int(delta * 1000.0 / self.bin_size)
        self.histogram[bin] += 1


    def summary(self, include_rate = False):
        """Return summary as string."""
        if self.count < 1:
            return "(no events)"
        result = "avg %dms" % round(self.average * 1000.0)
        if include_rate: result += "(rate=%d Hz)" % round(1.0 / self.average)
        for bin, count in self.histogram.iteritems():
            result += "\n[%4dms,%4dms): %d" % (bin * 5, bin * 5 + 5, count)
        return result

class TimedLoop:
    """Helper to schedule a fixed rate timing loop as accurately as possible.

    Does not sleep on the first call to sleep().

    Does not attempt to "catch-up" if a loop iteration is behind schedule.
    """
    _target_time = 0.0

    def __init__(self, target_period):
        """Constructor.
        Arguments:
            period (float): target time (in seconds) between loop iterations
        """
        self.target_period = target_period
        self.target_time = 0.0

    def sleep(self):
        """Sleeps for some time between 0 and the target_period."""
        current_time = time.time()

        if not self.target_time:  # first run
            self.target_time = current_time + self.target_period
            return

        sleep_time = self.target_time - current_time
        if sleep_time < 0.0:
            print "warning: missed timing (%dms slow)" % (-sleep_time * 1000)
            self.target_time = current_time + self.target_period
        else:
            time.sleep(sleep_time)
            self.target_time += self.target_period

if __name__ == "__main__":
    import random

    histogram_timer = HistogramTimer(bin_size = 1)
    timed_loop = TimedLoop(1.0 / 30)
    for _ in xrange(30):
        timed_loop.sleep()
        histogram_timer.event()
    print histogram_timer.summary()

    histogram_timer_1 = HistogramTimer()
    histogram_timer_2 = HistogramTimer()
    timed_loop = TimedLoop(0.05)
    for _ in xrange(30):
        with histogram_timer_1:
            timed_loop.sleep()
        with histogram_timer_2:
            time.sleep(random.random() * 0.06)
    print "Timed Loop Sleep:", histogram_timer_1.summary()
    print "Random Sleep:", histogram_timer_2.summary()
