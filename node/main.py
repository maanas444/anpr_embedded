#!/usr/bin/env python3
import time
import datetime

from node.camera import Camera
from node.ocr_ml import load_model, extract_number_plates


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
    frame = cam.read_frame()
    timestamp_ns = time.time_ns()

    # TODO: Remove, for debugging
    import cv2
    cv2.imwrite("../results/image.jpg", frame)
    print("Got image - Extracting plates...")

    plates = extract_number_plates(frame)
    for plate in plates:
        number_plate_read(plate, timestamp_ns)

def main():
    load_model()

def test():
    load_model()
    input("Camera ready")
    trigger_read()


if __name__ == "__main__":
    test()
