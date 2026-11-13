import cv2

# Check if FaceDetectorYN or human face is upright in thumb_0423_noautorotate vs thumb_0423
img_rot = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\thumb_0423.jpg")
img_norot = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\thumb_0423_noautorotate.jpg")

print("thumb_0423 shape:", img_rot.shape if img_rot is not None else None)
print("thumb_0423_noautorotate shape:", img_norot.shape if img_norot is not None else None)
