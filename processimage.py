import cv2
import sys
import numpy as np
import time
import mytimer

"""
Take an image and decide on motor drive values
Input: numpy array
Output: (leftSpeed, rightSpeed)
"""
def process(image, show=False):
    if show: import showimage

    t = mytimer.MyTimer()

    t.stamp()
#    image = cv2.bilateralFilter(image, 20, 150, 150)
    t.stamp("bilateralFilter")
    if show: showimage.showSmallImage(image)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    t.stamp("BGR2HSV")
    if show: showimage.showSmallImage(image)

    lower_blue = np.array([90,150,50])
    upper_blue = np.array([130,255,255])
    mask = cv2.inRange(image, lower_blue, upper_blue)
    image = cv2.bitwise_and(image, image, mask = mask)

    t.stamp("filter blue")
    if show: showimage.showSmallImage(image)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # grayscale

    t.stamp("BGR2GRAY")
    if show: showimage.showSmallImage(image)

    (l, m, r) = _count(image)
    t.stamp("count()")
    print "lmr %d %d %d" % (l, m, r)

    #t.printStamps()

    if show: showimage.closeOnInput()

    THRES = 2.0
    FAST  = 0xA0
    SLOW  = 0x80
    TIME = 0.06
    if l > r and l > m and l > THRES:
        print "left"
        return (0x00, 0xA0, TIME)
    if r > l and r > m and r > THRES:
        print "right"
        return (0xA0, 0x00, TIME)
    if m > r and m > l and m > THRES:
        if r > THRES or l > THRES:
            print "carefull forward"
            return (SLOW, SLOW, TIME)
        else:
            print "fast forward"
            return (FAST, FAST, TIME)
    print "stop"

    return (0x00, 0x00, 0.1)

def _count(image):
    #crop
    (Y, X) = image.shape[:2]
    left = image[int(Y*0.2):Y, 0:int(X*0.2)]
    middle = image[int(Y*0.2):Y, int(X*0.2):int(X*0.8)]
    right = image[int(Y*0.2):Y, int(X*0.8):X]

    leftCount = np.mean(left)
    rightCount = np.mean(right)
    middleCount = np.mean(middle)
    return (leftCount, middleCount, rightCount)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "USAGE:"
        print "    python processimage.py JPEG"
        sys.exit()

    filename = sys.argv[1]
    image = cv2.imread(filename)  #BGR

    (left, right, duration) = process(image, show=True)

    print left, right, duration
