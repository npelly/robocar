import time
import select
import sys
import Queue
import threading
import argparse

import timer
import motor
import car_model
import camera
import perceptor

def main(args):
    cancel = False
    with camera.get_camera() as camera_image_queue:
        per = perceptor.get_perceptor(camera.CAMERA_RESOLUTION)
        car = car_model.get_car_model()
        moto = motor.get_motor(args)

        camera_queue = cam.start()

        per_timer = timer.HistogramTimer()
        car_timer = timer.HistogramTimer()
        moto_timer = timer.HistogramTimer()

        print "ENTER to finish"
        try:
            while not check_stdin():
                try:
                    image = camera_queue.get(block=True, timeout=0.2)
                except Queue.Empty:
                    print "warning: delayed camera image"
                    continue

                if check_stdin(): break

                per_timer.enter()
                observations = per.process(image)
                per_timer.exit()

                if check_stdin(): break

                car_timer.enter()
                instructions = car.process(observations)
                car_timer.exit()

                if check_stdin(): break

                moto_timer.enter()
                moto.process(instructions)
                moto_timer.exit()

                print image, observations, instructions

                statistics.process(observations, instructions)

            moto.close()

    print "Perception processing:",
    per_timer.print_summary()
    print "Car Model processing:",
    car_timer.print_summary()
    print "Motor processing:",
    moto_timer.print_summary()

def check_stdin():
    r, _, _ = select.select([sys.stdin], [], [], 0.0)
    return r

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor")
    args = parser.parse_args()
    main(args)
