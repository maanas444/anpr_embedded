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

def process_plate_image(img):
    return img

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
            low_text=0.3
        )

        number_plates.append("".join(text).strip())

    return number_plates

def extract_number_plates(frame):
    plates = find_plates(frame)
    return read_plates(plates)
