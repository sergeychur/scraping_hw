from bs4 import BeautifulSoup

class CssSelectorParser:
    def parse(self, content, current_url):
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.select_one("table.infobox")

        result = None
        urls = []

        if table is None:
            raise Exception('404')

        table = table.attrs.get('data-name')

        if 'Чемпионат Европы по футболу 2024' in table:
            result, urls = self._main_page_parse(soup)
        elif 'Сборная страны по футболу' in table:
            result, urls = self._team_parse(soup)
        elif 'Футболист' in table:
            result, urls = self._player_parse(soup, current_url)

        return result, urls

    def _main_page_parse(self, data):
        all_web_links = data.select('a')
        actual_web_links = []

        for link in all_web_links:
            url = link.get('href')

            if url is not None:
                actual_web_links.append('https://ru.wikipedia.org' + url)

        return None, actual_web_links

    def _team_parse(self, data):
        players_table = data.find("table", {"class": "wikitable mw-datatable"})
        all_web_links = players_table.select("a")
        actual_web_links = []

        for link in all_web_links:
            url = link.get("href")

            if url is not None:
                actual_web_links.append("https://ru.wikipedia.org" + url)

        return None, actual_web_links

    def _player_parse(self, data, current_url):
        player_data = {}

        #   URL
        player_data['url'] = current_url

        #   Player name
        name = data.select_one("span.mw-page-title-main")
        player_data["name"] = name.contents[0].split(",")

        #   Height
        infobox = data.find("table", {"class": "infobox"})

        tot = infobox.find_all("th", {"style": "text-align:left"})

        

        return player_data, []
