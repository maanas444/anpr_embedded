import cv2
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError

# Disable Ultralytics online/telemetry checks
import os
os.environ["YOLO_AUTOINSTALL"] = "False"
os.environ["ULTRALYTICS_AUTOINSTALL"] = "False"
from ultralytics import YOLO


# Multi-license plate reading with ROI
# 1. Pre-processing
# 2. Find license plates (rectangles)
# 3. Crop license plates
# 4. Align/Rotate/Warp text
# 5. OCR on plates

def stack_vertically(frames, labels):
    labeled = []
    for img, text in zip(frames, labels):
        # Convert grayscale (2D) to 3-channel BGR (3D) if needed
        f = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
        
        # Top-left corner with larger font scale (1.2) and thicker stroke (3)
        cv2.putText(f, text, (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        labeled.append(f)
        
    return np.vstack(labeled)

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray

def preprocess_plate(img):
    """Cropped plate image (BGR or gray) -> binary image, dark text on light."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise and even out contrast
    bilateral = cv2.bilateralFilter(gray, 13, 15, 15)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(bilateral)

    # Binarize
    _, binary = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Text is the minority colour: make sure it's the dark one
    if np.mean(binary) < 127:
        binary = cv2.bitwise_not(binary)

    # TODO: Remove, for debugging
    cv2.imwrite( "../results/pre-process.jpg",
        stack_vertically(
            [ img,   gray,   bilateral,   clahe,   binary], 
            ["raw", "gray", "bilateral", "CLAHE", "binary"]
        )
    )

    return binary

def find_plate_by_contours(image_path, output_path='../results/output_contours.jpg'):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blurred, 30, 200)
    
    # contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:50]
    
    candidate_contours = []
    boxes = []
    scores = []

    for c in contours:
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        
        # Check if shape is a quadrilateral
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            
            # Filter typical license plate aspect ratios
            if 2.0 <= aspect_ratio <= 5.5:
                candidate_contours.append(approx)
                boxes.append([x, y, w, h])
                scores.append(float(cv2.contourArea(c)))

    # Apply Non-Maximum Suppression to filter out overlapping/nested detections
    detected_plates = []
    if candidate_contours:
        indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.0, nms_threshold=0.3)
        if len(indices) > 0:
            for i in indices.flatten():
                detected_plates.append(candidate_contours[i])

    # Draw and save results
    if detected_plates:
        cv2.drawContours(img, detected_plates, -1, (0, 255, 0), 3)
        cv2.imwrite(output_path, img)
        print(f"Success! Detected {len(detected_plates)} plate(s). Saved to: {output_path}")
    else:
        print("No rectangular plates detected using traditional contours.")

def find_plate_by_yolo(image_path, output_path='../results/output_yolo.jpg'):
    # # 1. Load the model
    # model = YOLO("node/models/license-plate-finetune-v1n.pt")  # Nano  :  5.47 MB
    # # results = model(image_path)

    # # 2. Export to NCNN format (creates a folder named 'yolov11n_ncnn_model')
    # model.export(format="ncnn", verbose=False)

    # # # Quiet down Ultralytics logger
    # # import os
    # # os.environ["YOLO_VERBOSE"] = "False"

    # # # Suppress PyTorch/Python deprecation warnings
    # # import warnings
    # # warnings.filterwarnings("ignore")

    # 3. Load the exported model for sub-100ms inference
    ncnn_model = YOLO("node/models/license-plate-finetune-v1n_ncnn_model")
    results = ncnn_model(image_path)
    
    # Alternatively, manually save to a specific filename:
    i = 0
    img = cv2.imread(image_path)
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            if conf > 0.4:
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(img, f"Plate: {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Optional: Save a separate crop of the plate region
                cropped_plate = img[y1:y2, x1:x2]
                cv2.imwrite(f"../results/cropped_plate_{i}.jpg", cropped_plate)
                i += 1

    cv2.imwrite(output_path, img)
    print(f"Success! Custom YOLO rendering saved to: {output_path}")

def extract_number_plate_text(roi):
    # PSM 7 = Single line of text
    # With the addition of a character whitelist
    OCR_CONFIG = r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    try:
        text = pytesseract.image_to_string(roi, config=OCR_CONFIG)
        return text.strip()
    except TesseractNotFoundError:
        print(f"[ERROR] Tesseract is not installed (or not added to system PATH)!\n        Run 'install-ocr' to install!")
        import sys
        sys.exit(1)

def extract_number_plates(frame):
    
    processed_image = preprocess(frame)

    cv2.imwrite( "../results/pre-processed.jpg", processed_image )
    find_plate_by_contours("../results/pre-processed.jpg")

    file_prefix = "../results/cropped_plate_"
    np0  = f"2"
    np1  = f"3"
    np2  = f"0"
    np3  = f"1"
    img0 = cv2.imread(f"{file_prefix}{np0}.jpg")
    img1 = cv2.imread(f"{file_prefix}{np1}.jpg")
    img2 = cv2.imread(f"{file_prefix}{np2}.jpg")
    img3 = cv2.imread(f"{file_prefix}{np3}.jpg")
    img0 = preprocess_plate(img0)
    img1 = preprocess_plate(img1)
    img2 = preprocess_plate(img2)
    img3 = preprocess_plate(img3)
    np0  = f"pp_{np0}"
    np1  = f"pp_{np1}"
    np2  = f"pp_{np2}"
    np3  = f"pp_{np3}"
    cv2.imwrite(f"{file_prefix}{np0}.jpg", img0)
    cv2.imwrite(f"{file_prefix}{np1}.jpg", img1)
    cv2.imwrite(f"{file_prefix}{np2}.jpg", img2)
    cv2.imwrite(f"{file_prefix}{np3}.jpg", img3)
    print(f"License Plate 0: \"{extract_number_plate_text(f"{file_prefix}{np0}.jpg")}\"")
    print(f"License Plate 1: \"{extract_number_plate_text(f"{file_prefix}{np1}.jpg")}\"")
    print(f"License Plate 2: \"{extract_number_plate_text(f"{file_prefix}{np2}.jpg")}\"")
    print(f"License Plate 3: \"{extract_number_plate_text(f"{file_prefix}{np3}.jpg")}\"")
