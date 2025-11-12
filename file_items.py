import warnings
from bs4 import XMLParsedAsHTMLWarning, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

import json
from bs4 import BeautifulSoup


class FileItem:
# FileItem: Allows for each file to be treated as an object
# for example, in raw/analyst/www_cs_uci_edu, 
# there are different files, and this object represents that file

    url = ""
    contents = ""
    encoding = ""
    filename = ""

    def __init__(self, js_filename):
        self.filename = js_filename
        self.parse_data()
    

    def parse_data(self):
        # NOTE: A method that parses the content of the fileItem, with json library
        try: 
            with open(self.filename, 'r', encoding='utf-8') as file:
                data = file.read().strip()

            if not data:
                print(f"Warning: {self.filename} is empty")
                self.url = ""
                self.content = ""
                self.encoding = ""
                return

            parsed_data = json.loads(data)
        
            # print("printing:" , parsed_data['url'])
            self.url = parsed_data['url']
            self.content = parsed_data['content']
            self.encoding = parsed_data['encoding']

        except json.JSONDecodeError:
            print(f"Warning: {self.filename} is not valid JSON, skipping.")
            self.url = ""
            self.content = ""
            self.encoding = ""
    
    def parse_contents(self):
        # TODO: A method that parses the contents of the fileItem
        # because we only have the raw HTML
        
        # check the type of content
        if self.content.strip().startswith("BEGIN:VCALENDAR"):
            # calendar content, return as is
            return self.content
        else:
            # otherwise, HTML doc
            soup = BeautifulSoup(self.content, "html.parser")  # use HTML parser
            # remove scripts and styles
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return text

# if __name__ == "__main__":
#     default_test = "raw\\ANALYST\\www-db_ics_uci_edu\\16c4d46a219e4961a76bb1e1bc7b5cd2d812c3ec2580baf91f0a4ad89cc0d208.json"

#     fi = FileItem(default_test)
    # print("url:", fi.url)
    # print("file content:", fi.content)
    # print("file name:", fi.filename)