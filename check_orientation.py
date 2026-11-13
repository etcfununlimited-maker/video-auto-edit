import cv2
import numpy as np

cap = cv2.VideoCapture(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\raw_input\IMG_E0418.MOV")
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

# Sample frames at 100s, 110s, 118s, 125s, 140s
timestamps = [50.0, 100.0, 115.0, 118.0, 122.0, 130.0, 150.0]

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

for t in timestamps:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ret, frame = cap.read()
    if not ret or frame is None:
        continue
    h, w = frame.shape[:2]

    # Test 4 rotations: 0, 90 CW, 180, 270 CW
    rotations = {
        0: frame,
        90: cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE),
        180: cv2.rotate(frame, cv2.ROTATE_180),
        270: cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    }

    best_rot = 0
    max_faces = 0
    face_details = []

    for deg, img in rotations.items():
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 3, minSize=(40, 40))
        if len(faces) > max_faces:
            max_faces = len(faces)
            best_rot = deg

    print(f"Time {t:5.1f}s | Frame Res: {w}x{h} | Upright Face Detection: {max_faces} faces at rotation {best_rot}°")

cap.release()
