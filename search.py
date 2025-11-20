import json, csv, math, struct, heapq
import os.path
import tokenizer
from collections import defaultdict
# cannot import this! let the indexer write the files then search reads these files only
# import indexer


class SearchEngine:

    def __init__(self):
        # Load dictionary into memory (small)
        with open("index/dictionary.csv", "r", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            self.dictionary = {
                row["term"]: (int(row["df"]), int(row["offset"]), int(row["length"]))
                for row in rdr
            }
        
        with open("doc_ids.json", "r", encoding="utf-8") as f:
            self.doc_ids = json.load(f) # keys are strings

        with open("index/corpus_meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.N = int(meta["N"])

        self.postings_path = "index/postings.bin"

        print(f"[INFO] Loaded dictionary with {len(self.dictionary)} terms.")
        print(f"[INFO] Ready to search {self.N} documents.")


    def read_postings(self, term):
        info = self.dictionary.get(term)
        if not info:
            return []
        
        df, offset, length = info

        postings = []
        with open(self.postings_path, "rb") as f:
            f.seek(offset)
            block = f.read(length)

        # Decode each (doc_id:int32, tf:float32)
        for i in range(0, length, 8):
            doc_id, tf = struct.unpack_from("<if", block, i)
            postings.append((doc_id, tf))

        return postings
    
    # TF-IDF weighting
    def idf(self, df):
        return math.log((self.N + 1) / (df + 0.5)) + 1.0


    # Searches for one term at a time
    # Takes tokenized search query
    # Returns positional indices for each search as a dictionary
    def searchOne(self, term):
        term = tokenizer.tokenize(term)
        if len(term) == 0:
            return {}
        
        t = term[0] # tokenize returns a list 
        if t not in self.dictionary:
            print(f"[INFO] '{t}' not found.")
            return {}
        
        df, offset, length = self.dictionary[t]
        postings = self.read_postings(t)

        docid_weight = {doc_id: tf for doc_id, tf in postings}
        print(f"[INFO] searchOne('{term}') yielded >>> {len(docid_weight)} results")
        return docid_weight

    # Searches for multiple terms with TF-IDF scoring
    def searchFor(self, query, top_k=10):
        q_terms = tokenizer.tokenize(query)
        if not q_terms:
            return []
        
        scores = defaultdict(float)

        for t in q_terms:
            if t not in self.dictionary:
                continue

            df, _, _ = self.dictionary[t]
            idf_weight = self.idf(df)

            postings = self.read_postings(t)
            for doc_id, tf in postings:
                tfw = 1 + math.log(max(tf,1e-6))
                scores[doc_id] += tfw * idf_weight

        if not scores:
            return []
        
        # top-k 
        top = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])

        # convert doc_id >>> url 
        results = [(self.doc_ids[str(doc)], score) for doc, score in top]
        return results

    def printResults(self, results):
        if not results:
            return 
        
        for i, (url, score) in enumerate(results, start=1):
            print(f"{i}.{url} (score={score:.4f})")
    
    # Boolean helper function to parse and identify the boolean type
    def parse_query_boolean(self, q):
        tokens = q.upper().split()

        if "AND" in tokens:
            op = "AND"
        elif "OR" in tokens:
            op = "OR"
        elif "NOT" in tokens:
            op = "NOT"
        else:
            op = "NONE"
        
        return op
    
    # Boolean operators configured to work with documents
    def boolean_and(self, left, right):
        # left / right are lists of [url, score]
        left_dict = {url:score for url, score in left}
        right_dict = {url:score for url, score in right}
        common = left_dict.keys() & right_dict.keys()
        return [(u, left_dict[u] + right_dict[u]) for u in common]

    def boolean_or(self, left, right):
        combined = {}
        for url, score in left:
            combined[url] = max(score, combined.get(url, 0))
        for url, score in right:
            combined[url] = max(score, combined.get(url, 0))
        return [(u, combined[u]) for u in combined]

    def boolean_not(self, left, right):
        right_urls = {u for u, _ in right}
        return [(u, score) for u, score in left if u not in right_urls]
    


if __name__ == "__main__":
    # Testings sample queries 
    engine = SearchEngine()
    
    print("Simple Boolean Query Search Engine - Developer:")
    print("Supports boolean operations 'AND', 'OR', 'NOT'")
    print("Input a search term, or type '/quit' to exit.")

    while True:
        query = input("Search > ").strip()

        # Quit statement 
        if query.lower() == "/quit":
            break

        print(query)
        
        op = engine.parse_query_boolean(query)
        
        if op is not None and op == "AND":
            left, right = [s.strip() for s in query.upper().split("AND")]
            results = engine.boolean_and(engine.searchFor(left), engine.searchFor(right))
        elif op == "OR":
            left, right = [s.strip() for s in query.upper().split("OR")]
            results = engine.boolean_or(engine.searchFor(left), engine.searchFor(right))
        elif op == "NOT":
            left, right = [s.strip() for s in query.upper().split("NOT")]
            results = engine.boolean_not(engine.searchFor(left), engine.searchFor(right))
        elif op == "NONE":
            results = engine.searchFor(query)
    
        engine.printResults(results)

    #print("--- Sample Queries ---")
    #for q in ["machine learning", "cristina lopes", "ACM", "undergraduate research", "Masters of software engineering"]:
        #print("\nQuery:", q)
    