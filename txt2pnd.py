import os, sys
from pathlib import Path
import numpy as np
import cv2
import concurrent.futures

#for loading xTal image.txt 
sys.path.append('/user/devsalt/USER/CNR/3.SQA/SCRIPTS')
from mycal import readXtalImage

np.seterr(divide='ignore', invalid='ignore')

# Initialize paths
pwd = os.getcwd()
root = Path(pwd)
result = root / 'result'

pngs = root / 'pngs'
pngs.mkdir(exist_ok=True)
mi_pngs = pngs / 'mi_pngs'
mi_pngs.mkdir(exist_ok=True)
ai_pngs = pngs / 'ai_pngs'
ai_pngs.mkdir(exist_ok=True)
ri_pngs = pngs / 'ri_pngs'
ri_pngs.mkdir(exist_ok=True)

mi_txt_list = sorted((root / 'mi').glob('*.txt'))
ai_txt_list = sorted((root / 'ai').glob('*.txt'))
ri_txt_list = sorted((root / 'ri').glob('*.txt'))

# Function to process and save images
def process_and_save_image(txt_path, save_dir, prefix):
    try:
        # Read image data
        img_data = readXtalImage(txt_path)[2]
        
        # Save as text file
        txt_save_path = save_dir / f"{txt_path.stem}.txt"
        np.savetxt(txt_save_path, img_data)

        # Normalize and save as PNG
        img_data = (img_data * 255).astype(np.uint8)
        png_save_path = save_dir / f"{txt_path.stem}.png"
        cv2.imwrite(str(png_save_path), img_data)
    except Exception as e:
        print(f"Error processing {prefix} file {txt_path}: {e}")

# Multithreading function
def process_files_in_parallel(file_list, save_dir, prefix):
    max_threads = os.cpu_count()  # Get the maximum number of threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(process_and_save_image, txt_path, save_dir, prefix)
            for txt_path in file_list
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Raise exceptions if any

# Process AI, MI, and RI files in parallel
if __name__ == "__main__":
    process_files_in_parallel(mi_txt_list, mi_pngs, "MI")
    process_files_in_parallel(ai_txt_list, ai_pngs, "AI")
    process_files_in_parallel(ri_txt_list, ri_pngs, "RI")

