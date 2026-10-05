import cv2
import pytesseract


def extract_license_plates(frame):
    gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    return pytesseract.image_to_string(thresh, config="--psm 8")
