"""
demo_led_feedback.py

A small runnable demo of the LED matrix feedback, independent of the
distance sensor (since you don't have that hardware yet). This lets
you test/show off the Sense HAT part of your task today.

Simulates a "vehicle detected -> OCR result" pipeline:
    1. Show checkmark for a "recognised" plate + scroll the plate text
    2. Show cross for a "not recognised" plate

Run on the Pi:
    python3 demo_led_feedback.py
"""

import time
from led_matrix import LedMatrix


def simulate_plate_result(matrix: LedMatrix, plate: str | None):
    """
    plate: a sanitised plate string if OCR succeeded, or None if it
           failed / wasn't confident enough. This mirrors what the
           OCR module's return value will eventually feed in here.
    """
    if plate:
        print(f"Plate recognised: {plate}")
        matrix.show_checkmark()
        time.sleep(1.5)
        matrix.scroll_text(plate)
    else:
        print("Plate not recognised")
        matrix.show_cross()
        time.sleep(2)

    matrix.clear()


if __name__ == "__main__":
    matrix = LedMatrix()

    # Simulated detections - swap this for real OCR output later.
    test_results = ["ABC123", None, "XYZ789"]

    for result in test_results:
        simulate_plate_result(matrix, result)
        time.sleep(1)

    print("Demo finished.")