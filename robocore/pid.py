class Pid:
    def __init__(self, k_p, k_i, k_d):
        self.k_p = float(k_p)
        self.k_i = float(k_i)
        self.k_d = float(k_d)
        self.prev_error = 0.0
        self.sum_error_time = 0.0

    def update(self, error, time_delta):
        p = self.k_p * error
        self.sum_error_time += error * time_delta
        i = self.k_i * self.sum_error_time
        if time_delta > 0.0:
            d = self.k_d * (error - self.prev_error) / time_delta
        else:   # first loop
            d = 0.0
        self.prev_error = error

        pid = p + i + d

        pid_debug = "P=%.3f I=%.3f D=%.3f t=%.3f PID=%.3f" % (p, i, d, time_delta, pid)

        return pid, pid_debug
