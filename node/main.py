#!/usr/bin/env python3
import time
import datetime
import threading

from node.camera import Camera
from node.ocr_ml import load_model, get_ocr_reader, extract_number_plates

from node.detection import should_trigger, led_on, led_off
from node.led_matrix import clear_matrix, show_checkmark, show_cross, scroll_text


DEBUG_MODE = True
NODE_ID = 69

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
    print(f"[{_print_timestamp(timestamp_ns)}] Number Plate: \"{plate}\" (RAW:\"{plate_text_raw}\")")

    # TODO: Trigger DB sender

    # Display number plate
    scroll_text(plate)

def trigger_read():
    led_on()
    frame = cam.read_frame()
    timestamp_ns = time.time_ns()
    led_off()

    if DEBUG_MODE:
        import cv2
        cv2.imwrite("../results/image.jpg", frame)
        print("Got image - Extracting plates...")

    plates = extract_number_plates(frame)

    if plates is None:
        print("No plates found!")
        show_cross()
        return

    for plate in plates:
        number_plate_read(plate, timestamp_ns)
    show_checkmark()


if DEBUG_MODE:
    import cv2
    def show():
        while cv2.waitKey(1) != ord('q'):
            frame = cam.read_frame()
            if frame is not None:
                cv2.imshow(f"Node{NODE_ID} - Cam", frame)
        cv2.destroyAllWindows()

def main():
    load_model()
    get_ocr_reader()  # Initialise OCR reader

    if DEBUG_MODE:
        threading.Thread(target=show).start()

    print("Running...")
    while True:

        if should_trigger():
            if DEBUG_MODE:
                print("Triggered!")
            
            trigger_read()

            # Wait before detecting again
            try:
                time.sleep(1.5)
            except KeyboardInterrupt:
                break
            finally:
                clear_matrix()

        # try:
        #     time.sleep(0.1)
        # except KeyboardInterrupt:
        #     break

def test():
    load_model()
    get_ocr_reader()  # Initialise OCR reader

    input("Camera ready! ")
    trigger_read()


if __name__ == "__main__":
    test()
