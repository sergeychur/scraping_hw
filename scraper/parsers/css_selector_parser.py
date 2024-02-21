from bs4 import BeautifulSoup


class CssSelectorParser:
    def parse(self, content: str, base_url: str):
        soup = BeautifulSoup(content) 