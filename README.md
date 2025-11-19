# cs121-projects
A repository for CS121 A3: 
- Max maxwels@uci.edu
- Lola lolak@uci.edu
- Julie minhab@uci.edu

Inputs: 
- Developer.zip: A large amount of webpages

Outputs:
- final.json of all unqiue tokens and summary statistics.

Link to report: 
https://docs.google.com/document/d/1cZwJC8PhzzUrJywTjfjHYW5TceV56hibrpc7OzomDg4/edit?usp=sharing


## Indexer - General notes
From 

`tokenizer.py` - this is copied from previous files

`unzip.py` - this unzips your file with the usage format: `python -u parse.py [filename.zip here]`

`file_items` - treats each file as an item, handles json within the file itself

Note: my .gitignore includes `analyst.zip` and `developer.zip` because we already have access to these files. Github won't let me unzip 1000+ changes from the folder when you unzip so you'll have to run the command yourself.

## Completed Items

'indexer.py': Functional
`file_items.py`:  Functional
`def parse_contents`: Functional
`tokenizer.py`: Functional: 


## How to run

### Installations required
`python -pip install nltk`
`python -m pip install lxml`
'python pip install bs4'

### Running the installer
`python -u unzip.py`
`python indexer.py`

### Running the query
`python search.py`