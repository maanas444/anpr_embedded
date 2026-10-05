import cv2
import numpy as np
import pytesseract
from pytesseract import TesseractNotFoundError


# 1. Pre-processing
# 2. Find license plates (rectangles)
# 3. Crop license plates
# 4. OCR on plates

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
    cv2.imwrite("../processing-v2.jpg", combined)

    return thresh  # Return pre-processed frame

def _preprocess_plate2(frame):
    """Clean, upscale, and pad a cropped license plate image for OCR."""
    # 1. Upscale image to increase character size for Tesseract
    height, width = frame.shape[:2]
    frame_resized = cv2.resize(frame, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)

    # 2. Convert to grayscale
    gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

    # 3. Denoise with Gaussian Blur instead of Bilateral filter
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 4. Use Otsu's thresholding for cleaner separation
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 5. Add a clean white border around the thresholded image
    # Tesseract struggles when text or black regions touch the exact boundary
    padded = cv2.copyMakeBorder(
        thresh,
        top=15,
        bottom=15,
        left=15,
        right=15,
        borderType=cv2.BORDER_CONSTANT,
        value=[255, 255, 255]
    )

    # TODO: Remove, for debugging
    # --- DEBUG VISUALIZATION (Fixed dimensions & channels) ---
    # Convert all images to 3-channel BGR and match the padded width
    target_width = padded.shape[1]
    def prep_for_stack(img):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return cv2.resize(img, (target_width, int(img.shape[0] * (target_width / img.shape[1]))))
    
    combined = cv2.vconcat([
        prep_for_stack(frame_resized),
        prep_for_stack(blurred),
        prep_for_stack(gray),
        prep_for_stack(thresh),
        prep_for_stack(padded)
    ])
    cv2.imwrite("../processing-v3.jpg", combined)

    return padded

def _preprocess_plate3(frame):
    """Clean, upscale, and pad a cropped license plate image for OCR."""
    # 1. Upscale image (Tesseract needs characters ~30-40px high)
    height, width = frame.shape[:2]
    frame_resized = cv2.resize(frame, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)

    # 2. Convert to grayscale & Blur
    gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Otsu Thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4. Remove outer black borders/noise using Morphological Opening
    # This separates black border lines from the black text characters
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # 5. Pad the image AFTER converting to BGR for uniform dimensions in vconcat
    padded = cv2.copyMakeBorder(
        cleaned,
        top=15,
        bottom=15,
        left=15,
        right=15,
        borderType=cv2.BORDER_CONSTANT,
        value=255
    )


    # TODO: Remove, for debugging
    # --- DEBUG VISUALIZATION (Fixed dimensions & channels) ---
    # Convert all images to 3-channel BGR and match the padded width
    target_width = padded.shape[1]
    def prep_for_stack(img):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return cv2.resize(img, (target_width, int(img.shape[0] * (target_width / img.shape[1]))))
    
    combined = cv2.vconcat([
        prep_for_stack(frame_resized),
        prep_for_stack(gray),
        prep_for_stack(thresh),
        prep_for_stack(cleaned),
        prep_for_stack(padded)
    ])
    cv2.imwrite("../processing-v4.jpg", combined)

    return padded

def clean_plate_borders(binary_img):
    """Removes black borders connected to the image boundaries."""
    h, w = binary_img.shape[:2]
    
    # Invert so background is black (0) and text/borders are white (255)
    inv = cv2.bitwise_not(binary_img)
    
    # Create a mask slightly larger than the image for floodFill
    mask = np.zeros((h + 2, w + 2), np.uint8)
    
    # Flood-fill black from all 4 borders to wipe out edge-connected black borders
    for x in range(w):
        if inv[0, x] == 255: cv2.floodFill(inv, mask, (x, 0), 0)
        if inv[h-1, x] == 255: cv2.floodFill(inv, mask, (x, h-1), 0)
    for y in range(h):
        if inv[y, 0] == 255: cv2.floodFill(inv, mask, (0, y), 0)
        if inv[y, w-1] == 255: cv2.floodFill(inv, mask, (w-1, y), 0)
        
    # Invert back to normal black-on-white text
    cleaned = cv2.bitwise_not(inv)
    return cleaned

def _preprocess_plate4(crop):
    # 1. Resize/Upscale crop
    h, w = crop.shape[:2]
    crop_resized = cv2.resize(crop, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale & Threshold
    gray = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 3. Strip outer border frame
    cleaned = clean_plate_borders(thresh)

    # 4. Add fresh white padding around isolated text
    padded = cv2.copyMakeBorder(cleaned, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)

    # TODO: Remove, for debugging
    # --- DEBUG VISUALIZATION ---
    target_width = padded.shape[1]

    def prep_for_stack(img):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return cv2.resize(img, (target_width, int(img.shape[0] * (target_width / img.shape[1]))))

    combined = cv2.vconcat([
        prep_for_stack(crop_resized),
        prep_for_stack(gray),
        prep_for_stack(thresh),
        prep_for_stack(cleaned),
        prep_for_stack(padded)
    ])
    cv2.imwrite("../processing-v5.jpg", combined)

    return padded

def extract_license_plates(frame):
    # PSM 7 = Single line of text
    # With the addition of a character whitelist
    OCR_CONFIG = r"--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    # processed_image = _preprocess_plate(frame)
    # processed_image = _preprocess_plate2(frame)
    # processed_image = _preprocess_plate3(frame)
    processed_image = _preprocess_plate4(frame)

    try:
        text = pytesseract.image_to_string(processed_image, config=OCR_CONFIG)
        return text.strip()
    except TesseractNotFoundError:
        print(f"[ERROR] Tesseract is not installed (or not added to system PATH)!\n        Run 'install-ocr' to install!")
        import sys
        sys.exit(1)
