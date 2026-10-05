import numpy as np
import cv2

def test():
    # Hook video capture
    cap = cv2.VideoCapture(0)  # /dev/video0

    # Read frame
    ret, frame = cap.read()
        
    if ret:
        cv2.imwrite("../captured_image.jpg", frame)

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
