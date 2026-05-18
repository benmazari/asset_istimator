from PIL import Image
import os

base_dir = r"C:\Users\benmazari_s\Delta\.." # We know the folder is:
base_dir = r"C:\Users\benmazari_s\.gemini\antigravity\brain\cfbf3589-b092-49bc-bc96-5d76729585f9"
img_path = os.path.join(base_dir, "media__1779028980270.png")

try:
    im = Image.open(img_path)
    # Crop the area of interest: Mobiliers de Bureaux row gap column
    # Let's crop the bottom right section where 'Mobiliers de Bureaux' row is.
    # Width is 1024, height is 216.
    # Mobiliers de Bureaux is the 5th row, so it's near the bottom (height ~ 160-200).
    # Gap column is around the middle-right.
    # Let's crop the entire bottom region and print a ASCII representation or save it as a smaller file.
    w, h = im.size
    crop_area = im.crop((int(w * 0.65), int(h * 0.75), int(w * 0.85), int(h * 0.95)))
    crop_area.save(os.path.join(base_dir, "crop_gap.png"))
    print("Crop saved successfully!")
except Exception as e:
    print(f"Error: {e}")
