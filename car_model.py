import time
import threading
import sys
import select

import timer
import motor
import perception

DEBUG = False

_MIN_2WD_START_PWM = 0xA1#0x80   # 2WD, found emperically
_MIN_2WD_MOVE_PWM  = 0xA2#0x70   # 2WD, found emperically
_MIN_LWD_START_PWM = 0xA3#0xA8
_MIN_LWD_MOVE_PWM  = 0xA4#0x90
_MIN_LWD_CASTER_FIX_START_PWM = 0xC5
_MIN_LWD_CASTER_FIX_MOVE_PWM = 0xA6
_LWD_CASTER_FIX_TIME = 0.15

class PID:
    def __init__(self, C, P, I, D):
        self.Kc = float(C)
        self.Kp = float(P)
        self.Ki = float(I)
        self.Kd = float(D)
        self.derivator = 0.0
        self.integrator = 0.0

    def update(self, error):
        P_value = self.Kp * error
        D_value = self.Kd * (error - self.derivator)
        self.derivator = error
#        self.integrator = max(min(self.integrator + error, self.integrator_max), self.integrator_min)
        I_value = self.integrator * self.Ki

        return P_value + D_value + I_value + self.Kc

"""
Jaycar chassis, stem caster, 7.2 volts
"""
class RoboCar72v:

    def __init__(self):
        self.left_pid = PID(0.2, 0.5, 0, 0)
        self.right_pid = PID(0.2, -0.5, 0, 0)

    def process(self, observation):
        (cross_track_error, visible) = observation

        if not visible:
            return 0x00, 0x00

        left_power = self.left_pid.update(cross_track_error)
        right_power = self.right_pid.update(cross_track_error)

        if (left_power > 0):
            left_power = 0x80 + 0x80 * left_power
        else:
            left_power = -0x80 + 0x80 * left_power
        if (right_power > 0):
            right_power = 0x80 + 0x80 * right_power
        else:
            right_power = -0x80 + 0x80 * right_power

        left_power = min(max(left_power, -0xFF), 0xFF)
        right_power = min(max(right_power, -0xFF), 0xFF)

        return left_power, right_power

def get_car_model():
    return RoboCar72v()

def main(args):
    car = get_car_model()

    CROSS_TRACK_ERRORS = [0, -0.1, -0.1, -0.1, 0, 0, -1, -1, -1]
    for error in CROSS_TRACK_ERRORS:
        observation = (error, True)
        instruction = car.process(observation)
        print perception.describe(observation), motor.describe(instruction)

if __name__ == "__main__":
    #test()
    #calibrate()
    #verify()
    #testMinimumSpeed()
    main(None)
