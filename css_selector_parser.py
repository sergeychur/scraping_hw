from bs4 import BeautifulSoup

class CssSelectorParser:
    def parse(self, content):
        soup = BeautifulSoup(content)
        element = soup.select_one('article.product_page')

        if element is not None:
            result = self._parse_book(soup)
            return result, []