import os
import serial
import threading
import time
import select
import docopt
import util

DEBUG = False

class DummyMotor:
    def process(self, instructions):
        pass
    def __enter__(self):
        pass
    def __exit__(self, type, value, traceback):
        pass

class ArduinoSerialMotor:
    ARUDINO_PORT = "/dev/ttyACM"
    ARDUINO_BAUDRATE = 9600
    ENABLE_READ_THREAD = False

    def __enter__(self):
        for i in xrange(10):
            port = self.ARUDINO_PORT + str(i)
            try:
                self.serial = serial.Serial(port, self.ARDUINO_BAUDRATE, timeout=1.0)
                if self.ENABLE_READ_THREAD: threading.Thread(target=self._read).start()
                print "Opened", port
                return
            except serial.SerialException:
                continue
        print "ERROR: Could not open any", self.ARUDINO_PORT + "x"

    def __exit__(self, type, value, traceback):
        if not self.serial: return
        self._send("F00F00\n")
        serial = self.serial
        self.serial = None
        serial.close()
        print "closed serial port"

    """left and right in range [-255, 255]"""
    def process(self, instructions):
        command = ""
        for power in (instructions.left_power, instructions.right_power):
            if power == 0x100:
                command += "B00"
                continue
            elif power >= 0x00:
                command += 'F'
            else:
                command += 'R'
            command += "%02X" % (abs(power))
        self._send(command + "\n")

    def _send(self, command):
        if not self.serial: return
        self.serial.write(command)
        if DEBUG: print ">", command,

    def _read(self):
        try:
            while self.serial:
                input = self.serial.readline()
                if input and DEBUG: print "<", input,
        except (OSError, select.error, TypeError):
            pass


FREQUENCY_HZ_REQUEST = 90.0
FREQUENCY_HZ = 94.35  # actual frequency (measured by multimeter)

THROTTLE_CHANNEL = 1
THROTTLE_NEUTRAL_TICK = 600
THROTTLE_DEFAULT_FWD_TICK = 631

STEERING_CHANNEL = 2
STEERING_NEUTRAL_TICK = 560
STEERING_RANGE_TICK = 90
class ServoMotor:
    def __init__(self):
        import Adafruit_PCA9685
        self.pwm = Adafruit_PCA9685.PCA9685()

    def __enter__(self):
        self.pwm.set_pwm_freq(FREQUENCY_HZ_REQUEST)
        self.pwm.set_pwm(THROTTLE_CHANNEL, 0, THROTTLE_NEUTRAL_TICK)
        self.pwm.set_pwm(STEERING_CHANNEL, 0, STEERING_NEUTRAL_TICK)

    def __exit__(self, type, value, traceback):
        self.pwm.set_pwm(THROTTLE_CHANNEL, 0, THROTTLE_NEUTRAL_TICK)
        self.pwm.set_pwm(STEERING_CHANNEL, 0, STEERING_NEUTRAL_TICK)

    def process(self, instructions):
        throttle_tick = THROTTLE_NEUTRAL_TICK
        if instructions.throttle > 0.0:
            throttle_tick = THROTTLE_DEFAULT_FWD_TICK

        steering_tick = int(STEERING_NEUTRAL_TICK + instructions.steering * STEERING_RANGE_TICK)

        # sanity check
        throttle_tick = util.minmax(throttle_tick, THROTTLE_NEUTRAL_TICK, THROTTLE_DEFAULT_FWD_TICK)
        steering_tick = util.minmax(steering_tick, STEERING_NEUTRAL_TICK - STEERING_RANGE_TICK, STEERING_NEUTRAL_TICK + STEERING_RANGE_TICK)

        self.pwm.set_pwm(THROTTLE_CHANNEL, 0, throttle_tick)
        self.pwm.set_pwm(STEERING_CHANNEL, 0, steering_tick)
