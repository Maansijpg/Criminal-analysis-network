import sys
from pathlib import Path
from PIL import Image, ImageOps

folder = Path(sys.argv[1])
for photo in list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png")):
    img = Image.open(photo)
    fixed = ImageOps.exif_transpose(img)
    fixed.save(photo)
    print(f"Fixed: {photo.name}")