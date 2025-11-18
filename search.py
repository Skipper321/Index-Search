import json
import os.path
import indexer
import tokenizer

# Searches for one term
def searchOne(term, index_path):
    with open(index_path) as f:
        data = json.load(f)
        result = [data[x] for x in data if x == term]
        print(term, ": ", result)


if __name__ == "__main__":
    example_queries = [
        "cristina lopes", 
        "machine learning",
        "ACM",
        "master of software engineering"]
    
    default_path = "index_final.json"
    
    # TODO: need to change this for the actual engine
    # this is just a test
    for queries in example_queries:
        query_tokens = tokenizer.tokenize(queries)

        for token in query_tokens:
            searchOne(token, "index_part_0.json")