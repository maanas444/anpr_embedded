import cv2
import numpy as np
from pathlib import Path

import easyocr

# Suppress PyTorch deprecation/user warnings before imports
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
# Disable Ultralytics online/telemetry checks
import os
os.environ["YOLO_AUTOINSTALL"] = "False"
os.environ["ULTRALYTICS_AUTOINSTALL"] = "False"
from ultralytics import YOLO

DEBUG_MODE = True
RESULTS_FOLDER = "../results"
MODEL_PATH_WITHOUT_EXTENSION = "node/models/license-plate-finetune-v1n"  # Nano : 5.47 MB


def _export_model():
    model = YOLO(f"{MODEL_PATH_WITHOUT_EXTENSION}.pt")
    model.export(format="ncnn")

def find_plates(img):
    NCNN_MODEL_PATH = f"{MODEL_PATH_WITHOUT_EXTENSION}_ncnn_model"

    if not Path(NCNN_MODEL_PATH).exists():
        _export_model()  # Create NCNN (embedded) model

    # Load model and process image
    ncnn_model = YOLO(NCNN_MODEL_PATH)
    results = ncnn_model(img, verbose=False)
    
    # Extract Regions of Interest (RoI)
    plates = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            if conf > 0.4:  # Confidence cutoff
                plates.append( img[y1:y2, x1:x2] )  # Save RoI

                if DEBUG_MODE:  # Draw box on image
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.putText(img, f"Plate: {conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if DEBUG_MODE:  # Save plate locations
        os.makedirs(RESULTS_FOLDER, exist_ok=True)
        cv2.imwrite(f"{RESULTS_FOLDER}/found_plates_yolo.jpg", img)

    return plates

_plate_count = 0
def process_plate_image(img):
    """
    Preprocess cropped license plate:
    1. Crop horizontal outer margins (15% | removes 'NEW ZEALAND' logos on side badges).
    2. Resize up for better OCR resolution.
    3. Grayscale + CLAHE for contrast improvement across dark & light plates.
    """
    global _plate_count
    h, w = img.shape[:2]

    # Crop off outer 15% left & right sides to ignore side badges/logos
    margin_x = int(w * 0.15)
    cropped = img[:, margin_x:w - margin_x]

    # Convert to grayscale
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    # Invert image if background is dark (mean pixel intensity < 128)
    if np.mean(gray) < 128:
        gray = cv2.bitwise_not(gray)

    # Resize to standard OCR height (~120px) using CUBIC interpolation
    target_h = 120
    aspect_ratio = cropped.shape[1] / cropped.shape[0]
    target_w = int(target_h * aspect_ratio)
    resized = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    # Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(resized)

    if DEBUG_MODE:
        cv2.imwrite(f"{RESULTS_FOLDER}/unprocessed_plate{_plate_count}.jpg", img)
        cv2.imwrite(f"{RESULTS_FOLDER}/processed_plate{_plate_count}.jpg", enhanced)
        _plate_count += 1

    return enhanced

_READER = None
def get_ocr_reader():
    global _READER
    if _READER is None:
        # EasyOCR init prints warnings internally; suppress around creation
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _READER

def read_plates(plate_images):
    CHAR_SET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    reader   = get_ocr_reader()

    number_plates = []
    for plate_img in plate_images:
        processed_img = process_plate_image(plate_img)

        text = reader.readtext(
            processed_img,
            detail=0,
            allowlist=CHAR_SET,
            paragraph=False,
            text_threshold=0.5,  # Lower seed threshold
            low_text=0.2,        # Expand detection mask to capture thin lines
        )

        number_plates.append(" ".join(text).strip())

    return number_plates

def extract_number_plates(frame):
    plates = find_plates(frame)
    return read_plates(plates)
