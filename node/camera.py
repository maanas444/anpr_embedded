import numpy as np
import cv2

def test():
    cam = Camera()
    frame = cam.read_frame()

    if frame is not None:
        cv2.imwrite("../captured_image.jpg", frame)

class Camera():
    # Constructor (automatically called on creation)
    def __init__(self):
        # Hook video capture
        self.cap = cv2.VideoCapture(0)  # /dev/video0

    # Deconstructor (automatically called on cleanup/deletion)
    def __del__(self):
        self.cap.release()

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None  # No image
        
        return frame
