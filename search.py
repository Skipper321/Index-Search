import json, csv, math, struct, heapq
import os.path
import tokenizer
import time
from collections import defaultdict
import nltk 
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords

#nltk.download("wordnet")
#nltk.download("omw-1.4")

STOPWORDS = set(stopwords.words("english"))

class SearchEngine:

    def __init__(self):
        # Load dictionary into memory (small)
        with open("index/dictionary.csv", "r", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            self.dictionary = {
                row["term"]: (int(row["df"]), int(row["offset"]), int(row["length"]))
                for row in rdr
            }
        # Load precomputed synonyms
        with open("index/synonyms.json", "r", encoding="utf-8") as f:
            self.synonym_cache = json.load(f)

        with open("doc_ids.json", "r", encoding="utf-8") as f:
            self.doc_ids = json.load(f) # keys are strings

        with open("index/corpus_meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.N = int(meta["N"])

        # Load doc norms for cosine normalization 
        with open("index/doc_norms.json", "r", encoding="utf-8") as f:
            self.doc_norms = { int(k): float(v) for k, v in json.load(f).items()}


        self.postings_path = "index/postings.bin"
        self.postings_file = open(self.postings_path, "rb")  # open once

        #print(f"[INFO] Loaded dictionary with {len(self.dictionary)} terms.")
        #print(f"[INFO] Ready to search {self.N} documents.")
        #print(f"[INFO] Loaded doc normalizations")


    def read_postings(self, term):
        """Given a term, read its postings"""


        info = self.dictionary.get(term)
        if not info:
            return []
        
        df, offset, length = info

        postings = []
        self.postings_file.seek(offset)
        block = self.postings_file.read(length)
        # with open(self.postings_path, "rb") as f:
        #     f.seek(offset)
        #     block = f.read(length)

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
    
    def __del__(self):
        if hasattr(self, "postings_file"):
            self.postings_file.close()

    # TF-IDF weighting
    def idf(self, df):
        """Calculages TF-IDF weighing"""
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
    
    # fallback_search, when primary search returns 0 results, will try weaker searches to get something useful
    def fallback_search(self, q_terms):
        
        # Try OR search
        or_query = " OR ".join(q_terms)
        results = self.searchFor(or_query, allow_fallback=False)
        if results:
            print("[INFO] Fallback: switched to OR search")
            return results
        
        # Try removing stopwords and search 
        print("[INFO] Trying fallback: removing stopwords")
        
        # if query only contains stopwords i.e "to be or not to be"
        if not q_terms or all(t in STOPWORDS for t in q_terms):
            print("[INFO] Fallback stopped: query contained only stopwords.")
            return []

        content_terms = [t for t in q_terms if t not in STOPWORDS]
        if content_terms:
            results = self.searchFor(" ".join(content_terms), allow_fallback=False)
            if results:
                print("[INFO] Fallback: removed stopwords and retried search.")
                return results
        
        # Try synonyms of each term
        syns = []
        for t in q_terms:
            syn_list = self.synonym_cache.get(t, [])
            syns.extend(syn_list[:3])
        syns = [s for s in syns if s in self.dictionary]

        if syns:
            syn_query = " ".join(syns)
            results = self.searchFor(syn_query, allow_fallback=False)
            if results:
                print("[INFO] Fallback: synonym search")
                return results
        
        # Otherwise nothing found

        print("[INFO] Nothing was found in the corpus")
        return []

    
    def expand_synonyms(self, terms, max_synonyms = 3):
        """Given a term, get a set of its synonyms
        
        :term: term to find synonyms
        :max_synonyms=3: number of synonyms to find"""
        expanded = set()
        for t in terms:
            expanded.add(t)  # always include the original term
            syns = self.synonym_cache.get(t, [])  # look up precomputed synonyms
            expanded.update(syns)
        return expanded
    
    def is_high_df(self, term, threshold=1000):
        if term not in self.dictionary:
            return False
        df, _, _ = self.dictionary[term]
        return df > threshold
            
    def getWeightFromTuple(t):
        """Helper function for accessing tuples in results"""
        return t[1]


    # Searches for multiple terms with TF-IDF scoring
    def searchFor(self, query, top_k=10, allow_fallback = True):
        """Gives search results based on a query, searches for multiple terms with TF-IDF scoring
        
        :query: query to search for
        :top_k=10: number of results"""


        q_terms_original = set(tokenizer.tokenize(query))
        q_terms = list(q_terms_original)  # list for iteration
        
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
            
            # add synonyms for low-DF terms from cache
            syns = self.expand_synonyms([t])
            expanded_terms.extend([syn for syn in syns if syn != t])  # avoid adding the original term twice

        q_terms = expanded_terms
        # Initialize scores and cache
        scores = defaultdict(float)
        postings_cache = {}
    
        # Read postings once and cache them
        for t in q_terms:
            if t not in self.dictionary:
                continue
            
            # If exact word, use weight 1.0, else use 0.6 for synonym
            if t in q_terms_original:
                query_weight = 1.0
            else:
                query_weight = 0.6
                
            postings = self.read_postings(t)

            # TF-IDF scoring
            df, _, _ = self.dictionary[t]
            idf_weight = self.idf(df)
            
            for doc_id, tf, positions in postings:
                tfw = 1 + math.log(max(tf, 1e-6))
                scores[doc_id] += tfw * idf_weight * query_weight

        # Check for phrase search (any number of words in quotes)
        normalized_query = query.strip().lower()
        phrase_mode = normalized_query.startswith('"') and normalized_query.endswith('"')
        if phrase_mode and len(q_terms) >= 2:
            phrase_docs = self.phrase_match(q_terms, postings_cache)
            # Only keep phrase-matching docs
            scores = {d: scores[d] * 2.0 for d in phrase_docs}

        if not scores:
            if allow_fallback:
                print("[INFO] No direct results, trying fallback search...")
                return self.fallback_search(list(q_terms_original))
            else:
                # if fallback fails as well, do not fallback again.
                return []

        # Cosine normalization
        for doc_id in list(scores.keys()):
            scores[doc_id] /= self.doc_norms[doc_id]

        # Top-k results
        top = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])
        results = [(self.doc_ids[str(doc)], score) for doc, score in top]

        return results

    def printResults(self, results):
        """Prints search results"""

        if not results:
            return 
        
        for i, (url, score) in enumerate(results, start=1):
            print(f"{i}.{url} (score={score:.4f})")


    

    def getWeightFromTuple(t):
        """Helper function for sorting result lists, accesses weight in tuple values"""
        # print(f"Term {t[0]} - with weight {t[1]}")
        return t[1]

    def sort_results(results_list:list):
        """Sorts results after merging"""
        # TODO: Sort the results according to its score from highest to lowest
        # Must check if this actually works the way it was intended to

        # print("Sorting results") 
        results_list.sort(reverse=True, key=SearchEngine.getWeightFromTuple)        

        return results_list

    # Boolean search functions
    
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
    
    def split_boolean(self, q):
        """split boolean queries to be able to handle more than one operator per query"""
        tokens = q.split()
        processed_tokens = []
        for t in tokens:
            if t.upper() in ("AND", "OR", "NOT"):
                processed_tokens.append(t.upper())
            else:
                processed_tokens.append(t.lower())
        return processed_tokens
    
    def eval_boolean(self, q):
        tokens = self.split_boolean(q)

        # except more than 3 terms for multi-operator boolean queries
        if len(tokens) < 3:
            return self.searchFor(q)
        
        # start search with the first term
        result = self.searchFor(tokens[0])

        i = 1
        while i < len(tokens) - 1:
            op = tokens[i]
            right_term = tokens[i + 1]

            right_result = self.searchFor(right_term)

            if op == "AND":
                result = self.boolean_and(result, right_result)
            elif op == "OR":
                result = self.boolean_or(result, right_result)
            elif op == "NOT":
                result = self.boolean_not(result, right_result)

            i += 2

        return result
    

    def boolean_and(self, left, right):
        # left / right are lists of [url, score]
        left_dict = {url:score for url, score in left}
        right_dict = {url:score for url, score in right}
        common = left_dict.keys() & right_dict.keys()
        return [(u, left_dict[u] + right_dict[u]) for u in common]

    def boolean_or(self, left, right, top_k = 10):
        combined = {}
        for url, score in left:
            combined[url] = max(score, combined.get(url, 0))
        for url, score in right:
            combined[url] = max(score, combined.get(url, 0))

        sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        # return only top-k (10)
        return sorted_results[:top_k]

    def boolean_not(self, left, right):
        right_urls = {u for u, _ in right}
        return [(u, score) for u, score in left if u not in right_urls]




if __name__ == "__main__":
    engine = SearchEngine()
    
    print("\nSimple Boolean Query Search Engine - Developer:")
    print("Supports boolean operations 'AND', 'OR', 'NOT'")
    print("Supports exact phrase searches using double quotes, e.g., \"building software solutions\"")
    print("Input a search term(s), or type '/quit' to exit.\n")

    while True:
        query = input("Search > ").strip()

        # Quit statement 
        if query.lower() == "/quit":
            break

        terms = tokenizer.tokenize(query)
        # Remove Boolean operators from the terms list for this check
        BOOLEAN_OPS = {"and", "or", "not"}
        terms = [t for t in terms if t not in BOOLEAN_OPS]

        # If ALL terms = stopwords → do NOT search
        if not terms or all(t in STOPWORDS for t in terms):
            print("[INFO] Query contains only stopwords — nothing to search.")
            print("No results.\n")
            continue

        op = engine.parse_query_boolean(query)

        # start query time
        start_time = time.perf_counter()
        
        # Evaluate query using your boolean engine (left-to-right)
        results = engine.eval_boolean(query)

        # if op is not None and op == "AND":
        #     left, right = [s.strip() for s in query.upper().split("AND")]
        #     results = engine.boolean_and(engine.searchFor(left), engine.searchFor(right))
        # elif op == "OR":
        #     left, right = [s.strip() for s in query.upper().split("OR")]
        #     results = engine.boolean_or(engine.searchFor(left), engine.searchFor(right))
        # elif op == "NOT":
        #     left, right = [s.strip() for s in query.upper().split("NOT")]
        #     results = engine.boolean_not(engine.searchFor(left), engine.searchFor(right))
        # elif op == "NONE":
        #     results = engine.searchFor(query)

        # fallback search if no search terms are returned 
        if not results:
            raw_terms = tokenizer.tokenize(query)
            if raw_terms:
                results = engine.fallback_search(raw_terms)
            else:
                print(f"[INFO] No results found for: {raw_terms}")

        SearchEngine.sort_results(results)
    
        # calculate query search time
        end_time = time.perf_counter()
        elapsed_time = (end_time - start_time) * 1000 # convert to ms

        engine.printResults(results)
        print(f"\nQuery returned {len(results)} results in {elapsed_time:.2f} ms.")

    