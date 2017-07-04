"""
Drive Robocar.

Usage:
  drive.py -h | --help
  drive.py CONFIG_PATH [--telemetry SERVER] [--camera_replay PATH]

Examples:
  drive.py config-newton.ini

Options:
  -h --help             Show this help text
  --telemetry SERVER    Telemetry Server [Default: localhost:7007]
  --camera_replay PATH  Optional: replay camera from telemetry at PATH
"""

import cPickle as pickle
import configparser
import docopt
import Queue

import robocore.cameras
import robocore.perception
import robocore.vehicle_dynamics
import robocore.telemetry_client
import robocore.util

if __name__ == "__main__":
    args = docopt.docopt(__doc__)

    config = configparser.SafeConfigParser(inline_comment_prefixes='#;')
    config.readfp(open(args["CONFIG_PATH"], 'r'))

    if args["--camera_replay"]:
        camera = robocore.cameras.ReplayCamera(config, args["--camera_replay"])
    else:
        try:
            camera_class = getattr(robocore.cameras, config["Camera"].get("CLASS"))
            camera = camera_class(config)
        except EnvironmentError:  # HW not available, fallback to Dummy Camera
            camera = robocore.cameras.DummyCamera(config)

    perception = getattr(robocore.perception, config["Perception"].get("CLASS"))(config)

    vehicle = getattr(robocore.vehicle_dynamics, config["VehicleDynamics"].get("CLASS"))(config)

    actuator = getattr(robocore.actuators, config["VehicleDynamics"].get("ACTUATOR_CLASS"))(config)

    with open(args["CONFIG_PATH"], 'r') as config_file:
        telemetry_server = args["--telemetry"]
        telemetry_client = robocore.telemetry_client.TelemetryClient(telemetry_server, config_file.read())

    perception_profiler = robocore.util.SectionProfiler()
    vehicle_profiler = robocore.util.SectionProfiler()

    print "ENTER to finish"

    with camera, actuator, telemetry_client:
        while not robocore.util.check_stdin():
            image, telemetry = camera.wait_for_next_image(break_func=robocore.util.check_stdin)
            telemetry["image_desc"] = str(image)
            if not image or robocore.util.check_stdin(): break

            with perception_profiler:
                observation = perception.process(image, telemetry)
                telemetry["observation"] = str(observation)

            with vehicle_profiler:
                instruction = vehicle.process(observation, telemetry)
                actuator.process(instruction, telemetry)
                telemetry["instruction"] = str(instruction)

            print image, observation, instruction

            telemetry_client.process_async(telemetry)

    print "Perception processing:", perception_profiler
    print "Vehicle processing:", vehicle_profiler
