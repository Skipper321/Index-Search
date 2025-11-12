import json

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

        with open(self.filename, 'r') as file:
            data = file.read()

        parsed_data = json.loads(data)
    
        print("printing:" , parsed_data['url'])
        self.url = parsed_data['url']
        self.content = parsed_data['content']
        self.encoding = parsed_data['encoding']
    
    def parse_contents(self):
        # TODO: A method that parses the contents of the fileItem
        # because we only have the raw HTML
        pass

# if __name__ == "__main__":
#     default_test = "raw\\ANALYST\\www-db_ics_uci_edu\\16c4d46a219e4961a76bb1e1bc7b5cd2d812c3ec2580baf91f0a4ad89cc0d208.json"

#     fi = FileItem(default_test)
    # print("url:", fi.url)
    # print("file content:", fi.content)
    # print("file name:", fi.filename)