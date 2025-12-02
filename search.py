import json, csv, math, struct, heapq
import os.path
import tokenizer
import time
from collections import defaultdict
import nltk 
from nltk.corpus import wordnet as wn

#nltk.download("wordnet")
#nltk.download("omw-1.4")



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
    def phrase_match(self, phrase_terms, cache=None):
        if len(phrase_terms) < 2:
            return set()
        
        postings_lists = []
        for t in phrase_terms:
            if cache and t in cache:
                postings_lists.append(cache[t])
            else:
                postings_lists.append(self.read_postings(t))

        postings_dicts = [{doc: set(pos) for doc, _, pos in postings} for postings in postings_lists]

        common_docs = set(postings_dicts[0].keys())
        for d in postings_dicts[1:]:
            common_docs &= d.keys()

        matches = set()
        for doc in common_docs:
            first_positions = postings_dicts[0][doc]
            for start_pos in first_positions:
                match = True
                for i in range(1, len(phrase_terms)):
                    if start_pos + i not in postings_dicts[i][doc]:
                        match = False
                        break
                if match:
                    matches.add(doc)
                    break

        return matches
    
    def expand_synonyms(self, terms, max_synonyms = 3):
        synonym_terms = set()
        
        for t in terms:
            # get wordnet synonoms
            synsets = wn.synsets(t)
            count = 0
            
            for syn in synsets:
                for lemma in syn.lemmas():
                    if count >= max_synonyms: # if more than 3 syn break
                        break
                    word = lemma.name().lower().replace("_", " ")
                    
                    # tokenize and stem synonom
                    tok = tokenizer.tokenize(word)
                    if tok:
                        synonym_terms.add(tok[0])
                        count += 1
                if count >= max_synonyms:
                    break
        
        return synonym_terms
    
    def is_high_df(self, term, threshold=1000):
        if term not in self.dictionary:
            return False
        df, _, _ = self.dictionary[term]
        return df > threshold
            

    # Searches for multiple terms with TF-IDF scoring
    def searchFor(self, query, top_k=10):
        q_terms = tokenizer.tokenize(query)
        
        if not q_terms:
            return []
        
        expanded_terms = []
        
        for t in q_terms:
            # keep original term 
            
            expanded_terms.append(t)
            
            # skip synonom expansion if high DF
            if self.is_high_df(t, threshold=1000):
                print(f"[INFO] Skipping synonym expansion for high-DF term:  {t}")
                continue
            
            # add synonyms for low-df terms 
            syns = self.expand_synonyms([t])
            expanded_terms.extend(syns)

        q_terms = expanded_terms
        # Initialize scores and cache
        scores = defaultdict(float)
        postings_cache = {}
    
        # Read postings once and cache them
        for t in q_terms:
            if t not in self.dictionary:
                continue
            
            # If exact word, use weight 1.0, else use 0.6 for synonom
            if t in q_terms:
                query_weight = 1.0
            else:
                query_weight = 0.6
                
            postings = self.read_postings(t)

            # TF-IDF scoring
            df, _, _ = self.dictionary[t]
            idf_weight = self.idf(df)
            
            for doc_id, tf, positions in postings:
                tfw = 1 + math.log(max(tf, 1e-6))
                scores[doc_id] += tfw * idf_weight

        # Check for phrase search (any number of words in quotes)
        normalized_query = query.strip().lower()
        phrase_mode = normalized_query.startswith('"') and normalized_query.endswith('"')
        if phrase_mode and len(q_terms) >= 2:
            phrase_docs = self.phrase_match(q_terms, postings_cache)
            # Only keep phrase-matching docs
            scores = {d: scores[d] * 2.0 for d in phrase_docs}

        if not scores:
            return []

        # Cosine normalization
        for doc_id in list(scores.keys()):
            scores[doc_id] /= self.doc_norms[doc_id]

        # Top-k results
        top = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])
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
    
    print("\nSimple Boolean Query Search Engine - Developer:")
    print("Supports boolean operations 'AND', 'OR', 'NOT'")
    print("Supports exact phrase searches using double quotes, e.g., \"building software solutions\"")
    print("Exact Phrase examples: \"the document\", \"machine learning\"")
    print("Input a search term(s), or type '/quit' to exit.\n")

    while True:
        query = input("Search > ").strip()

        # Quit statement 
        if query.lower() == "/quit":
            break

        print(query)

        op = engine.parse_query_boolean(query)

        # start query time
        start_time = time.perf_counter()
        
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
    
        # calculate query search time
        end_time = time.perf_counter()
        elapsed_time = (end_time - start_time) * 1000 # convert to ms

        engine.printResults(results)
        print(f"\nQuery returned {len(results)} results in {elapsed_time:.2f} ms.")
        if elapsed_time <= 300:
            print("[INFO] Query executed under 300 ms.\n\n")
        else:
            print("[INFO] Query took longer than 300 ms.\n\n")

    