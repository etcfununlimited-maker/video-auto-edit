import cv2
import numpy as np

img1 = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\thumb_0423.jpg")
img2 = cv2.imread(r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\thumb_0423_noautorotate.jpg")

# In horizontal videos, horizontal edges (like roads, mountains, bus seats, horizons) dominate over vertical edges
def compute_edge_orientation_ratio(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    # Energy of horizontal gradients vs vertical gradients
    horizontal_edges = np.mean(np.abs(sobely))  # horizontal lines have vertical intensity changes
    vertical_edges = np.mean(np.abs(sobelx))    # vertical lines have horizontal intensity changes
    return horizontal_edges, vertical_edges

h1, v1 = compute_edge_orientation_ratio(img1)
h2, v2 = compute_edge_orientation_ratio(img2)

print(f"thumb_0423 (1080x1920 vertical): horizontal_edge={h1:.2f}, vertical_edge={v1:.2f}, H/V ratio={h1/v1:.2f}")
print(f"thumb_0423_noautorotate (1920x1080 horizontal): horizontal_edge={h2:.2f}, vertical_edge={v2:.2f}, H/V ratio={h2/v2:.2f}")
