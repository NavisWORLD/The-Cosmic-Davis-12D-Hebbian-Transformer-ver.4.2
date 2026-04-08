import os
import glob
import zipfile
import shutil

base_dir = r"d:\Cosmos"
analysis_dir = os.path.join(base_dir, "quantum_analysis")

os.makedirs(analysis_dir, exist_ok=True)

# Unzip all workloads (*).zip
zip_files = glob.glob(os.path.join(base_dir, "workloads (*).zip"))
for zf in zip_files:
    basename = os.path.basename(zf).replace(".zip", "")
    dest = os.path.join(analysis_dir, basename)
    if not os.path.exists(dest):
        print(f"Extracting {zf} to {dest}")
        try:
            with zipfile.ZipFile(zf, 'r') as zip_ref:
                zip_ref.extractall(dest)
        except Exception as e:
            print(f"Failed to extract {zf}: {e}")

# Copy directory workloads
dir_files = glob.glob(os.path.join(base_dir, "workloads (*)"))
for df in dir_files:
    if os.path.isdir(df) and "quantum_analysis" not in df:
        basename = os.path.basename(df)
        dest = os.path.join(analysis_dir, basename)
        if not os.path.exists(dest):
            print(f"Copying {df} to {dest}")
            try:
                shutil.copytree(df, dest)
            except Exception as e:
                print(f"Failed to copy {df}: {e}")

# List all files in analysis dir
print("\n--- Files in quantum_analysis ---")
for root, _, files in os.walk(analysis_dir):
    for f in files:
        if f.endswith(".json") or f.endswith(".jsonl"):
            full_path = os.path.join(root, f)
            print(full_path, f"({os.path.getsize(full_path)} bytes)")
