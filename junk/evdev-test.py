import evdev

devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
for device in devices:
    print(device.fn, device.name, device.phys)

device = evdev.InputDevice('/dev/input/event1')
print device

for event in device.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        print categorize(event)
