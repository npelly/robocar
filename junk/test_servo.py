import Adafruit_PCA9685

# Initialise the PCA9685 using the default address (0x40).
self.pwm = Adafruit_PCA9685.PCA9685()

self.pwm.set_pwm_freq(60)

while True:
    pwm.set_pwm(1, 0, int(input('set PWM value: ')))
