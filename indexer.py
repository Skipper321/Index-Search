from file_items import FileItem
from tokenizer import tokenize_html  # use the new HTML tokenizer
import os
import json

def read_zip_contents():
    # Returns the path to the folder containing extracted JSON files.
    return "raw/DEV"  


def inverted_index():
    index = {}            # term -> list of (doc_id, freq)
    doc_ids = {}          # doc_id -> URL
    doc_id_key = 0
    num_indexed = 0
    unique_tokens = 0

    folder_path = read_zip_contents()

    # Walk through all subdirectories and JSON files
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            file_path = os.path.join(root, file_name)
            file_item = FileItem(file_path)

            # Skip if invalid or empty
            if not file_item.content.strip():
                continue

            num_indexed += 1
            doc_id = doc_id_key
            doc_ids[doc_id] = file_item.url
            doc_id_key += 1

            # Tokenize + weight + stem using tokenizer.py
            token_freqs = file_item.parse_contents()

            # Build inverted index
            for token, freq in token_freqs.items():
                if token not in index:
                    index[token] = []
                    unique_tokens += 1
                index[token].append((doc_id, freq))

    # Write to disk
    os.makedirs("index", exist_ok=True)
    with open("index/inverted_index.txt", "w", encoding="utf-8") as f:
        for token, postings in index.items():
            f.write(f"{token}: {postings}\n")

    # Save doc mapping for future search use
    with open("index/doc_ids.json", "w", encoding="utf-8") as f:
        json.dump(doc_ids, f)

    print(f"Indexed {num_indexed} documents.")
    print(f"Unique tokens: {unique_tokens}")
    print(f"Index written to index/inverted_index.txt")

    return index

def get_index_size():
    # Sum of all the files in the index folder
    total_size = 0
    index_folder = "index"

    for file_name in os.listdir(index_folder):
        file_path = os.path.join(index_folder, file_name)
        if os.path.isfile(file_path):
            total_size += os.path.getsize(file_path)  # size in bytes
    total_size_kb = total_size / 1024 # convert bytes to KB
    print(f"Total size of index on disk: {total_size_kb:.2f} KB") 
    return total_size_kb


if __name__ == "__main__":
    inverted_index()
    get_index_size()
