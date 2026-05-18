from PIL import Image
import os

base_dir = r"C:\Users\benmazari_s\.gemini\antigravity\brain\cfbf3589-b092-49bc-bc96-5d76729585f9"
for fname in ["media__1779028980270.png", "media__1779028983539.png"]:
    path = os.path.join(base_dir, fname)
    try:
        im = Image.open(path)
        print(f"File: {fname}, Size: {im.size}, Mode: {im.mode}")
    except Exception as e:
        print(f"Error opening {path}: {e}")
