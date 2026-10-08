"""blink_test.py - simple LED blink test on GPIO2."""

import time
from gpiozero import LED

LED_PIN = 2

led = LED(LED_PIN)

while True:
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)