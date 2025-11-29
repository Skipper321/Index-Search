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

import nltk
nltk.download('stopwords')
STOPWORDS = set(stemmer.stem(w) for w in stopwords.words("english")) # use set for fast lookup
STOPWORD_WEIGHT = 0.5

# sort dictionary by key instead 
# returns a list
def getSortedList(freq:dict):
    valueSorted = sorted(freq, key=freq.get, reverse=True)
    myList = []

    for i in valueSorted:
        current = [i, freq[i]]
        myList.append(current)
    
    return myList

# prints dict - renamed so that doesn't interfere with built in print function
# returns list (optional)
def print_freq(freq:dict) -> list:
    myList = getSortedList(freq)

    for i in myList:
        current = i[0] + " -> " + str(i[1])
        __builtins__.print(current)
    return myList

# retrieves the path
# position = file position path
def getInput(position:int = 1):
    path = sys.argv[position]

    # Check if path exits
    if os.path.exists(path):
        # __builtins__.print("filename : " + path.split("/")[-1])
        return path    
    else:
        __builtins__.print("Path not found! Input: ", path)

# converts char to ascii
def charToAscii(myChar):
    return ord(myChar)

# determines if char is alphanumeric
def isAsciiChar(ch) -> bool:

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


# checks if string is valid
# 
# -1 if valid
# index of the first character that is invalid
def isValidWord(word:string):
    # Note: return -1 if valid

    for i in range(0, len(word)):
        if not isAsciiChar(word[i]):        
            return i
    return -1
    
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

# tokenizer - IGNORE we need to use stemming (we just call it for tokenizing alphanumeric)
def tokenize(input_data: str):
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
                    stemmed = stemmer.stem(word.lower())
                    tokens.append(stemmed)
                else:
                    wordsSlicedFromWord = getSlicedWords(word)
                    stemmed_words = [stemmer.stem(w.lower()) for w in wordsSlicedFromWord]
                    tokens.extend(stemmed_words)
            except Exception:
                continue

    return tokens


# tokenizes HTML, borrows from original tokenizer for alphanum, but also incorporates weights
def tokenize_html(html: str):
    #Tokenizes HTML content and applies weighting for title, headings, and bold text.
    #Returns a dict of stemmed tokens -> weighted term frequency.
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
        </body>
    </html>
    """
    tokens = tokenize_html(samplehtml)
    print("Weighted tokens:\n")
    for t, freq in list(tokens.items())[:15]:
        print(f"{t}: {freq}")
    #shouldBeSorted = print(frequencies)