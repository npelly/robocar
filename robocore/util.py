"""Utility class. No internal dependencies."""
import os
import time
import select
import sys


def minmax(value, value_min, value_max):
    return min(max(value, value_min), value_max)

def isRaspberryPi():
    """Return True if running on a Raspberry Pi, False otherwise."""
    try:
        return os.uname()[1] == "pi" or os.uname()[1] == "euler"
    except NameError:
        return False

def isRobocar1():
    try:
        return os.uname()[1] == "pi"
    except NameError:
        return False

def isRobocar2():
    try:
        return os.uname()[1] == "euler"
    except NameError:
        return False

def check_stdin():
    r, _, _ = select.select([sys.stdin], [], [], 0.0)
    return r

class ConstantRateLoop:
    """Helper to keep a loop running at a constant rate.

    Use sleep() to sleep until the next iteration is scheduled.

    When used in a loop, the loop will run at a fixed rate (on average), even
    when the rest of the loop has variable timing.
    """
    def __init__(self, rate):
        """
        Arguments:
          rate (float): The rate (in Hz) to target.
        """
        self.period = 1.0 / rate
        self.next_time = 0.0

    def sleep(self):
        """Sleep as necessary to maintain target rate.

        If the loop timing has already been missed then return immediately.

        The first call start loop timing and returns immediately.
        """
        current_time = time.time()

        if not self.next_time:  # first call
            self.next_time = current_time + self.period
            return

        delta = self.next_time - current_time
        if delta > 0:
            time.sleep(delta)
        self.next_time += self.period

class BaseProfiler:
    def __init__(self, bin_size, include_rate):
        self.bin_size = bin_size
        self.histogram = {} # tracked in ms
        self.count = 0      # count of total time deltas recorded
        self.cumulative_time = 0.0
        self.include_rate = include_rate

    def _record_delta(self, delta):
        self.count += 1
        self.cumulative_time += delta
        bin = int(delta * 1000.0 / self.bin_size)
        try:
            self.histogram[bin] += 1
        except KeyError:
            self.histogram[bin] = 1

    def __str__(self):
        if self.count < 1:
            return "No profile times recorded"
        average = self.cumulative_time / self.count
        result = "count=%d avg=%.1fms" % (self.count, average * 1000.0)
        if self.include_rate: result += " (rate=%.1f Hz)" % (1.0 / average)
        for bin, count in sorted(self.histogram.iteritems()):
            result += "\n[%4dms,%4dms): %d" % \
                    (bin * self.bin_size, (bin+1) * self.bin_size, count)
        return result


class SectionProfiler(BaseProfiler):
    """A Context Manager to track and profile a repeated section of code.

    Use built-in __str__() to generate summary string.
    """
    def __init__(self, bin_size=5):
        """
        Arguments:
            bin_size (int): histogram bin size, in ms. Default: 5
        """
        BaseProfiler.__init__(self, bin_size, include_rate=False)

    def __enter__(self):
        self.enter_time = time.time()

    def __exit__(self, type, value, traceback):
        self._record_delta(time.time() - self.enter_time)

    def __str__(self):
        return BaseProfiler.__str__(self)

class LoopProfiler(BaseProfiler):
    """Track and profile the timing between calls to time().

    Use built-in __str__() to generate summary string.
    """
    def __init__(self, bin_size=5):
        """
        Arguments:
            bin_size (int): histogram bin size, in ms. Default: 5
        """
        BaseProfiler.__init__(self, bin_size, include_rate=True)
        self.prev_time = 0.0
        self.first_time = 0.0

    def time(self):
        """Track timing between calls to this function.

        First call starts the timing (but does not record a time delta).

        Returns a tuple (delta_time, cumulative_time), where delta_time is time
        since the previous call and cumulative_time is time since the first
        call. Both are 0.0 on the first call.
        """
        current = time.time()

        if not self.first_time:  # first call
            self.first_time = current
            self.prev_time = current
            return 0.0, 0.0

        delta = current - self.prev_time
        cumulative = current - self.first_time
        self.prev_time = current

        self._record_delta(delta)

        return delta, cumulative

    def __str__(self):
        """Create summary text as string."""
        return BaseProfiler.__str__(self)

if __name__ == "__main__":
    import random

    print "ENTER skips current test"

    loop_profiler = LoopProfiler(bin_size=1)
    loop = ConstantRateLoop(30.0)
    for _ in xrange(100):
        loop.sleep()
        loop_profiler.time()
        if check_stdin(): break
    print loop_profiler

    section_1 = SectionProfiler()
    section_2 = SectionProfiler()
    loop_profiler = LoopProfiler()
    loop = ConstantRateLoop(20.0)
    for _ in xrange(100):
        loop_profiler.time()
        with section_1:
            loop.sleep()
        if check_stdin(): break
        with section_2:
            time.sleep(random.random() * 0.06)
        if check_stdin(): break
    print "Scheduled Sleep:", section_1
    print "Random Sleep:", section_2
    print "Total Loop Profile:", loop_profiler
