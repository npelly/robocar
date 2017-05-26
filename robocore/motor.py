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
