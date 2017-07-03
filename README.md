# Robocar (self-driving vehicle) platform

There are two core executables, drive.py and telemetryserver.py

telemetryserver.py
- Provides interface to archived and live telemetry at http://localhost:7007.
- Listens for incoming telemetry from vehicle(s)

drive.py
- Executes autonomous driving on-board a vehicle, or,
- Simulates autonomous driving based on archived telemetry

Basic Usage:
- python telemetryserver.py   # on laptop/workstation, now browse http://localhost:7007
- python drive.py config.ini  # on vehicle

For advanced usage check command line options on drive.py

Features
- Fully on-board compute pipeline.
- Live telemetry streamed to remote server.
- Designed for experimentation: tunable via config.ini's or replace entire pipeline stages
- Generalized camera / perception / vehicle_dynamics / actuator pipeline.
- Extensible telemetry - just add key:value pairs to the dictionary and they'll show in UI

Supported Vehicles:
- "Newton" 2WD differential drive with caster wheel. See config-newton.ini
- "Euler" 1/10th RC car with servo steering and ESC. See config-euler.ini

"Newton" Notes
- Install and load arduino-driver/ on the Arduino using platformio.

Dependencies:
- Python 2.7
- Numpy
- PiCamera
- OpenCV
- docopt
- websocket-client

Optional Dependencies:
- pygame (for manual_drive.py on host)
