# Decoding
import os
import sys
import string

# Stemming and Tokenizing html text and weights 
import re
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords # use nltk stopword list
from bs4 import BeautifulSoup
stemmer = PorterStemmer()
stem_cache = {}
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

# run these lines once to download nltk stopwords !
# import nltk
# nltk.download('stopwords')

STOPWORDS = set(stemmer.stem(w) for w in stopwords.words("english")) # use set for fast lookup
STOPWORD_WEIGHT = 0.5

# For similarity detection
import hashlib

def get_value(weight, sign:bool):
    """Given a weight, apply its sign"""
    return weight if sign else weight*(-1)

def get_final_hash(values):
    """Given the V vector final values, returns a final hash (as a string)"""
    myhash = ""

    for value in values:
        myhash += str(1 if value >= 0 else 0)

    return myhash

def get_signs(word):
    """Given a word, return its signs
    
    Returns list of booleans"""
    return [ determine_sign(item) for item in num_to_list(hash_word(word)) ] 

def determine_sign(hash_digit):
    """
    Helper function to determine signs from a hash digit

    :True: positive sign (addition)

    :False: negative sign (subtraction)
    """
    return (hash_digit == 1)

# TODO: this is a temporary solution
# needs work/response from TA since we're not sure how the binary values are generated
def hash_word(my_str):
    """Creates an 8 bit hash value from a given string, of binary values only"""

    hashcode=hashlib.md5(my_str.encode('utf-8')).hexdigest()
    result = int(bin(int(hashcode,16))[2:])
    temp_str = str(result) + ""

    if (len(temp_str) < 8):
        temp_str = temp_str + len(str(result))*"0" + "1"
    if (len(temp_str) > 8):
        temp_str = temp_str[0:8]

    return temp_str

def num_to_list(hash_val):
    """Converts a numeric hash value into a list of numbers, helper function for vectorization"""
    return [int(digit) for digit in str(hash_val)]

def sim_hash(text):
    """Creates a fingerprint based on the text body
    
    Currently doesn't discrimminate with HTML tags, so should be used in areas where the content is likely"""
    tokens = tokenize(text)
    
    # frequency counts how frequent word appears in text (ie. "weights")
    unique = set(tokens)
    frequency = {}
    for word in unique:
        frequency[word] = tokens.count(word)
    weights = getSortedList(frequency) # A list of [word, frequency] items
    n = len(weights)

    # Create V vector
    # NOTE: IMPORTANT!! this MUST be in the sorted order of `weights`)
    signs = [ get_signs(item[0]) for item in weights ]
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
    for i in range (0, 8):
        current_sum = 0

        for j in range(0, n):
            # current_word = weights[j][0] 
            current_weight = weights[j][1]
            current_sign = signs[j][i]
            current_value = get_value(current_weight, current_sign)
            current_sum += current_value

        position_sum.append(current_sum)        
        sum += current_value

    # Optionally prints the sum for each position
    # print("sums at each positions: (index = item) ", position_sum)
    result = get_final_hash(position_sum)
            
    return result

def detect_similarity(item1, item2, threshold=0.9):
    """Detects similarity with pre-existing documents
    :threshold=0.9: 
    Returns true if similar, false if not similar"""
    sim_score = 0

    f1 = create_fingerprint(item1)
    f2 = create_fingerprint(item2)

    
    return (sim_score > threshold)


def getSortedList(freq:dict):
    """sort dictionary by key instead 
    returns a list[[i, frequency]]"""

    valueSorted = sorted(freq, key=freq.get, reverse=True)
    myList = []

    for i in valueSorted:
        current = [i, freq[i]]
        myList.append(current)
    
    return myList



#!SECTION - Output helper functions

# prints dict - renamed so that doesn't interfere with built in print function
# returns list (optional)
def print_freq(freq:dict) -> list:
    myList = getSortedList(freq)

    for i in myList:
        current = i[0] + " -> " + str(i[1])
        __builtins__.print(current)
    return myList

def getInput(position:int = 1):
    """retrieves the path

    position = file position path
    """
    path = sys.argv[position]

    # Check if path exits
    if os.path.exists(path):
        # __builtins__.print("filename : " + path.split("/")[-1])
        return path    
    else:
        __builtins__.print("Path not found! Input: ", path)


#!SECTION - Validates words

def charToAscii(myChar):
    """converts char to ascii"""
    return ord(myChar)

def isAsciiChar(ch) -> bool:
    """Determines if char is alphanumeric"""

    aVal = charToAscii(ch)

    # numerical
    if aVal > 47 and aVal < 58:
        return True

    # uppercase
    if aVal > 64 and aVal < 91:
        return True 
    
    # lowercase
    if aVal > 96 and aVal < 123:
        return True 

    return False

def isValidWord(word:string):
    """Checks if string is valid

    -1 if valid

    index of the first character that is invalid
    """
    # Note: return -1 if valid

    for i in range(0, len(word)):
        if not isAsciiChar(word[i]):        
            return i
    return -1



#!SECTION - Helper functions to slice words until they're valid

# gets indices of non-alphanumeric characters in a word
def getSliceIndices(word:string):
    indices = []
    for i in range(0, len(word)):
        currentChar = word[i]

        if not isAsciiChar(currentChar):
           indices.append(i)

    return indices

# takes non-alphanumeric word and gets alphanumeric words within that word
def getSlicedWords(bigWord:string, firstSplit = -1):
    splittedWords = []
    prev = 0

    idxs = getSliceIndices(bigWord) # O(N)
    idxs.append(len(bigWord))

    for i in idxs: # O(N) also
        currentWord = bigWord[prev:i]
        if currentWord.isalnum():
            splittedWords.append(bigWord[prev:i])
        prev = i + 1

    return splittedWords




#!SECTION - Tokenizer functions

# tokenizer - NOTE: IGNORE we need to use stemming (we just call it for tokenizing alphanumeric)
def tokenize(input_data: str):
    """Raw tokenizer with no stemming, returns a list of tokens
    """
    tokens = []

    if os.path.isfile(input_data):
        with open(input_data, 'r', encoding='utf8') as f:
            raw_list = f.readlines()
    else:
        raw_list = input_data.splitlines()

    for line in raw_list:
        for word in line.split():
            try:
                valIndex = isValidWord(word)
                if valIndex == -1:
                    tokens.append(word.lower())
                else:
                    tokens.extend(getSlicedWords(word))
            except Exception:
                continue

    return tokens

# """tokenizes HTML, borrows from original tokenizer for alphanum, but also incorporates weights"""
def tokenize_html(html: str):
    """    Tokenizes HTML content and applies weighting for title, headings, and bold text.
    Returns a dict of stemmed tokens -> weighted term frequency.
    """

    soup = BeautifulSoup(html, "html.parser")
    weights = {"title": 3.0, "h1": 2.5, "h2": 2.0, "h3": 1.4, "b": 1.6, "strong": 1.6 }# Modified heading weights

    # Remove scripts, styles, nav, etc.
    for tag in soup(["script", "style", "noscript", "footer", "header", "nav"]):
        tag.extract()

    pos = 0 # global position counter
    token_positions = {} # ex: {stem: [(pos, weight), ...]}
    token_freqs = {}

    # Handle Weighted sections/tags with positions
    for tag_name, w in weights.items():
        for tag in soup.find_all(tag_name):
            text = tag.get_text(separator=" ", strip=True)
            tokens = TOKEN_RE.findall(text.lower())

            for t in tokens:
                # use cache 
                if t not in stem_cache:
                    stem_cache[t] = stemmer.stem(t)
                stem = stem_cache[t]

                # compute final weight considering stopwords
                final_weight = w
                if stem in STOPWORDS:
                    final_weight = STOPWORD_WEIGHT * w

                # Record token frequency
                token_freqs[stem] = token_freqs.get(stem, 0) + final_weight

                # Record stem position
                if stem not in token_positions:
                    token_positions[stem] = []
                token_positions[stem].append((pos, final_weight))

                # Iterate to next position
                pos += 1

    # Handle Regular body text (weight 1.0)
    body_text = soup.get_text(separator=" ", strip=True)
    body_tokens = TOKEN_RE.findall(body_text.lower())

    for t in body_tokens:
        if t not in stem_cache:
            stem_cache[t] = stemmer.stem(t)
        stem = stem_cache[t] 

        final_body_weight = 1.0
        if stem in STOPWORDS:
            final_body_weight *= STOPWORD_WEIGHT
        # Record token frequency
        token_freqs[stem] = token_freqs.get(stem, 0) + final_body_weight

        # Record stem position
        if stem not in token_positions:
            token_positions[stem] = []
        token_positions[stem].append((pos, final_body_weight))
        
        # Iterate to next position
        pos += 1

    return {
        "tf": token_freqs,
        "positions": token_positions
    }

# gets word frequency
def computeWordFrequencies(tokenList):
    myDict = dict()

    for i in range(0, len(tokenList)):
        currentWord = tokenList[i].casefold()

        if myDict.get(currentWord) == None:
            myDict[currentWord] = 1
        else:
            myDict[currentWord] += 1

    return myDict

# Just for testing locally
if __name__ == '__main__':
    samplehtml = """
    sample_html = 
    <html>
        <head><title>UCI Computer Science</title></head>
        <body>
            <h1>Research Areas</h1>
            <p>UCI focuses on computing and data science.</p>
            <b>Machine Learning</b> is a core field.
            <a href="http://en.wikipedia.org/wiki/Main_Page">Sample anchor words</a>
        </body>
    </html>
    """

    # sample_fingerprinting = "I love diving, I love love love love"
    # print(sim_hash(sample_fingerprinting))

    tokens = tokenize_html(samplehtml)
    print("Weighted tokens:\n")
    for t, freq in list(tokens.items())[:15]:
        print(f"{t}: {freq}")

    shouldBeSorted = print(frequencies)