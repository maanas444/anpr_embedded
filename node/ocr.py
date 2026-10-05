import cv2
import pytesseract
from pytesseract import TesseractNotFoundError


def _preprocess_plate(frame):
    """Clean and enhance a cropped license plate image for OCR."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 1. Bilateral filter removes noise while keeping edges sharp
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    # 2. Adaptive threshold handles uneven lighting and shadows
    thresh = cv2.adaptiveThreshold(
        filtered,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )

    # TODO: Remove, for debugging
    combined = cv2.vconcat([
        frame, 
        cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), 
        cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    ])
    cv2.imwrite("../frame_processing.jpg", combined)

    return thresh  # Return pre-processed frame

def extract_license_plates(frame):
    # PSM 7 = Single line of text
    # With the addition of a character whitelist
    OCR_CONFIG = r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    processed_image = _preprocess_plate(frame)

    try:
        return pytesseract.image_to_string(processed_image, config=OCR_CONFIG)
    except TesseractNotFoundError:
        print(f"[ERROR] Tesseract is not installed (or not added to system PATH)!\n        Run 'install-ocr' to install!")

        import sys
        sys.exit(1)
