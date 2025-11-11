import os
import sys

import zipfile

path = ""
analyst_path = "analyst.zip"
developer_path = "developer.zip"

def unzipper(path):
    if path == "":
        path = analyst_path

    with zipfile.ZipFile(path, 'r') as zip_ana:
        zip_ana.extractall("raw")

unzipper(developer_path)

if __name__ == "__main__":
    input_path = sys.argv[0]

    if (os.path.exists(path)):
        unzipper(path)
    else:
        print("path does not exist: ", path)