import os
import sys
from PIL import Image
from pillow_heif import register_heif_opener

# Redirect stdout/stderr to a file to capture output
sys.stdout = open('conversion_log_v2.txt', 'w')
sys.stderr = sys.stdout

print("Starting conversion script...")
register_heif_opener()

files = [
    ("1. Mug Insert Light Grey.heic", "1. Mug Insert Light Grey.jpg"),
    ("2.Mug Insert Dark Grey.heic", "2. Mug Insert Dark Grey.jpg")
]

for input_file, output_file in files:
    if os.path.exists(input_file):
        print(f"Converting {input_file} to {output_file}...")
        try:
            image = Image.open(input_file)
            image.save(output_file, "JPEG")
            print(f"Success: {output_file}")
        except Exception as e:
            print(f"Failed to convert {input_file}: {e}")
    else:
        print(f"File not found: {input_file}")

print("Script finished.")
