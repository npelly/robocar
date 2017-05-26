import time
import threading
import sys

import util

DEBUG = False

class Pid:
    def __init__(self, k_p, k_i, k_d):
        self.k_p = float(k_p)
        self.k_i = float(k_i)
        self.k_d = float(k_d)
        self.prev_error = 0.0
        self.sum_error_time = 0.0

    def update(self, error, time_delta):
        p = self.k_p * error
        self.sum_error_time += error * time_delta
        i = self.k_i * self.sum_error_time
        if time_delta > 0.0:
            d = self.k_d * (error - self.prev_error) / time_delta
        else:   # first loop
            d = 0.0
        self.prev_error = error

        pid = p + i + d

        if DEBUG: print "P=%.3f I=%.3f D=%.3f t=%.3f PID=%.3f" % (p, i, d, error_time_delta, pid)

        return pid

class Instruction:
    def __init__(self, left_power, right_power):
        self.left_power = left_power
        self.right_power = right_power
    def __str__(self):
        s = "*** "
        for power in (self.left_power, self.right_power):
            if power == 0x00: s += "    "
            elif power == 0x100: s += " ** "
            else:
                flag = ' ' if power > 0 else '-'
                s += "%c%02X%c" % (flag, abs(power), flag)
        s += " ***"
        return s


class RoboCar72v:
    """
    Jaycar 2WD chassis, stem caster, 7.2 volts
    """
    def __init__(self):
        self.base_power = 0xFF

        pid_aggression = 0xAF
        damping = 0.5
        # input cross track error [-1.0, +1.0] left <-> right
        # output power delta [-0xFF, 0xFF]
        self.pid = Pid(pid_aggression, 0, pid_aggression * damping)

        self.first_observation = True

    def process(self, observation):
        cross_track_error = observation.cross_track_error

        if not observation.visible:
            return Instruction(0x00, 0x00)

        power_delta = self.pid.update(cross_track_error, observation.time_delta)

        left_power = min(self.base_power, self.base_power + power_delta)
        right_power = min(self.base_power, self.base_power - power_delta)

        # sanity check
        left_power = util.minmax(left_power, -0xFF, 0xFF)
        right_power = util.minmax(right_power, -0xFF, 0xFF)

        return Instruction(left_power, right_power)
