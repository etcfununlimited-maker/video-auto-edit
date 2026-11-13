import cv2
import os

cap = cv2.VideoCapture(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\raw_input\IMG_E0418.MOV")
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

out_dir = r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads"
for t in [30.0, 100.0, 118.0, 122.0, 135.0]:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ret, frame = cap.read()
    if ret and frame is not None:
        p = os.path.join(out_dir, f"frame_0418_{int(t)}s.jpg")
        cv2.imwrite(p, frame)
        h, w = frame.shape[:2]
        print(f"Saved frame at {t}s: {w}x{h} -> {p}")

cap.release()
