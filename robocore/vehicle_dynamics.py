import time
import threading
import sys

import actuators
import pid
import util

class DualMotorInstruction:
    def __init__(self, left_power, right_power):
        self.left_power = left_power
        self.right_power = right_power

    def __str__(self):
        return "*** %s %s ***" % (self._power_to_str(self.left_power), self._power_to_str(self.right_power))

    def _power_to_str(self, power):
        if power == 0x100: return "BBB"
        if power == 0x00:  return "   "
        else:              return "%+0.2X" % power

class ThrottleSteeringInstruction:
    def __init__(self, throttle_ticks, steering_ticks):
        self.throttle_ticks = throttle_ticks
        self.steering_ticks = steering_ticks

    def __str__(self):
        return "*** t:%03d s:%03d ***" % (self.throttle_ticks, self.steering_ticks)

"""
Vehicle with differential steering.
"""
class DifferentialSteeringVehicle:
    def __init__(self, config):
        config = config["VehicleDynamics"]
        self.BASE_POWER = config.getint("BASE_POWER")
        PID_AGGRESSION = config.getfloat("PID_AGGRESSION")
        PID_DAMPING = config.getfloat("PID_DAMPING")

        # input:  cross track error [-1.0, +1.0] left <-> right
        # output: left/right power delta [-0xFF, 0xFF]
        self.pid = pid.Pid(PID_AGGRESSION, 0, PID_AGGRESSION * PID_DAMPING)

    def process(self, observation, telemetry):
        if not observation.visible:
            return DualMotorInstruction(0x00, 0x00)

        power_delta, pid_debug = self.pid.update(observation.cross_track_error, observation.time_delta)
        telemetry["pid_debug"] = pid_debug

        left_power = min(self.BASE_POWER, self.BASE_POWER + power_delta)
        right_power = min(self.BASE_POWER, self.BASE_POWER - power_delta)

        # sanity check
        left_power = util.minmax(left_power, -0xFF, 0xFF)
        right_power = util.minmax(right_power, -0xFF, 0xFF)

        return DualMotorInstruction(left_power, right_power)


"""
Vehicle with independant servo steering and ESC motor.
"""
class ServoSteeringVehicle:
    def __init__(self, config):
        config = config["VehicleDynamics"]
        self.DEFAULT_THROTTLE = config.getfloat("DEFAULT_THROTTLE")
        PID_AGGRESSION = config.getfloat("PID_AGGRESSION")
        PID_DAMPING = config.getfloat("PID_DAMPING")
        self.THROTTLE_NEUTRAL_TICKS = config.getint("THROTTLE_NEUTRAL_TICKS")
        self.THROTTLE_DEFAULT_FWD_TICKS = config.getint("THROTTLE_DEFAULT_FWD_TICKS")
        self.STEERING_NEUTRAL_TICKS = config.getint("STEERING_NEUTRAL_TICKS")
        self.STEERING_RANGE_TICKS = config.getint("STEERING_RANGE_TICKS")

        # input cross track error [-1.0, +1.0] left <-> right
        # output direction [-1.0, 1.0]
        self.pid = pid.Pid(PID_AGGRESSION, 0, PID_AGGRESSION * PID_DAMPING)

    def process(self, observation, telemetry):
        if not observation.visible:
            return ThrottleSteeringInstruction(self.THROTTLE_NEUTRAL_TICKS, self.STEERING_NEUTRAL_TICKS)

        steering, pid_debug = self.pid.update(observation.cross_track_error, observation.time_delta)
        telemetry["pid_debug"] = pid_debug

        steering = util.minmax(steering, -1.0, 1.0)
        telemetry["steering"] = steering

        steering_ticks = int(self.STEERING_NEUTRAL_TICKS + steering * self.STEERING_RANGE_TICKS)

        return ThrottleSteeringInstruction(self.THROTTLE_DEFAULT_FWD_TICKS, steering_ticks)
