import cv2
import numpy as np

img = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\frame_0418_118s.jpg")
print("Shape of frame_0418_118s:", img.shape)
left_bar = img[:, :300]
right_bar = img[:, -300:]
center = img[:, 300:-300]
print("Left bar mean brightness:", np.mean(left_bar))
print("Right bar mean brightness:", np.mean(right_bar))
print("Center mean brightness:", np.mean(center))
