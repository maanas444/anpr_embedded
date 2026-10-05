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

def find_plate_by_contours(image_path, output_path='output_contours.jpg'):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blurred, 30, 200)
    
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    plate_contour = None
    for c in contours:
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            if 2.0 <= aspect_ratio <= 5.5:
                plate_contour = approx
                break

    if plate_contour is not None:
        cv2.drawContours(img, [plate_contour], -1, (0, 255, 0), 3)
        # Save to disk instead of window popup
        cv2.imwrite(output_path, img)
        print(f"Success! OpenCV output saved to: {output_path}")
    else:
        print("No rectangular plate detected using traditional contours.")

def find_plate_by_yolo(image_path, output_path='output_yolo.jpg'):
    # Load model
    model = YOLO('yolov8n.pt') 
    
    # Run prediction and leverage built-in saving feature
    # 'save=True' automatically drops a boxed image into a runs/ directory
    results = model(image_path, save=True)
    
    # Alternatively, manually save to a specific filename:
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
                cv2.imwrite('cropped_plate.jpg', cropped_plate)

    cv2.imwrite(output_path, img)
    print(f"Success! Custom YOLO rendering saved to: {output_path}")

def extract_license_plates(frame):
    # PSM 7 = Single line of text
    # With the addition of a character whitelist
    OCR_CONFIG = r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    processed_image = _preprocess_plate(frame)

    try:
        text = pytesseract.image_to_string(processed_image, config=OCR_CONFIG)
        return text.strip()
    except TesseractNotFoundError:
        print(f"[ERROR] Tesseract is not installed (or not added to system PATH)!\n        Run 'install-ocr' to install!")
        import sys
        sys.exit(1)
