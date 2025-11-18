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
    # Returns a common dictionary
    def searchAllTerms(self, query, index_path=""):
        query_tokens = tokenizer.tokenize(query)
        common = {}

        # `common` - Represents all locations of search terms that show up in the same place
        # key = location

        # value = list of weights
        # position of list = weight of query term

        # for example, query = "john steinbeck" 
        # "john" -> [3, 1.3]
        # "steinbeck" -> [3, 4.2] [6, 7.2]
        # common = {3, [1.3, 4.2]}
        # query[0] = "john", common[3][0] = 1.3 (weight of "john")

                    
        return common 

    def printCommon(self, query, index_path):
        print("Searched for ", query, " within file ", index_path)
        print(self.searchAllTerms(query, index_path))
    

    # Takes two dictionaries and merges it
    # Keys = docid
    # Values = weights
    # Position for values = position of word in query
    # Values are in a list
    def getCommon(dict1, dict2):
        merged = {}

        d1 = set(dict1)
        d2 = set(dict2)

        common_keys = d1.intersection(d2)

        for key in common_keys:
            merged[key] = [dict1[key], dict2[key]]

        return merged
    
    def results(self):
        return self.results


if __name__ == "__main__":
    input = [
        "cristina lopes", 
        "machine learning",
        "ACM",
        "master of software engineering"]

    # NOTE: sorry I haven't used this yet because i literally didn't get the results yet so i'm only really able to search within index_part_0.json
    final_index = "final_index.json" 
    default_path = "index/index_part_0.json"
    
    # TODO: need to change this for the actual engine
    # this is just a test

    sg = SearchEngine(default_path)
    sg.searchOne("artificial")
    sg.printCommon("machine learning", final_index)