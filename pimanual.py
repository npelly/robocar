import picamera
import picamera.array
import time
import cv2
import motorcontrol
import processimage
import select
import sys

LEFT = 0xA0
RIGHT = 0xA0

motor = motorcontrol.MotorControl()

done = False
while not done:
    c = sys.stdin.readline()[0]
    if (c == 'f' or c == 'F'):
        motor.drive(LEFT, RIGHT)
    if (c == 'l' or c == 'L'):
        motor.drive(0x00, RIGHT)
    if (c == 'r' or c == 'R'):
        motor.drive(LEFT, 0x00)
    if (c == 'q' or c == 'Q'):
        done = True
    if (c == 's' or c == 'S'):
        motor.stop()
    if (c == 'b' or c == 'B'):
        motor.drive(-LEFT, -RIGHT)

motor.stop()
motor.close()
