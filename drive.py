"""Drive Robocar

Usage:
  drive.py [--framerate=<fps>] [--dummy_motor] [--telemetry SERVER]

Options:
  -h --help           Print this help text
  --dummy_motor       Use a dummy motor
  --framerate FPS     Attempt to run camera at specified framerate [DEFAULT: 30]
  --telemetry SERVER  Optional Telemetry Server, example "pi.local:7007"
"""

import cPickle as pickle
import docopt
import Queue

import robocore.camera
import robocore.perceptor
import robocore.car_model
import robocore.motor
import robocore.telemetry_producer
import robocore.util


if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    framerate = int(args["--framerate"])
    resolution = (160, 128)
    telemetry_server = args["--telemetry"]

    if telemetry_server:
        telemetry_server = "ws://%s/api/telemetry" % telemetry_server

    if robocore.util.isRaspberryPi():
        camera = robocore.camera.PiCamera(resolution, framerate)
        perceptor = robocore.perceptor.Perceptor(resolution)
        car_model = robocore.car_model.RoboCar72v()
        if not args["--dummy_motor"]:
            motor = robocore.motor.ArduinoSerialMotor()
        else:
            motor = robocore.motor.DummyMotor()
        telemetry_producer = robocore.telemetry_producer.TelemetryProducer(telemetry_server)
    else:
        camera = robocore.camera.DummyCamera(resolution, framerate)
        perceptor = robocore.perceptor.Perceptor(resolution)
        car_model = robocore.car_model.RoboCar72v()
        motor = robocore.motor.DummyMotor()
        telemetry_producer = robocore.telemetry_producer.TelemetryProducer(telemetry_server)

    perceptor_profiler = robocore.util.SectionProfiler()
    car_model_profiler = robocore.util.SectionProfiler()
    motor_profiler = robocore.util.SectionProfiler()

    print "ENTER to finish"

    with camera as camera_image_queue, motor, telemetry_producer:
        while not robocore.util.check_stdin():
            try:
                image = camera_image_queue.get(block=True, timeout=1.0)
            except Queue.Empty:
                print "warning: delayed camera image"
                continue

            if robocore.util.check_stdin(): break

            with perceptor_profiler:
                observations = perceptor.process(image)

            with car_model_profiler:
                instructions = car_model.process(observations)

            with motor_profiler:
                motor.process(instructions)

            print image, observations, instructions

            telemetry_producer.process(image, observations, instructions)

    print "Perception processing:", perceptor_profiler
    print "Car Model processing:", car_model_profiler
    print "Motor processing:", motor_profiler
