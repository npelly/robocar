import os
import threading
import time
import select
import docopt
import util

"""
Implement dual motor drive using a custom serial protocol
to an Arduino, that does the PWM to a motor shield.
Using an Arduino is total overkill, should have used an
Adafruit PCA9685, or even better something with both PWM
and H-Bridge Motor driver.
"""
class DualMotorArduinoController:
    ARUDINO_PORT_BASE = "/dev/ttyACM"
    ARDUINO_BAUDRATE = 9600
    ENABLE_READ_THREAD = False
    DEBUG = False

    def __init__(self, config):
        global serial
        import serial

    def __enter__(self):
        for i in xrange(10):
            port = self.ARUDINO_PORT_BASE + str(i)
            try:
                self.serial = serial.Serial(port, self.ARDUINO_BAUDRATE, timeout=1.0)
                if self.ENABLE_READ_THREAD: threading.Thread(target=self._read).start()
                print "Opened", port
                return
            except serial.SerialException:
                self.serial = None
                continue
        print "WARNING: Could not open any %sx, no actuation" % self.ARUDINO_PORT_BASE

    def __exit__(self, type, value, traceback):
        if not self.serial: return
        self._send("F00F00\n")
        serial = self.serial
        self.serial = None
        serial.close()
        print "closed serial port"

    """
    Set left motor power and right motor power.
    Both are integers in range [-255, 255], or 256 to brake.
    """
    def process(self, instruction, telemetry):
        command = "%s%s\n" % (self._power_to_command(instruction.left_power), self._power_to_command(instruction.right_power))
        self._send(command)

    def _power_to_command(self, power):
        if power == 0x100: return "B00"
        if power >= 0x00:  return "F%02X" % power
        else:              return "R%02X" % (-power)

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

class Pca9685ServoController:
    def __init__(self, config):
        try:
            global Adafruit_PCA9685
            import Adafruit_PCA9685
        except ImportError:
            print "WARNING: PCA9685 driver not available, no actuation"
            self.pwm = None
            return

        config = config["VehicleDynamics"]
        self.FREQUENCY_HZ = config.getfloat("FREQUENCY_HZ")
        self.THROTTLE_CHANNEL = config.getint("THROTTLE_CHANNEL")
        self.THROTTLE_NEUTRAL_TICKS = config.getint("THROTTLE_NEUTRAL_TICKS")
        self.STEERING_CHANNEL = config.getint("STEERING_CHANNEL")
        self.STEERING_NEUTRAL_TICKS = config.getint("STEERING_NEUTRAL_TICKS")

        self.pwm = Adafruit_PCA9685.PCA9685()

    def __enter__(self):
        if not self.pwm: return
        self.pwm.set_pwm_freq(self.FREQUENCY_HZ)
        self.pwm.set_pwm(self.THROTTLE_CHANNEL, 0, self.THROTTLE_NEUTRAL_TICKS)
        self.pwm.set_pwm(self.STEERING_CHANNEL, 0, self.STEERING_NEUTRAL_TICKS)

    def __exit__(self, type, value, traceback):
        if not self.pwm: return
        self.pwm.set_pwm(self.THROTTLE_CHANNEL, 0, self.THROTTLE_NEUTRAL_TICKS)
        self.pwm.set_pwm(self.STEERING_CHANNEL, 0, self.STEERING_NEUTRAL_TICKS)

    def process(self, instruction, telemetry):
        if not self.pwm: return
        self.pwm.set_pwm(self.THROTTLE_CHANNEL, 0, instruction.throttle_ticks)
        self.pwm.set_pwm(self.STEERING_CHANNEL, 0, instruction.steering_ticks)
