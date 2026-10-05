"""
detection.py

Handles the "Detection" side of the Environment/Feedback (I/O) task:
    - Poll an ultrasonic distance sensor
    - Pulse/flash an IR illuminator LED when a vehicle is detected
    - Run a background loop that calls a callback function when a
      vehicle comes within range

Hardware assumed once wired up (update pins to match your wiring):
    - HC-SR04 ultrasonic distance sensor (TRIG / ECHO pins)
    - A single IR illuminator LED driven from a GPIO pin

Uses gpiozero, the standard high-level GPIO library on Raspberry Pi OS.
Install with: sudo apt install python3-gpiozero  (usually preinstalled)

PROOF-OF-CONCEPT MOCK MODE
---------------------------
We don't have the ultrasonic sensor yet, so by default this class runs
in mock mode: `read_distance_sensor()` just returns a random value
between 0.1 and 2.0 metres instead of reading real hardware. This lets
the whole detection -> LED pipeline be built and tested now.

Switch to real hardware later by passing `use_mock=False` once the
sensor and LED are wired up - no other code needs to change, since
whoever calls `Detection` only ever sees `get_range()` / `start()`.
"""

import random
import threading
import time


def read_distance_sensor() -> float:
    """
    MOCK distance reading, standing in for the real ultrasonic sensor
    until we have the hardware. Returns a random distance in metres,
    between 0.1 and 2.0 m, simulating a vehicle approaching at a
    random position.
    """
    return random.uniform(0.1, 2.0)


class _MockLed:
    """Stand-in for gpiozero.LED when we don't have an IR LED wired up yet."""

    def on(self):
        print("[mock IR LED] ON")

    def off(self):
        print("[mock IR LED] OFF")


class Detection:
    """Encapsulates vehicle detection hardware: ultrasonic sensor + IR LED."""

    def __init__(
        self,
        trigger_pin: int = 23,
        echo_pin: int = 24,
        ir_led_pin: int = 17,
        trigger_distance_m: float = 1.0,
        poll_interval_s: float = 0.2,
        use_mock: bool = True,
    ):
        """
        trigger_pin / echo_pin: GPIO BCM pin numbers for the HC-SR04
                                 (only used when use_mock=False).
        ir_led_pin:             GPIO BCM pin for the IR illuminator LED
                                 (only used when use_mock=False).
        trigger_distance_m:     distance (metres) within which a vehicle
                                 counts as "detected". Defaults to 1m so
                                 it triggers sensibly against the mocked
                                 0.1-2.0m range; tune this once the real
                                 sensor/car-park geometry is known (user
                                 story asks for 3m).
        poll_interval_s:        how often to check the sensor, in seconds.
        use_mock:                True (default): use read_distance_sensor()
                                 and a fake LED - no hardware required.
                                 False: use the real HC-SR04 + IR LED via
                                 gpiozero (requires hardware to be wired up).
        """
        self.use_mock = use_mock
        self.trigger_distance_m = trigger_distance_m
        self.poll_interval_s = poll_interval_s

        if use_mock:
            self.sensor = None
            self.ir_led = _MockLed()
        else:
            # Imported lazily so this module still runs fine on a machine
            # without gpiozero/RPi.GPIO installed, as long as use_mock=True.
            from gpiozero import DistanceSensor, LED
            self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin,
                                          max_distance=4)
            self.ir_led = LED(ir_led_pin)

        self._running = False
        self._thread = None

    def get_range(self) -> float:
        """Return the current measured distance in metres."""
        if self.use_mock:
            return read_distance_sensor()
        return self.sensor.distance

    def pulse_led(self, duration_s: float = 0.5):
        """Flash the IR illuminator LED on, then off after duration_s."""
        self.ir_led.on()
        time.sleep(duration_s)
        self.ir_led.off()

    def _on_vehicle_detected(self, on_detect):
        """
        Internal handler run when a vehicle enters range. Pulses the
        LED first, then calls the supplied callback - this is the
        extension point the camera team member hooks into.
        """
        self.pulse_led()
        if on_detect is not None:
            on_detect()

    def _poll_loop(self, on_detect):
        while self._running:
            distance = self.get_range()
            if distance <= self.trigger_distance_m:
                self._on_vehicle_detected(on_detect)
            time.sleep(self.poll_interval_s)

    def start(self, on_detect=None):
        """
        Start polling the distance sensor in a background thread.

        on_detect: a zero-argument function called every time a vehicle
                   is detected within range (after the IR LED pulse).
                   This is where the camera team member's frame-capture
                   / OCR trigger function should be plugged in, e.g.:

                        detection.start(on_detect=camera.capture_and_process)
        """
        if self._running:
            return  # already running
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop, args=(on_detect,), daemon=True
        )
        self._thread.start()

    def stop(self):
        """Stop the background polling loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join()


if __name__ == "__main__":
    # Manual test - runs in mock mode by default, so this works right now
    # without any hardware at all. Prints a message each time a vehicle
    # is "detected".

    def on_vehicle():
        print("Vehicle detected! (LED pulsed)")

    detection = Detection()  # use_mock=True by default
    print("Starting detection loop (MOCK mode). Ctrl+C to stop.")
    detection.start(on_detect=on_vehicle)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detection.stop()
        print("Stopped.")