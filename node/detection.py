"""detection.py - detects a vehicle and pulses the IR LED."""

import random
import time

TRIGGER_DISTANCE_M = 1.0


def read_distance_sensor():
    """Mock check: True if a vehicle is within range."""
    distance = random.uniform(0.1, 2.0)
    return distance <= TRIGGER_DISTANCE_M


def pulse_led():
    print("IR LED ON")
    time.sleep(0.5)
    print("IR LED OFF")


def detect_loop(on_detect=None):
    while True:
        if read_distance_sensor():
            pulse_led()
            if on_detect:
                on_detect()
        time.sleep(0.2)


if __name__ == "__main__":
    detect_loop(on_detect=lambda: print("Vehicle detected!"))