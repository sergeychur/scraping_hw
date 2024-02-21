from urllib.parse import urlparse


class Item:
    def __init__(self, url, tries=0):
        self.url = url
        self.start = None
        self.tries = tries
        self.host = self._get_host(url)

    @staticmethod
    def _get_host(url: str) -> str:
        return urlparse.urljoin(url, '/') 