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


DEBUG_MODE = False
RESULTS_FOLDER = "../results"
MODEL_PATH_WITHOUT_EXTENSION = "node/models/license-plate-finetune-v1n"  # Nano : 5.47 MB


def _export_model():
    model = YOLO(f"{MODEL_PATH_WITHOUT_EXTENSION}.pt")
    model.export(format="ncnn")

ncnn_model = None
def load_model():
    global ncnn_model

    NCNN_MODEL_PATH = f"{MODEL_PATH_WITHOUT_EXTENSION}_ncnn_model"

    if not Path(NCNN_MODEL_PATH).exists():
        _export_model()  # Create NCNN (embedded) model

    # Load model and process image
    ncnn_model = YOLO(NCNN_MODEL_PATH)

def _dedupe(dets, contain_thresh=0.7):
    # dets: list of (conf, x1, y1, x2, y2); keep highest-confidence first
    dets = sorted(dets, reverse=True)
    kept = []
    for conf, x1, y1, x2, y2 in dets:
        area = (x2 - x1) * (y2 - y1)
        dup = False
        for _, kx1, ky1, kx2, ky2 in kept:
            iw = max(0, min(x2, kx2) - max(x1, kx1))
            ih = max(0, min(y2, ky2) - max(y1, ky1))
            inter = iw * ih
            smaller = min(area, (kx2 - kx1) * (ky2 - ky1))
            if smaller > 0 and inter / smaller > contain_thresh:
                dup = True
                break
        if not dup:
            kept.append((conf, x1, y1, x2, y2))
    return kept

def find_plates(img):
    global ncnn_model
    if ncnn_model is None:
        return  # Early exit: model not initialised

    results = ncnn_model(img, verbose=False)
    
    # Extract Regions of Interest (RoI)
    dets = []
    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])
            if conf > 0.4:  # Confidence cutoff
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                dets.append((conf, x1, y1, x2, y2))  # Save RoI

    plates = []
    for conf, x1, y1, x2, y2 in _dedupe(dets):
        plates.append( img[y1:y2, x1:x2] )
        
        if DEBUG_MODE:  # Draw box on image
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(img, f"Plate: {conf:.2f}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if DEBUG_MODE:  # Save plate locations
        os.makedirs(RESULTS_FOLDER, exist_ok=True)
        cv2.imwrite(f"{RESULTS_FOLDER}/found_plates_yolo.jpg", img)

    return plates

def _order_points(pts):
    # returns top-left, top-right, bottom-right, bottom-left
    pts = pts.reshape(4, 2).astype("float32")
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)],
                     pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")

def deskew_plate(img):
    """Warp the plate to a flat rectangle. Falls back to the original crop."""
    pad = 15  # YOLO crops are tight, so give the contour room to close
    img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    h, w = img.shape[:2]

    gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # If the plate is the dark region instead, flip (check the border pixels)
    border = np.concatenate([mask[0], mask[-1], mask[:, 0], mask[:, -1]])
    if border.mean() > 127:
        mask = cv2.bitwise_not(mask)

    # Close the gaps left by the letters
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img
    cnt = max(contours, key=cv2.contourArea)
    if cv2.contourArea(cnt) < 0.25 * w * h:
        return img  # didn't find a plate-sized blob

    hull = cv2.convexHull(cnt)
    approx = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True)
    quad = approx if len(approx) == 4 else cv2.boxPoints(cv2.minAreaRect(hull))

    tl, tr, br, bl = _order_points(np.asarray(quad))
    out_w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    out_h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    if out_w < 20 or out_h < 10:
        return img

    dst = np.array([[0, 0], [out_w, 0], [out_w, out_h], [0, out_h]], dtype="float32")
    M = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl], dtype="float32"), dst)
    return cv2.warpPerspective(img, M, (out_w, out_h))

_plate_count = 0
def process_plate_image(img):
    """
    Preprocess cropped license plate:
    1. Deskew
    2. Resize up for better OCR resolution.
    3. Grayscale + CLAHE for contrast improvement across dark & light plates.
    """
    global _plate_count

    # Rotate
    img = deskew_plate(img)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Invert image if background is dark (mean pixel intensity < 128)
    if np.mean(gray) < 128:
        gray = cv2.bitwise_not(gray)

    # Resize to standard OCR height (~120px) using CUBIC interpolation
    target_h = 120
    aspect_ratio = img.shape[1] / img.shape[0]
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
            text_threshold=0.5,
            low_text=0.3,        # Expand detection mask to capture thin lines
            mag_ratio=1.5
        )

        number_plates.append(" ".join(text).strip())

    return number_plates

def extract_number_plates(frame):
    plates = find_plates(frame)
    if DEBUG_MODE:
        print(f"{len(plates)} plates found! reading (ocr)...")

    if len(plates) == 0:
        return None  # Early exit: no plates to read
    return read_plates(plates)
