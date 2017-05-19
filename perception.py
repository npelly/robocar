import cv2
import sys
import numpy
import time
import os
import argparse

import timer

class Perception:
    def __init__(self, resolution):
        (self.X, self.Y) = resolution
        self.weights = self._create_weights(self.Y, self.X, 0.2)

    def process(self, image):
    #    image = cv2.cvtColor(image, cv2.COLOR_YUV420p2RGB)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        lower_blue = numpy.array([90,150,50])
        upper_blue = numpy.array([130,255,255])
        mask = cv2.inRange(image, lower_blue, upper_blue)
        image = cv2.bitwise_and(image, image, mask = mask)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        error = self._cross_track_error(image)

        return error

    """
    distance_weight is the weight of pixels at y=0 compared to weight at y=Y
    """
    def _create_weights(self, Y, X, distance_weight):
        weights = numpy.empty([Y, X])
        (y_start, y_delta) = self._create_linear_weights(distance_weight, Y)

        for x in xrange(X):
            x_weight = float(x) / float(X/2) - 1.0
            w = y_start * x_weight
            delta = y_delta * x_weight
            for y in xrange(Y):
                weights[y, x] = w
                w += delta
        return weights

    """
    Calculate linear progression of n floats that sum to 1, and
    first number / last number is a.
    """
    def _create_linear_weights(self, a, n):
    #    end = 2.0 / n / (1.0 + a)
    #    start = a * end
    #    delta = end * (1.0 - a) / (n - 1.0)
        return (a, (1.0 - a) / (n - 1.0))


    def _cross_track_error(self, image):
        #target_region = image[int(Y*0.2):Y, :]
        target_region = image

        target_sum = numpy.sum(target_region)
        if target_sum < 10000:
            return (0, False)
        #print target_sum
    #    print numpy.sum(target_region * WEIGHTS)
        pixel_error = numpy.sum(target_region * self.weights) / target_sum
        print pixel_error
        return (pixel_error, True)

def describe(observation):
    (cross_track_error, visible) = observation
    if not visible: return "-----"
    return "%+.4f" % cross_track_error

def get_perception(resolution):
    return Perception(resolution)

def testImage(filename):
    image = cv2.imread(filename)  #BGR
    print process(image, show=False)

def testPi():
    import camera
    cam = camera.get_default_camera()
    queue = cam.start()
    for _ in xrange(30):
        image = queue.get(block=True)
        print image.shape
        print process(image)
    cam.close()

if __name__ == "__main__":
    if os.uname()[1] == "pi":
        testPi()
    else:
        if len(sys.argv) != 2:
            print "USAGE:"
            print "    python processimage.py JPEG"
            sys.exit()
        testImage(sys.argv[1])
