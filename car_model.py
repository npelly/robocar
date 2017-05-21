import time
import threading
import sys
import select

import timer
import motor
import perceptor

D = True

class Pid:
    def __init__(self, k_p, k_i, k_d):
        self.k_p = float(k_p)
        self.k_i = float(k_i)
        self.k_d = float(k_d)
        self.prev_error = 0.0
        self.prev_timestamp = 0.0
        self.sum_error_time = 0.0
        self.first_run = True

    def update(self, error, timestamp):
        if self.first_run:
            self.first_run = False
            self.prev_error = error
            self.prev_timestamp = timestamp
            return None

        t = timestamp - self.prev_timestamp
        self.prev_timestamp = timestamp
        p = self.k_p * error
        self.sum_error_time += error * t
        i = self.k_i * self.sum_error_time
        d = self.k_d * (error - self.prev_error) / t
        self.prev_error = error

        pid = p + i + d

        if D: print "P=%.3f I=%.3f D=%.3f t=%.3f PID=%.3f" % (p, i, d, t, pid)

        return pid

def minmax(value, value_min, value_max):
    return min(max(value, value_min), value_max)

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

"""
Jaycar chassis, stem caster, 7.2 volts
"""
class RoboCar72v:
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
        timestamp = observation.timestamp

        if not observation.visible:
            return Instruction(0x00, 0x00)

        power_delta = self.pid.update(cross_track_error, timestamp)

        if power_delta is None:
            return Instruction(0x00, 0x00)

        left_power = min(self.base_power, self.base_power + power_delta)
        right_power = min(self.base_power, self.base_power - power_delta)

        # sanity check
        left_power = minmax(left_power, -0xFF, 0xFF)
        right_power = minmax(right_power, -0xFF, 0xFF)

        return Instruction(left_power, right_power)

def get_car_model():
    return RoboCar72v()

def main(args):
    car = get_car_model()

    CROSS_TRACK_ERRORS = [0, -0.1, -0.1, -0.1, 0, 0, -1, -1, -1]
    timestamp = 0.0
    for error in CROSS_TRACK_ERRORS:
        observation = perceptor.Observation(error, True, timestamp)
        instruction = car.process(observation)
        print observation, instruction
        timestamp += 0.2

if __name__ == "__main__":
    #test()
    #calibrate()
    #verify()
    #testMinimumSpeed()
    main(None)
