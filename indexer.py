from tokenizer import tokenize, computeWordFrequencies
from unzip import unzipper
from file_items import FileItem
import os
import json

def read_zip_contents():
    directory_dict = {}

    unzipper('/Users/alohamylola/Desktop/analyst.zip') # may need to replace path name
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

    for site, file_paths in directory_dict.items():
        for file_path in file_paths:
            file_item = FileItem(file_path)
            num_indexed += 1
            # map document URL to an integer
            doc_id = doc_id_key
            doc_ids[doc_id] = file_item.url
            doc_id_key += 1
            # load JSON content to tokenize
            text = file_item.parse_contents()
            tokens = tokenize(text)
    
            token_freq_dict = computeWordFrequencies(tokens)
            for token, freq in token_freq_dict.items():
                # check for unique tokens
                # increase unique_tokens counter and add token to index
                if token not in index:
                    index[token] = [] # use lists instead of sets to maintain order
                    unique_tokens += 1
                index[token].append((doc_id, freq))
    return index

if __name__ == "__main__":
    index = inverted_index()
    
    with open("inverted_index.txt", "w", encoding="utf-8") as f:
        for token, postings in index.items():
            f.write(f"{token}: {postings}\n")