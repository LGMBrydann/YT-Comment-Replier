import os

# Set the folder path to where you think your files are
folder_path = "/home/itslgmbrydan/YT Bot"

# Files to check
files_to_check = ["client_secret.json", "youtube-bot.py"]

print(f"Checking files in folder: {folder_path}\n")

try:
    # List all files in the folder
    files_in_folder = os.listdir(folder_path)
    print(f"Files found in folder:\n{files_in_folder}\n")
except FileNotFoundError:
    print(f"Folder not found: {folder_path}")
    exit(1)

# Check if each file exists
for filename in files_to_check:
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path):
        print(f"✅ Found file: {filename}")
    else:
        print(f"❌ Missing file: {filename}")

