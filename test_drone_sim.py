import subprocess
from pathlib import Path
from backend.config import FFMPEG_PATH, RAW_INPUT_DIR, UPLOADS_DIR

# Pick a scenic clip: e.g. IMG_0419.MOV (2.5s) or IMG_0433.MOV (3.0s)
scenic_src = str(RAW_INPUT_DIR / "IMG_0433.MOV")
drone_out = str(UPLOADS_DIR / "test_drone_flight.mp4")

# Cinematic Drone Fly-Through Filter:
# Starts at 1.05x scale, smoothly pushes in to 1.25x scale while drifting slowly up-right,
# simulating an aerial drone fly-through over the scenery.
vf_drone = (
    "scale=1920:1080:force_original_aspect_ratio=increase,"
    "crop=1920:1080,"
    "zoompan=z='min(zoom+0.0018,1.25)':x='iw/2-(iw/zoom/2)+sin(in/20)*30':y='ih/2-(ih/zoom/2)-in*0.4':d=90:s=1920x1080:fps=30,"
    "format=yuv420p"
)

cmd = [
    FFMPEG_PATH,
    "-y",
    "-i", scenic_src,
    "-vf", vf_drone,
    "-c:v", "libx264",
    "-preset", "faster",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    drone_out
]

print("Rendering test drone shot...")
subprocess.run(cmd, check=True)
print(f"Drone test shot rendered: {drone_out}")
