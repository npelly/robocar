

class statistics:
    def __init__(self):
        self.prev_timestamp = 0.0

        self.average_cross_track_error = 0
        self.average_cross_track_error_absolute = 0
        self.average_cross_track_error_squared = 0

    def process(self, observation, instruction):
        cross_track_error, timestamp = observations
        cross_track_error_absolute = abs(cross_track_error)
        cross_track_error_squared = cross_track_error ** 2

        self.average_

    def updateAverage(average, size, value)


    def print_summary(self):
