import cv2
import numpy as np

img = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\movie_frame_3m20s.jpg")
print("Shape of 3m20s frame:", img.shape)

# Let's check average color, black bars, etc.
# Check left and right 200 pixels vs center
left_bar = img[:, :300]
right_bar = img[:, -300:]
center = img[:, 300:-300]

print("Left bar mean brightness:", np.mean(left_bar))
print("Right bar mean brightness:", np.mean(right_bar))
print("Center mean brightness:", np.mean(center))
