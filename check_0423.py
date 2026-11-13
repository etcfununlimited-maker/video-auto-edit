import subprocess
import json
from backend.config import FFMPEG_PATH

cmd = [
    FFMPEG_PATH,
    "-i", r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\raw_input\IMG_0423.MOV",
    "-vf", "thumbnail=100",
    "-frames:v", "1",
    "-y", r"C:\Users\bhupp\OneDrive\Desktop\ANIRBAN AUTOMATIONS\AUTO EDIT MOVIE\uploads\thumb_0423.jpg"
]
subprocess.run(cmd, check=True)
print("Saved thumb_0423.jpg")
