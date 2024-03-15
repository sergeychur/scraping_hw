from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone


class CssSelectorParser:
    def parse(self, content, current_url, data_base):
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.select_one('table.infobox')

        result = None
        urls = []

        if table is None:
            raise Exception('404')

        table = table.attrs.get('data-name')

        if "Соревнование футбольных сборных" in table:
            result, urls = self._main_page_parse(soup)
        elif 'Сборная страны по футболу' in table:
            result, urls = self._team_parse(soup, data_base)
        elif 'Футболист' in table:
            result, urls = self._player_parse(soup, data_base, current_url)

        return result, urls

    def _main_page_parse(self, data):
        '''Find table with all teams that will participate, find all links in row and take the last that goes to country team page'''

        team_table = data.find("table", {"class": "standard sortable"})
        all_web_links = []

        for row in team_table.find_all('tr')[1:]:
            col = row.find('td')
            url = col.select('a')[-1]

            if url is not None:
                all_web_links.append("https://ru.wikipedia.org" + url.get('href'))

        return None, all_web_links

    def _team_parse(self, data, data_base):
        players_table = data.find("table", {"class": "wikitable"})
        actual_web_links = []

        for row in players_table.find_all('tr')[1:]:
            cols = row.find_all('td')

            if len(cols) == 0:
                continue

            pos = cols[1].find("a").text
            name = cols[2].find('a').text.strip(' ')
            url = "https://ru.wikipedia.org" + cols[2].find('a').get('href')
            bday = cols[3].find("span", {"class": "bday"})['title']
            timestamp = int(time.mktime(time.strptime(bday, '%Y-%m-%d'))) - datetime.now(timezone.utc).toordinal()
            matches = int(cols[4].text)
            goals = int(cols[5].text)
            current_club = cols[6].text[:-1]

            # if not data_base.isInBase(name):
            #     data_base.saveInfo(name, {
            #         "name": name,
            #         "url": url,
            #         "position": pos,
            #         "current_club": current_club,
            #         "birth": timestamp,
            #         "national_caps": matches,
            #         "national_scored": goals,
            #         "national_conceded": 0,
            #         }
            #     )

            actual_web_links.append(url)

        return None, actual_web_links

    def _player_parse(self, data, data_base, current_url):
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
