import cv2
import os

cap = cv2.VideoCapture(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\final_export\MASTER_FULL_FEATURE_MOVIE.mp4")
out_dir = r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads"

pts = [
    (120.0, "2m00s"),
    (200.0, "3m20s"),
    (220.0, "3m40s"),
    (259.0, "4m19s"),
    (322.0, "5m22s"),
    (400.0, "6m40s"),
    (500.0, "8m20s"),
    (650.0, "10m50s"),
    (760.0, "12m40s"),
    (1550.0, "25m50s")
]

for sec, label in pts:
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
    ret, frame = cap.read()
    if ret and frame is not None:
        p = os.path.join(out_dir, f"movie_frame_{label}.jpg")
        cv2.imwrite(p, frame)
        h, w = frame.shape[:2]
        print(f"Movie Frame at {label} ({sec}s): {w}x{h} -> {p}")

cap.release()
