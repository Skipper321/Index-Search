from file_items import FileItem
from tokenizer import tokenize_html  # use the new HTML tokenizer
import os
import json

BATCH_SIZE = 2000 # partial index every 2000 documents
RAW_DIR = "raw/DEV"

# Write partial index to disk 
def write_partial_index(index, batch):
    path = f"index_part_{batch}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f)
    print(f"[INFO] Wrote partial index: {path} ({len(index)} tokens)")

# Merge all partial index json files into one final index 
def merge_indexes():
    final_index = {}

    parts = [f for f in os.listdir() if f.startswith("index_part_")]
    parts.sort()

    print("[INFO] Merging partial indexes...")

    for p in parts: 
        with open(p, "r", encoding="utf-8") as f:
            chunk = json.load(f)

        for token, postings in chunk.items():
            if token not in final_index:
                final_index[token] = postings
            else:
                final_index[token].extend(postings)

    # sorting postings by doc_id for neatness
    for tok in final_index:
        final_index[tok].sort(key=lambda x: x[0])

    return final_index


def inverted_index():
    index = {}            # term -> list of (doc_id, freq)
    doc_ids = {}          # doc_id -> URL
    doc_id = 0
    
    batch_number = 0
    processed_docs = 0

    # Walk through all subdirectories and JSON files
    for root, _, files in os.walk(RAW_DIR):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            file_path = os.path.join(root, file_name)
            file_item = FileItem(file_path)
            token_freqs = file_item.parse_contents()

            # Skip if invalid or empty
            if not isinstance(token_freqs, dict) or len(token_freqs) == 0:
                continue

            # Assign doc ID
            doc_ids[doc_id] = file_item.url
            processed_docs += 1

            # Build inverted index - using list for easy JSON
            for token, freq in token_freqs.items():
                if token not in index:
                    index[token] = []
                index[token].append((doc_id, freq))

            doc_id += 1

            # batch flush
            if processed_docs % BATCH_SIZE == 0: 
                write_partial_index(index, batch_number)
                index.clear()
                batch_number += 1

                print(f"[INFO] Processed {processed_docs} documents...")

    # write final partial
    write_partial_index(index, batch_number)

    # write doc-id map
    with open("doc_ids.json", "w", encoding="utf-8") as f:
        json.dump(doc_ids, f)
    
    print("[INFO] ALL partial indexes written.")
    print("[INFO] Merging into final index...")

    final_index = merge_indexes()

    # write final index
    with open("final_index.json", "w", encoding="utf-8") as f:
        json.dump(final_index, f)

    print("[INFO] Final index written.")

    return processed_docs, len(final_index)

if __name__ == "__main__":
    num_docs, unique_tokens = inverted_index()

    print("\n===== INDEX STATISTICS =====")
    print(f"Indexed {num_docs} documents.")
    print(f"Unique tokens: {unique_tokens}")

    size_kb = os.path.getsize("final_index.json") / 1024
    print(f"Index size on disk: {size_kb:.2f} KB")

