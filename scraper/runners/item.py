from urllib.parse import urlparse


class Item:
    def __init__(self, url, extra_info=None, tries=0):
        self.url = url
        self.start = None
        self.end = None
        self.tries = tries
        self.extra_info = extra_info
