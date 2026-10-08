"""detection.py - detects a vehicle and pulses the IR LED."""

import time
import lgpio
from sense_hat import SenseHat, ACTION_PRESSED  # TODO: Remove, Placeholder

sense = SenseHat()

LED_PIN = 17
TRIGGER_PIN = 5

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, LED_PIN)
# lgpio.gpio_claim_input(h, TRIGGER_PIN, lgpio.SET_PULL_UP)  # TODO: Uncomment


def should_trigger():
    # """Real check: True while the trigger pin is touched to GND."""
    # return lgpio.gpio_read(h, TRIGGER_PIN) == 0   # TODO: Uncomment

    # TODO: Remove, Placeholder
    try:
        return sense.stick.wait_for_event().action == ACTION_PRESSED
    except KeyboardInterrupt:
        return False


def led_on():
    lgpio.gpio_write(h, LED_PIN, 1)
def led_off():
    lgpio.gpio_write(h, LED_PIN, 0)

# def pulse_led():
#     lgpio.gpio_write(h, LED_PIN, 1)
#     time.sleep(0.5)
#     lgpio.gpio_write(h, LED_PIN, 0)


# def detect_loop(on_detect=None):
#     while True:
#         if should_trigger():
#             pulse_led()
#             if on_detect:
#                 on_detect()
#         time.sleep(0.2)


# if __name__ == "__main__":
#     detect_loop(on_detect=lambda: print("Vehicle detected!"))
