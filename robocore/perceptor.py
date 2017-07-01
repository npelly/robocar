import cv2
import sys
import numpy
import time
import os

class Observation:
    def __init__(self, cross_track_error, visible, obs_time, obs_time_delta):
        self.cross_track_error = cross_track_error
        self.visible = visible
        self.time = obs_time
        self.time_delta = obs_time_delta
    def __str__(self):
        if not self.visible: return "-----"
        return "%+.4f" % self.cross_track_error
    def to_telemetry_dict(self):
        return dict(cross_track_error=self.cross_track_error,
                    visible=self.visible)

class Perceptor:
    def __init__(self, resolution):
        (self.X, self.Y) = resolution
        self.weights = self._create_weights(self.Y, self.X, 0.2)

    def process(self, camera_image, show=False):
        image = camera_image.image
    #    image = cv2.cvtColor(image, cv2.COLOR_YUV420p2RGB)

        if show:
            cv2.imshow('perception', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        if show:
            cv2.imshow('perception', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        lower_blue = numpy.array([90,150,50])
        upper_blue = numpy.array([130,255,255])
        mask = cv2.inRange(image, lower_blue, upper_blue)
        image = cv2.bitwise_and(image, image, mask = mask)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if show:
            cv2.imshow('perception', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        error, visible = self._cross_track_error(image)

        return Observation(error, visible, camera_image.time, camera_image.time_delta)

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
        return (pixel_error, True)
