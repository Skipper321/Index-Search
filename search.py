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

        # Load doc norms for cosine normalization 
        with open("index/doc_norms.json", "r", encoding="utf-8") as f:
            self.doc_norms = { int(k): float(v) for k, v in json.load(f).items()}


        self.postings_path = "index/postings.bin"

        print(f"[INFO] Loaded dictionary with {len(self.dictionary)} terms.")
        print(f"[INFO] Ready to search {self.N} documents.")
        print(f"[INFO] Loaded doc normalizations")


    def read_postings(self, term):
        info = self.dictionary.get(term)
        if not info:
            return []
        
        df, offset, length = info

        postings = []
        with open(self.postings_path, "rb") as f:
            f.seek(offset)
            block = f.read(length)

        ptr = 0

        while ptr < length:
            doc_id, tf = struct.unpack_from("<if", block, ptr)
            ptr += 8

            pos_count = struct.unpack_from("<i", block, ptr)[0]
            ptr += 4

            positions = []
            for _ in range(pos_count):
                p = struct.unpack_from("<i", block, ptr)[0]
                positions.append(p)
                ptr += 4
            postings.append((doc_id, tf, positions))

        return postings
    
    # TF-IDF weighting
    def idf(self, df):
        return math.log((self.N + 1) / (df + 0.5)) + 1.0
    
    # Phrase match helper - returns set of doc_ids where EXACT phrase occurs
    def phrase_match(self, termA, termB):
        postA = self.read_postings(termA)
        postB = self.read_postings(termB)

        matches = set()

        dictA = {doc: posA for (doc, _, posA) in postA}
        dictB = {doc: posB for (doc, _, posB) in postB}

        common_docs = dictA.keys() & dictB.keys()

        for d in common_docs:
            positionsA = dictA[d]
            positionsB = set(dictB[d])

            # phrase: B must be immediately after A
            for p in positionsA:
                if (p+1) in positionsB:
                    matches.add(d)
                    break

        return matches

    # Searches for multiple terms with TF-IDF scoring
    def searchFor(self, query, top_k=10):
        q_terms = tokenizer.tokenize(query)
        if not q_terms:
            return []
        
        # Detect phrase search: 2 terms, enclosed with quotes 
        normalized_query = query.strip().lower()
        phrase_mode = (normalized_query.startswith('"') and normalized_query.endswith('"') 
                       and len(q_terms) == 2)
    

        scores = defaultdict(float)

        # Basic TF-IDF accumulation
        postings_cache = {}
        for t in q_terms:
            if t not in self.dictionary:
                continue

            df, _, _ = self.dictionary[t]
            idf_weight = self.idf(df)

            postings = self.read_postings(t)
            postings_cache[t] = postings

            for (doc_id, tf, positions) in postings:
                tfw = 1 + math.log(max(tf,1e-6))
                scores[doc_id] += tfw * idf_weight

        # apply phrase constraint if needed
        if phrase_mode:
            t1, t2 = q_terms
            phrase_docs = self.phrase_match(t1, t2)

            # only keep phrase-matching docs
            scores = {d: scores[d] * 2.0 for d in phrase_docs} # boosting phrase matches

        if not scores:
            return []
        
        # Implemented Cosine Normalization - M3 
        for doc_id in list(scores.keys()):
            scores[doc_id] /= self.doc_norms[doc_id]
        
        # select top-k highest scores 
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
    print("Supports exact phrase searches, use double quotes for the 2 terms: ")
    print("Exact Phrase examples: \"the document\", \"machine learning\"")
    print("Input a search term(s), or type '/quit' to exit.")

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

    