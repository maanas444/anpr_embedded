import cv2
import pytesseract
from pytesseract import TesseractNotFoundError


def extract_license_plates(frame):
    gray      = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    try:
        return pytesseract.image_to_string(thresh, config="--psm 8")
    except:
        print(f"[ERROR] Tesseract is not installed (or not added to system PATH)!\n        Run 'install-ocr' to install!")

        import sys
        sys.exit(1)
