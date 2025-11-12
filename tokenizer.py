# Decoding
import os
import sys
import string

# Stemming and Tokenizing html text and weights 
import re
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
stemmer = PorterStemmer()


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

    if os.path.exists(input_data):
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
    soup = BeautifulSoup(html, "lxml")
    weights = {"title": 3.0, "h1": 2.5, "h2": 2.0, "h3": 1.5, "b": 1.25, "strong": 1.25}
    token_freqs = {}

    # Remove scripts, styles, nav, etc.
    for tag in soup(["script", "style", "noscript", "footer", "header", "nav"]):
        tag.extract()

    # Weighted sections
    for tag_name, weight in weights.items():
        for tag in soup.find_all(tag_name):
            text = tag.get_text(separator=" ", strip=True)
            tokens = tokenize(text)
            for t in tokens:
                token_freqs[t] = token_freqs.get(t, 0) + weight

    # Regular body text (weight 1.0)
    body_text = soup.get_text(separator=" ", strip=True)
    body_tokens = tokenize(body_text)
    for t in body_tokens:
        token_freqs[t] = token_freqs.get(t, 0) + 1.0

    return token_freqs


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