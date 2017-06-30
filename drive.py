"""Drive Robocar

Usage:
  drive.py [--framerate=<fps>] [--car_model=<model>] [--motor=<motor>] [--telemetry SERVER]

Options:
  -h --help           Print this help text
  --framerate FPS     Attempt to run camera at specified framerate [DEFAULT: 30]
  --car_model MODEL   Use specific car model [DEFAULT: auto]
  --motor MOTOR       Use specified motor control [DEFAULT: auto]
  --telemetry SERVER  Optional Telemetry Server, example "pi.local:7007"
"""

import cPickle as pickle
import docopt
import Queue

import robocore.camera
import robocore.perceptor
import robocore.car_model
import robocore.motor
import robocore.telemetry_client
import robocore.util


if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    framerate = int(args["--framerate"])
    resolution = (160, 128)
    telemetry_server = args["--telemetry"]

    if robocore.util.isRaspberryPi():
        camera = robocore.camera.PiCamera(resolution, framerate)
    else:
        camera = robocore.camera.DummyCamera(resolution, framerate)
    perceptor = robocore.perceptor.Perceptor(resolution)
    if args["--car_model"] == "auto":
        if robocore.util.isRobocar1():
            car_model = robocore.car_model.RoboCar72v()
        else:
            car_model = robocore.car_model.ServoCarTenth()
    else:
        car_model = getattr(robocore.car_model, args["--car_model"])()
    if args["--motor"] == "auto":
        if robocore.util.isRobocar1():
            motor = robocore.motor.ArduinoSerialMotor()
        elif robocore.util.isRobocar2():
            motor = robocore.motor.ServoMotor()
        else:
            motor = robocore.motor.DummyMotor()
    else:
        motor = getattr(robocore.motor, args["--motor"])()
    telemetry_client = robocore.telemetry_client.TelemetryClient(telemetry_server)

    perceptor_profiler = robocore.util.SectionProfiler()
    car_model_profiler = robocore.util.SectionProfiler()
    motor_profiler = robocore.util.SectionProfiler()

    print "ENTER to finish"

    with camera as camera_image_queue, motor, telemetry_client:
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

            if telemetry_client:
                telemetry_client.process(image, observations, instructions)

    print "Perception processing:", perceptor_profiler
    print "Car Model processing:", car_model_profiler
    print "Motor processing:", motor_profiler
