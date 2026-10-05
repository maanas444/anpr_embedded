#!/usr/bin/env python3
from node.camera import Camera
from node.ocr import extract_license_plates, find_plate_by_contours, find_plate_by_yolo


cam = Camera()

def trigger_read():
    # frame = cam.read_frame()  # TODO: Uncomment, for debugging
    import cv2  # TODO: Remove, for debugging
    frame = cv2.imread("../ocr-samples/four-plates-vertical-stack.jpg")  # TODO: Remove, for debugging
    # frame = cv2.imread("../captured_image.jpg")  # TODO: Remove, for debugging

    text  = extract_license_plates(frame)
    print(f"License Plate: \"{text}\"")

def main():
    # print("Hello, from a Camera Node!")
    # trigger_read()

    img_path = "../ocr-samples/four-plates-vertical-stack.jpg"
    find_plate_by_contours(img_path)
    find_plate_by_yolo(img_path)


if __name__ == "__main__":
    main()
