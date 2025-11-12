from tokenizer import tokenize
from unzip import unzipper
import os
import json

def read_zip_contents():
    directory_dict = {}

    unzipper('path_name') # may need to replace path name
    base_folder = "raw"

    for root, dirs, files in os.walk(base_folder):
        if root == base_folder:
            continue

        site_name = os.path.basename(root)
        directory_dict[site_name] = []

        for file_name in files:
            if file_name.endswith('.json'):
                directory_dict[site_name].append(os.path.join(root, file_name)) # store paths to json file
        
    return directory_dict

def inverted_index():
    index = {} 
    doc_ids = {} # map integer number to site URL
    doc_id_key = 0 
    unique_tokens = 0 
    num_indexed = 0 # number of indexed documents

    directory_dict = read_zip_contents()
    #  print(directory_dict)

if __name__ == "__main__":
    inverted_index()