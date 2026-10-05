import cv2
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError
from ultralytics import YOLO


# Multi-license plate reading with ROI
# 1. Pre-processing
# 2. Find license plates (rectangles)
# 3. Crop license plates
# 4. Align/Rotate/Warp text
# 5. OCR on plates

def preprocess_plate(img, height=80):
    """Cropped plate image (BGR or gray) -> binary image, dark text on light."""
    gray = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
 
    # Normalise size
    scale = height / gray.shape[0]
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
 
    # Denoise and even out contrast
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
 
    # Binarize
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
 
    # Text is the minority colour: make sure it's the dark one
    if np.mean(binary) < 127:
        binary = cv2.bitwise_not(binary)
 
    return binary

def find_plate_by_contours(image_path, output_path='../results/output_contours.jpg'):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blurred, 30, 200)
    
    # contours, _ = cv2.findContours(edged.copy(), cv2.RETRE_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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

def extract_license_plates(frame):
    # PSM 7 = Single line of text
    # With the addition of a character whitelist
    OCR_CONFIG = r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    processed_image = preprocess_plate(frame)
    find_plate_by_contours(processed_image)

    try:
        text = pytesseract.image_to_string(processed_image, config=OCR_CONFIG)
        return text.strip()
    except TesseractNotFoundError:
        print(f"[ERROR] Tesseract is not installed (or not added to system PATH)!\n        Run 'install-ocr' to install!")
        import sys
        sys.exit(1)
