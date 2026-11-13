import cv2
import numpy as np

img = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\movie_frame_3m20s.jpg")
h, w = img.shape[:2]

# Let's check face detector using YuNet if available or check edges/brightness
print("Image dimensions:", w, "x", h)

# Let's also check if face exists in rotated orientations:
# Let's save the 4 orientations so we can inspect:
cv2.imwrite(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\rot_0.jpg", img)
cv2.imwrite(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\rot_90.jpg", cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))
cv2.imwrite(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\rot_270.jpg", cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE))
print("Saved rot_0, rot_90, rot_270")
