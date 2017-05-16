"""
Motor driver control.
Implemented via serial protocol to arudino.
"""

import serial
import threading
import time
import mytimer

class MotorControl:
    _ARUDINO_PORT = "/dev/ttyACM"
    _ARDUINO_BAUDRATE = 9600
    _KEEPALIVE_SECONDS = 4.0

    _serial = None
    _serialLock = threading.Lock()
    _nextKeepalive = None

    def __init__(self):
        for i in range(10):
            port = self._ARUDINO_PORT + str(i)
            try:
                self._serial = serial.Serial(port, self._ARDUINO_BAUDRATE, timeout=1.0)
                threading.Thread(target=self._read).start()
                print "opened", port
                return
            except serial.SerialException:
                continue
        print "ERROR: Could not open any", self._ARUDINO_PORT + "x"

    def close(self):
        with self._serialLock:
            self._serial.close()
            self._serial = None
            print "closed serial port"

    """left and right in range [-255, 255]"""
    def drive(self, left, right):
        l = 'F' if left >= 0 else 'R'
        r = 'F' if right >= 0 else 'R'
        command = "%c%02X%c%02X\n" % (l, abs(left), r, abs(right))
        self._send(command, True)

    def stop(self):
        self._send("F00F00\n", False)

    def _send(self, command, keepalive, isKeepalive=False):
        with self._serialLock:
            if self._serial is None:
                return

            # Pretty print
            k = '*' if isKeepalive else ' '
            print ">" + k + command,

            self._serial.write(command)

            # Schedule keepalive
            if (self._nextKeepalive is not None):
                self._nextKeepalive.cancel()
            if (keepalive):
                self._nextKeepalive = threading.Timer(
                    self._KEEPALIVE_SECONDS, self._send,
                    args=[command, True, True])
                self._nextKeepalive.start()

    def _read(self):
        while self._serial is not None:
            input = self._serial.readline()
            #if input is not None:
                #print "<", input,

def test():
    motor = MotorControl()

    while (1):
        motor.drive(255, 255)
        time.sleep(0.1)
        motor.stop()
        time.sleep(0.1)


if __name__ == "__main__":
    test()
