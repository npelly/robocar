"""
Motor driver control.
Implemented via serial protocol to arudino.
"""

import os
import serial
import threading
import time
import select
import argparse

import timer

DEBUG = False

class DummyMotor:
    def process(self, instructions):
        pass

    def close(self):
        pass

class ArduinoMotor:
    _ARUDINO_PORT = "/dev/ttyACM"
    _ARDUINO_BAUDRATE = 9600

    _dummy = DummyMotor()

    def __init__(self):
        for i in xrange(10):
            port = self._ARUDINO_PORT + str(i)
            try:
                self._serial = serial.Serial(port, self._ARDUINO_BAUDRATE, timeout=1.0)
                threading.Thread(target=self._read).start()
                print "opened", port
                return
            except serial.SerialException:
                continue
        print "ERROR: Could not open any", self._ARUDINO_PORT + "x"

    """left and right in range [-255, 255]"""
    def process(self, instructions):
        command = ""
        for a in instructions:
            if a == 0x100:
                command += "B00"
                continue
            elif a >= 0x00:
                command += 'F'
            else:
                command += 'R'
            command += "%02X" % (abs(a))
        self._send(command + "\n")
        self._dummy.drive(instructions)

    def close(self):
        if self._serial is None: return
        self.drive(0, 0)
        serial = self._serial
        self._serial = None
        serial.close()
        print "closed serial port"

    def _send(self, command):
        if self._serial is None: return

        self._serial.write(command)
        if DEBUG: print ">", command,

    def _read(self):
        try:
            while self._serial is not None:
                input = self._serial.readline()
                if input and DEBUG: print "<", input,
        except (OSError, select.error, TypeError):
            pass

def describe(instructions):
    s = "*** "
    for a in instructions:
        if a == 0:
            s += "    "
            continue
        if a == 0x100:
            s += " ** "
            continue
        d = ' ' if a > 0 else '-'
        s += "%c%02X%c" % (d, abs(a), d)
    s += " ***"
    return s

def get_motor(args):
    if args.motor == "dummy":
        return DummyMotor()
    if os.uname()[1] == "pi":
        return ArduinoMotor()
    else:
        return DummyMotor()

def test(args):
    #TEST_PATTERN = [(255,255), (0, 255), (0, 0), (-255, 0), (-255, -255), (0, 0)]
    TEST_PATTERN = [(0xFF, 0xFF), (0x100, 0x00), (0xFF, 0xFF), (0x00, 0x100)]

    motor = get_motor(args)

    for i in range(1):
        for instruction in TEST_PATTERN:
            motor.process(instruction)
            print describe(instruction)
            time.sleep(2)
    motor.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor")
    args = parser.parse_args()
    test(args)
