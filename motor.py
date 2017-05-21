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

import car_model
import timer

DEBUG = False

class DummyMotor:
    def process(self, instructions):
        pass

    def close(self):
        pass

class ArduinoMotor:
    ARUDINO_PORT = "/dev/ttyACM"
    ARDUINO_BAUDRATE = 9600
    ENABLE_READ_THREAD = False

    def __init__(self):
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

    def close(self):
        if self.serial is None: return
        self._send("F00F00\n")
        serial = self.serial
        self.serial = None
        serial.close()
        print "closed serial port"

    def _send(self, command):
        if self.serial is None: return

        self.serial.write(command)
        if DEBUG: print ">", command,

    def _read(self):
        try:
            while self.serial is not None:
                input = self.serial.readline()
                if input and DEBUG: print "<", input,
        except (OSError, select.error, TypeError):
            pass


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
        for left, right in TEST_PATTERN:
            instruction = car_model.Instruction(left, right)
            motor.process(instruction)
            print instruction
            time.sleep(2)
    motor.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor")
    args = parser.parse_args()
    test(args)
