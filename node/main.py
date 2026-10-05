#!/usr/bin/env python3
from node.camera import Camera
# from node.ocr import extract_number_plates, find_plate_by_contours, find_plate_by_yolo, preprocess_plate
from node.ocr_ml import extract_number_plates

cam = Camera()

def trigger_read():
    # frame = cam.read_frame()  # TODO: Uncomment, for debugging
    import cv2  # TODO: Remove, for debugging
    frame = cv2.imread("../ocr-samples/four-plates-vertical-stack.jpg")  # TODO: Remove, for debugging
    # frame = cv2.imread("../captured_image.jpg")  # TODO: Remove, for debugging

    # extract_number_plates(frame)
    # text  = extract_number_plates(frame)
    # print(f"Number Plate: \"{text}\"")

    for i, plate in enumerate(extract_number_plates(frame)):
        print(f"[{i}] Number Plate: \"{plate}\"")


def main():
    # print("Hello, from a Camera Node!")
    trigger_read()

    # img_path = "../ocr-samples/four-plates-vertical-stack.jpg"
    # find_plate_by_contours(img_path)
    # # find_plate_by_yolo(img_path)

    # print(f"License Plate 0: \"{extract_number_plates("../results/cropped_plate_2.jpg")}\"")
    # print(f"License Plate 1: \"{extract_number_plates("../results/cropped_plate_0.jpg")}\"")
    # print(f"License Plate 2: \"{extract_number_plates("../results/cropped_plate_3.jpg")}\"")
    # print(f"License Plate 3: \"{extract_number_plates("../results/cropped_plate_1.jpg")}\"")
    


if __name__ == "__main__":
    main()
