from file_items import FileItem
from tokenizer import tokenize_html  # use the new HTML tokenizer
import os, json, struct, csv
import math # support cosine normalization - account for TF-IDF flaws with longer documents
from simhash_item import sh_item, sh_set

BATCH_SIZE = 2000 # partial index every 2000 documents
RAW_DIR = "raw/DEV"

def write_partial_index(index: int, batch):
    """Write partial index to disk

    :index: index of partial 
    :batch: current batch
    """

    path = f"index_part_{batch}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f)
    print(f"[INFO] Wrote partial index: {path} ({len(index)} tokens)")

def merge_indexes() -> dict:
    """Merge all partial index json files into one final index 

    Returns final index dict"""
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
    """Creates an inverted index"""

    index = {}            # term -> list of (doc_id, freq)
    doc_ids = {}          # doc_id -> URL
    doc_id = 0
    simhash_set = sh_set() # see simhash_item.py
    skips = 0 # keeps track of number of skips
    
    batch_number = 0
    processed_docs = 0

    # Walk through all subdirectories and JSON files
    for root, _, files in os.walk(RAW_DIR):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            file_path = os.path.join(root, file_name)
            file_item = FileItem(file_path)
            
            parsed = file_item.parse_contents() # returns dict: "tf": {...}

            # Skip if invalid or empty
            if not isinstance(parsed, dict) or "tf" not in parsed or "positions" not in parsed:
                continue

            tf_dict = parsed["tf"]
            pos_dict = parsed["positions"]
            simhash_val = parsed["simhash"]

            current_sh = sh_item(simhash_val)
            if (simhash_set.add(current_sh) == False):
                skips += 1
                # Skips if too similar
                # print(file_name, " is too similar")
                continue

            if len(tf_dict) == 0:
                continue

            # Assign doc ID
            doc_ids[doc_id] = file_item.url
            processed_docs += 1

            # Build inverted index - using list for easy JSON
            for token in tf_dict:
                tf = tf_dict[token]
                positions = [p for (p, w) in pos_dict[token]]

                if token not in index:
                    index[token] = []
                
                # Postings entry ex: ((doc_id, tf, position))
                index[token].append((doc_id, tf, positions))

            doc_id += 1

            # batch flush if limit reached 
            if processed_docs % BATCH_SIZE == 0: 
                write_partial_index(index, batch_number)
                index.clear()
                batch_number += 1

                print(f"[INFO] Processed {processed_docs} documents...")
                print(f"[INFO] {skips} files skipped during this batch, due to similarity detection with a threshold of {sh_set.threshold()}")
                skips = 0

    # write final partial
    write_partial_index(index, batch_number)

    # write doc-id map
    with open("doc_ids.json", "w", encoding="utf-8") as f:
        json.dump(doc_ids, f)
    
    print("[INFO] ALL partial indexes written.")
    print("[INFO] Merging into final index...")

    final_index = merge_indexes()


    # Compute Cosine Normalization 
    print("[INFO] Compute document cosine normalization...")

    doc_norms = {int(doc_id): 0.0 for doc_id in doc_ids}

    for term, postings in final_index.items():
        for (doc_id, tf, pos_list) in postings:
            w_tf = 1 + math.log(max(tf, 1e-6)) # Log-weighted term frequency
            doc_norms[doc_id] += (w_tf * w_tf) # accumulate squared weights
    
    # Finalize normalizations 
    for doc_id in doc_norms:
        doc_norms[doc_id] = math.sqrt(doc_norms[doc_id])

    # Save to disk
    with open("index/doc_norms.json", "w", encoding="utf-8") as f:
        json.dump(doc_norms, f)

    # write final index 
    with open("final_index.json", "w", encoding="utf-8") as f:
        json.dump(final_index, f)

    print("[INFO] Final index written with cosine normalization.")

    # ---------------------------------------------------------
    # WRITE BINARY INDEX FOR SEARCH (Developer Route requirement)
    # ---------------------------------------------------------
    print("[INFO] Writing binary postings...")

    os.makedirs("index", exist_ok=True)

    postings_path = "index/postings.bin"
    dict_rows = []
    offset = 0

    # 1) Write postings.bin
    with open(postings_path, "wb") as pbin:
        for term in sorted(final_index.keys()):
            plist = final_index[term]   # list[(doc_id, tf, positions)]
            df = len(plist)
            start = offset

            for (doc_id, tf, positions) in plist:
                pbin.write(struct.pack("<if", doc_id, tf))  # int32, float32
                offset += 8

                # number of positions
                pbin.write(struct.pack("<i", len(positions)))
                offset += 4

                # positions themselves
                for p in positions:
                    pbin.write(struct.pack("<i", p))
                    offset += 4

            length = offset - start
            dict_rows.append((term, df, start, length))

    # 2) Write dictionary.csv
    with open("index/dictionary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["term", "df", "offset", "length"])
        w.writerows(dict_rows)

    # 3) Write doc_ids.json (already created above)
    # rewrite or leave as-is

    # 4) Write corpus size meta
    with open("index/corpus_meta.json", "w", encoding="utf-8") as f:
        json.dump({"N": len(doc_ids)}, f)

    print("[INFO] Binary postings index written successfully.")

    return processed_docs, len(final_index)


if __name__ == "__main__":

    num_docs, unique_tokens = inverted_index()

    print("\n===== INDEX STATISTICS =====")
    print(f"Indexed {num_docs} documents.")
    print(f"Unique tokens: {unique_tokens}")

    size_kb = os.path.getsize("final_index.json") / 1024
    print(f"Index size on disk: {size_kb:.2f} KB")
