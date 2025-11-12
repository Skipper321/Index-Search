import os
import sys

import zipfile

path = ""
developer_path = "developer.zip"

def unzipper(path):
    with zipfile.ZipFile(path, 'r') as zip_ana:
        zip_ana.extractall("raw")
        print(f"Extracted '{path}' into 'raw/'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "developer.zip"  # default fallback

    if os.path.exists(path):
        unzipper(path)
    else:
        print("path does not exist:", path)