import json
import os.path
import indexer
import tokenizer

class SearchEngine:

    def __init__(self, path):
        self.path = path

    # Main function which generates search results
    #
    # Takes a search query
    # Returns dictionary results (for now)
    def searchFor(self, input):
        # TODO: need editing
        return

    # Searches for one term at a time
    #
    # Takes tokenized search query
    # Returns positional indices for each search as a dictionary
    def searchOne(term, index_path):
        results = {}

        with open(index_path) as f:
            data = json.load(f)
            result = [data[x] for x in data if x == term]
            print(term, ": ", result)
            results[term] = result;

        return results

    # Searches for the phrase positionally
    # 
    # Takes positional indices from a dictionary
    # Returns search terms merged, ensuring proximity
    def searchAllTerms(query, indices):

        if type(indices) == dict:
            # NOTE: Expected behavior
            pass
        else:
            # TODO: parse it as a path
            # Or identify it somehow
            pass

        results = {}

        query_tokens = tokenizer.tokenize(query)

        # TODO: need doing... what do we want to do here?

        return results
    
    def results(self):
        return self.results


if __name__ == "__main__":
    input = tokenizer.getInput()

    if input == "":
        input = [
            "cristina lopes", 
            "machine learning",
            "ACM",
            "master of software engineering"]

    # NOTE: sorry I haven't used this yet because i literally didn't get the results yet so i'm only really able to search within index_part_0.json
    # default_path = "index_final.json" 
    default_path = "index_part_0.json"
    
    # TODO: need to change this for the actual engine
    # this is just a test

    sg = SearchEngine(default_path)
    sg.searchFor(input)
    
    sg.results()