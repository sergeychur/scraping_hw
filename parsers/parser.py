import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class CssParser:
    def parse(self, content, cur_page_url):
        soup = BeautifulSoup(content, "html.parser")

        if "Чемпионат" in soup.title.text:
            return None, self._parse_chempoinship(soup, cur_page_url)

        if "Сборная" in soup.title.text:
            return None, self._parse_team(soup, cur_page_url)

        return self._parse_player(soup, cur_page_url), []

    
    def _parse_chempoinship(self, root, cur_page_url):
        table = root.select("table.standard tr td:nth-child(1) > a")
        
        links = [ln.get("href") for ln in table]
        links = [urljoin("https://ru.wikipedia.org/", ln) for ln in links]
        
        return links
    

    def _parse_team(self, root, cur_page_url):
        pointer = root.find("span", id=re.compile("^Текущий_состав"))
        if not pointer:
            pointer = root.find("span", id=re.compile("^Состав"))
        pointer = pointer.parent
        
        while not (pointer.name and pointer.name == "table"):
            pointer = pointer.next_sibling
            
        table = pointer.tbody.select("tr")
        table = [ln.select_one("td:nth-child(3) > a") for ln in table]
        
        links = [ln.get("href") for ln in table if ln]
        links = [ln for ln in links if "index.php" not in ln]
        links = [urljoin("https://ru.wikipedia.org/", ln) for ln in links]
        
        return links


    def _parse_player(self, root, cur_page_url):
        return {"player": root.title.text}
