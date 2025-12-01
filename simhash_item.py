import tokenizer
import string
import hashlib

B_BIT = tokenizer.B_BIT()
THRESHOLD = tokenizer.THRESHOLD()

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

        common_count = 0
        for i in range (0, B_BIT):
            if (other.value[i] == self.value[i]):
                common_count += 1
        score = common_count/B_BIT

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

    def threshold(self):
        return self.threshold

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
    i3 = sh_item("1111000111110001")
    i4 = sh_item("1111011111110111")

    print ("Should be both true: ", i1 == i2, ", ", hash(i1) == hash(i2) )
    print ("Should be both false: ", i1 == i4, ", ", hash(i1) == hash(i4))

    myset = sh_set()

    print("Threshold: ", myset.threshold)