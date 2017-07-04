import cv2
import sys
import numpy
import time
import os

import images

"""
cross_track_error (float) [-1.0, +1.0]
visible           (boolean)
time              (float) local time of this observation
time_delta        (float) time delta since previous visible=true observation
"""
class Observation:
    def __init__(self, cross_track_error, visible, time, time_delta):
        self.cross_track_error = cross_track_error
        self.visible = visible
        self.time = time
        self.time_delta = time_delta

    def __str__(self):
        if not self.visible: return "------"
        return "%+.3f" % self.cross_track_error

"""
1) HSV filter image to find a color of interest
2) Apply weight matrix and sum to find cross track error

If there is a single pixel of interest in bottom left, cross track error is -1.0
If there is a single pixel of interest in bottom right, cross track error is +1.0
etc
"""
class FilterAndWeighPixelPerception:
    def __init__(self, config):
        self.X = config["Camera"].getint("RESOLUTION_WIDTH")
        self.Y = config["Camera"].getint("RESOLUTION_HEIGHT")
        self.N = self.X * self.Y

        config = config["Perception"]
        Y_TOP_WEIGHT = config.getfloat("Y_TOP_WEIGHT")
        Y_BOT_WEIGHT = config.getfloat("Y_BOT_WEIGHT")
        lower, upper = eval(config.get("HSV_FILTER"))
        self.HSV_FILTER_LOWER = numpy.array(lower)
        self.HSV_FILTER_UPPER = numpy.array(upper)
        self.VISIBLE_THRESHOLD = config.getfloat("VISIBLE_THRESHOLD")

        self.WEIGHTS = self._create_weight_matrix(self.Y, self.X, Y_TOP_WEIGHT, Y_BOT_WEIGHT)

        self.last_visible_time = 0.0

    """
    Create weights array:
        -w ... 0 ... +w
           ...   ...
        -1 ... 0 ... +1
    Where w is y_0_weight
    """
    def _create_weight_matrix(self, Y, X, y_0_weight, y_Y_weight):
        weights = numpy.empty([Y, X])
        y_start = y_0_weight
        y_delta = (y_Y_weight - y_start) / (Y - 1)

        for x in xrange(X):
            x_weight = 2.0 * x / (X - 1) - 1.0  # -1.0 ... +1.0
            w = y_start * x_weight
            delta = y_delta * x_weight
            for y in xrange(Y):
                weights[y, x] = w
                w += delta
        return weights

    def process(self, image, telemetry):
        hsv_image = cv2.cvtColor(image.data, cv2.COLOR_BGR2HSV)

        filtered_image = cv2.inRange(hsv_image, self.HSV_FILTER_LOWER, self.HSV_FILTER_UPPER)
        # image: single channel with each pixel 0 or 255

        telemetry["filtered_image"] = images.NumpyImage(filtered_image, 0.0, 0.0)

        filtered_pixel_count = numpy.sum(filtered_image) / 255
        filtered_pixel_ratio = float(filtered_pixel_count) / self.N
        telemetry["filtered_pixel_count"] = filtered_pixel_count
        telemetry["filtered_pixel_ratio"] = filtered_pixel_ratio
        if filtered_pixel_ratio < self.VISIBLE_THRESHOLD:
            return Observation(0.0, False, image.time, 0.0)

        cross_track_error = numpy.sum(filtered_image * self.WEIGHTS) / 255 / filtered_pixel_count
        if self.last_visible_time == 0.0:  # first visible
            time_delta = 0.0
        else:
            time_delta = image.time - self.last_visible_time
        self.last_visible_time = image.time
        return Observation(cross_track_error, True, image.time, time_delta)
