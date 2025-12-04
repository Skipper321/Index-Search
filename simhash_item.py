import string
import hashlib
# from tokenizer import getSortedList

B_BIT = 16 # Bit constant
THRESHOLD = 0.9

class SimHash:
    """Helper class to organize functions that are similar to each other for Simhash"""

    def hash_word(my_str:str) -> str:
        """Creates an B BIT hash value from a given string, of binary values only

        NOTE: not to be used with text, should be used with words specifically
        
        Returns a string"""

        hashcode=hashlib.md5(my_str.encode('utf-8')).hexdigest()
        result = int(bin(int(hashcode,16))[2:])
        temp_str = str(result) + ""

        if (len(temp_str) < B_BIT):
            temp_str = temp_str*8
            temp_str = temp_str[0:B_BIT]
        if (len(temp_str) > B_BIT):
            temp_str = temp_str[0:B_BIT]

        return temp_str

    def get_sorted_frequencies(freq:dict, reverse=True):
        """Sort dictionary by key instead 

        Ranked by highest to lowest (reverse=True)

        Returns a list[[i, frequency]]

        :freq: Dictionary of word frequencies
        :reverse=True: Whether or not you want the frequencies to be ranked from highest to lowest
        """

        valueSorted = sorted(freq, key=freq.get, reverse=True)
        myList = []

        for i in valueSorted:
            current = [i, freq[i]]
            myList.append(current)
        
        return myList

    def get_signs(word: string):
        """Given a word, return its signs
        
        Returns list of -1 and 1"""

        hash_val = SimHash.hash_word(word)
        to_num = [int(digit) for digit in str(hash_val)]
        to_sign = [1 if num > 0 else -1 for num in to_num]


        return to_sign

    def determine_sign(hash_digit):
        """
        Helper function to determine signs from a hash digit

        :True: positive sign (addition)

        :False: negative sign (subtraction)
        """
        return (hash_digit == 1)

    def get_simhash(frequency:dict) -> string:
        """Creates a fingerprint (simhash method) based on the token frequency dictionary

        Returns the hash as a string

        Currently doesn't discrimminate with HTML tags, so should be used in areas where the content is likely
            
        :tokens: dictionary of token with the keys as frequency
        """

        # Sorts frequency by weights
        weights = SimHash.get_sorted_frequencies(frequency)
        n = len(weights)

        # Create V vector
        # NOTE: IMPORTANT!! this MUST be in the sorted order of `weights`)
        signs = [ SimHash.get_signs(item[0]) for item in weights ]
        # A list of list<boolean> of size n
        # Each entry representing a hash value, of size b-bit

        # Optionally prints the weights
        # for i in range(0, len(signs)): 
        #     print(weights[i][0], " has weight: " , weights[i][1], " and signs: ", signs[i])

        # Calculates the v vector sum
        sum = 0
        position_sum = []

        # j = rows (number of words)
        # i = columns (always 8 or however many bits)
        for i in range (0, B_BIT):
            current_sum = 0

            for j in range(0, n):
                # current_word = weights[j][0] 
                current_weight = weights[j][1]
                current_sign = signs[j][i]
                current_sum += (current_weight*current_sign)

            position_sum.append(current_sum)        
            sum += current_sum

        # Optionally prints the sum for each position
        # print("sums at each positions: (index = item) ", position_sum)


        # Given the V vector final values, returns a final hash (as a string)
        result = ""
        for value in position_sum:
            result += str(1 if value >= 0 else 0)

        return result

    def is_similar(hash1:string, hash2:string, threshold=THRESHOLD):
        """Given two hashes, determine if they are similar
        
        :hash1: hash of item 1
        :hash2: hash of item 2
        :threshold=0.9: if similarity >= threshold, then it's too similar"""

        similarity_score = SimHash.get_similarity_score(hash1, hash2, threshold)

        return similarity_score >= THRESHOLD

    def get_similarity_score(shv1, shv2, b_bit=B_BIT) -> float:
        """Calculates the similarity score of two simhashes, returns a float 
        
        :b_bit=B_BIT: bits used during hashing
        """

        # If int, convert to string
        shv1 = shv1 + "" if (type(shv1) == int) else shv1 
        shv2 = shv2 + "" if (type(shv2 == int)) else shv2    


        common_count = 0
        for i in range (0, B_BIT):
            if (shv1[i] == shv2[i]):
                common_count += 1
        score = common_count/B_BIT

        return score


class sh_item:
    """Simhash item, representing a single simhash
    
    :simhash_value: simhash value that was generated from tokenizing process
    :threshold: can be set, but shouldn't... it's best to set this from `tokenizer.py itself`
    """
    def __init__(self, simhash_value:str, threshold=THRESHOLD):
        self.value = simhash_value
        self.threshold = threshold
    
    def __hash__(self):
        # Sets require the hash function, do not change
        # You should rehash because self.value is a string and hash is an int
        return hash(self.value)

    def __eq__(self, other):
        # Assuming that other is also type simhash
        is_exact = other.value == self.value # exact match

        score = SimHash.get_similarity_score(other.value, self.value)

        # print("Comparing ", self.value, " to ", other.value)
        # print("Score: ", score, "| Threshold: ", self.threshold)

        is_similar = (score >= self.threshold)
        return is_exact | is_similar

class sh_set:
    # TODO: need to optimize... especially if we're not using it batch-wise
    """A set of simhashes
    
    Will not accept hashes that are too similar

    :threshold: default threshold is 0.7, but can be changed
    """

    def __init__(self, threshold=THRESHOLD):
        self.threshold = threshold 
        self.values = {}
        self.uniques = set()
        self.size = 0

    def threshold():
        return THRESHOLD

    def add(self, simhash:sh_item):
        """Adds a new simhash item to the simhash set

        True: Value was unique or similar
        False: Value was not unique or similar
        """
        self.uniques.add(simhash.value) # don't add the simhash object itself

        if (self.size == len(self.uniques) | self.__contains__(sh_item)):
            # Value was not unique OR simhash value was too similar
            # print("Too similar: ", simhash.value)
            return False 
        else:
            # Value was unique enough OR simhash was not found
            self.values[sh_item] = 1
            self.size = len(self.uniques)
            return True
    
    def __contains__(self, simhash:sh_item):
        """Returns true if set contains simhash item (or similar simhash items), or false if not
        
        If threshold = 0, it will always be false
        """

        return simhash in self.values

    def __sizeof__(self):
        return self.size


if __name__ == "__main__":
    i1 = sh_item("1111000011110000")
    i2 = sh_item("1111000011110000")

    i3 = sh_item("1111000011110001")
    i4 = sh_item("1111011111110111")

    print("Hash and equality should both be equal and true (requirement for sets): ", i1 == i1, ", ", hash(i1) == hash(i1))

    print ("Should be both true: ", i1 == i2, ", ", hash(i1) == hash(i2) )
    print ("Should be both false: ", i1 == i4, ", ", hash(i1) == hash(i4))
    print("Similarity test: ", i1 == i3, ", ", hash(i1) == hash(i3))

    myset = sh_set()

    print("Threshold: ", myset.threshold)