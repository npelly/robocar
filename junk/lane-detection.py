#!/usr/bin/python

import numpy as np
import sys
import cv2

import showimage
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def main():
    if len(sys.argv) != 2:
        print "USAGE:"
        print "    python lane-detection.py JPEG"
        return

    filename = sys.argv[1]
    image = cv2.imread(filename)  #BGR
    pipeline(image)

    (h, w) = image.shape[:2]
    h /= 2
    w /= 2
    image = cv2.resize(image, (w, h))
    pipeline(image)

    showimage.closeOnInput()



def pipeline(image):
    image = flip(image)
    image = cv2.bilateralFilter(image, 20, 150, 150)
    showimage.showSmallImage(image)



    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    showimage.showSmallImage(image)

    lower_blue = np.array([90,50,50])
    upper_blue = np.array([130,255,255])

    mask = cv2.inRange(image, lower_blue, upper_blue)
    image = cv2.bitwise_and(image, image, mask = mask)
    showimage.showSmallImage(image)

    image = grayscale(image)
    showimage.showSmallImage(image)

#    image = cv2.bilateralFilter(image, 20, 150, 150)
#    showimage.showSmallImage(image)

    #showimage.showSmallImage(cv2.Canny(image, 50, 100))
    #showimage.showSmallImage(cv2.Canny(image, 50, 200))
    #showimage.showSmallImage(cv2.Canny(image, 100, 150))
    #showimage.showSmallImage(cv2.Canny(image, 150, 200))
    image = cv2.Canny(image, 50, 200)
    showimage.showSmallImage(image)

    lines = cv2.HoughLinesP(image, rho=1, theta=np.pi/180.0, threshold=10,
                            minLineLength=40, maxLineGap=10)
    print "Hough lines: ", lines.shape[0]
    showimage.showSmallImage(createLineImage(lines, image.shape))


def flip(image):
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)

    # rotate the image by 180 degrees
    M = cv2.getRotationMatrix2D(center, 180, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def blue(img):
    blue = img[:,:,0]
    return blue

def green(img):
    green = img[:,:,1]
    return green

def red(img):
    red = img[:,:,2]
    return red

def createLineImage(lines, shape):
    image = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)

    N = lines.shape[0]
    for i in range(N):
        x1 = lines[i][0][0]
        y1 = lines[i][0][1]
        x2 = lines[i][0][2]
        y2 = lines[i][0][3]
        cv2.line(image,(x1,y1),(x2,y2),(255,0,0), 10)

    return image

if __name__ == "__main__":
    main()
