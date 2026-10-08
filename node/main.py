#!/usr/bin/env python3
import time
import datetime
import threading

from node.camera import Camera
from node.ocr_ml import load_model, get_ocr_reader, extract_number_plates

from node.detection import should_trigger, led_on, led_off
from node.led_matrix import show_checkmark, show_cross, scroll_text


cam = Camera()

def _print_timestamp(timestamp_ns):
    seconds = timestamp_ns // 1_000_000_000
    milliseconds = (timestamp_ns % 1_000_000_000) // 1_000_000
    
    local_dt = datetime.datetime.fromtimestamp(seconds)
    
    formatted_time = local_dt.strftime(f"%Y/%m/%d %H:%M:%S.{milliseconds:03d}")
    return formatted_time

def number_plate_read(plate_text_raw, timestamp_ns):
    MAX_LENGTH = 10

    plate = plate_text_raw[:MAX_LENGTH]
    print(f"[{_print_timestamp(timestamp_ns)}] Number Plate: \"plate\" (RAW:\"{plate_text_raw}\")")

    # TODO: Trigger DB sender

def trigger_read():
    led_on()
    frame = cam.read_frame()
    timestamp_ns = time.time_ns()
    led_off()

    # TODO: Remove, for debugging
    import cv2
    cv2.imwrite("../results/image.jpg", frame)
    print("Got image - Extracting plates...")

    plates = extract_number_plates(frame)
    if plates is None:
        print("No plates found!")
        show_cross()
        return
    show_checkmark()
    for plate in plates:
        number_plate_read(plate, timestamp_ns)

def main():
    load_model()
    get_ocr_reader()  # Initialise OCR reader

    while True:

        if should_trigger():
            trigger_read()


        time.sleep(0.1)

def test():
    load_model()
    get_ocr_reader()  # Initialise OCR reader

    input("Camera ready! ")
    trigger_read()


if __name__ == "__main__":
    test()
