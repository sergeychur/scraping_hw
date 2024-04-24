import json


class Item:
    def __init__(self, url, tries=0):
        self.url = url
        self.start = None
        self.tries = tries
        self.content = None

    def __str__(self):
        return json.dumps({
            'url': self.url
        })
