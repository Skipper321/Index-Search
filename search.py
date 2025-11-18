import json
import os.path
import indexer
import tokenizer

class SearchEngine:

    def __init__(self, final_index_path="final_index.json"):
        self.path = final_index_path

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
    def searchOne(self, term, index_path=""):
        if index_path == "":
            index_path = self.path

        docid_and_weight = {}

        with open(index_path) as f:
            data = json.load(f)
            # result = [data[x] for x in data if x == term]

            if (data[term]):
                for result in data[term]:
                    docid = result[0]
                    weight = result[1]

                    # TODO: we want to save the position as well right? not just docid and weight
                    # so that it still works if we want a search query with two words next to each other
                    # and not just one which allows us to know that it's present in the document

                    docid_and_weight[docid] = weight
        
        print("Searched the term ", term , " and found the following doc_ids and weights: ", docid_and_weight)
        
        return docid_and_weight

    # Searches for the phrase positionally
    # 
    # Takes positional indices from a dictionary
    # Returns search terms merged, ensuring proximity
    def searchAllTerms(self, query, index_path=""):
        results = {}

        query_tokens = tokenizer.tokenize(query)
        firstResult = {}
        nextToEachOther = {}

        for i in range(0, length(query_tokens)):
            if (i == 1):
                firstResult = self.searchOne(query_tokens[i], index_path)
            else:
                result = self.searchOne(query_tokens[i], index_path)
            
            

        # TODO: need doing... what do we want to do here?

        return results
    
    def results(self):
        return self.results


if __name__ == "__main__":
    input = [
        "cristina lopes", 
        "machine learning",
        "ACM",
        "master of software engineering"]

    # NOTE: sorry I haven't used this yet because i literally didn't get the results yet so i'm only really able to search within index_part_0.json
    # default_path = "index_final.json" 
    default_path = "index/index_part_0.json"
    
    # TODO: need to change this for the actual engine
    # this is just a test

    sg = SearchEngine(default_path)
    sg.searchOne("artificial")