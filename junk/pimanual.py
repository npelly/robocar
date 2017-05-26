import picamera
import picamera.array
import time
import cv2
import motorcontrol
import processimage
import select
import sys

FAST = 0xD0
SLOW = 0xB0

motor = motorcontrol.MotorControl()

done = False
while not done:
    c = sys.stdin.readline()[0]
    if (c == 'w' or c == 'W'):
        motor.drive(SLOW, SLOW)
    if (c == 'd' or c == 'D'):
        motor.drive(0x00, FAST)
    if (c == 'a' or c == 'A'):
        motor.drive(FAST, 0x00)
    if (c == 'q' or c == 'Q'):
        done = True
    if (c == 's' or c == 'S'):
        motor.stop()
    if (c == 'b' or c == 'B'):
        motor.drive(-LEFT, -RIGHT)

motor.stop()
motor.close()
