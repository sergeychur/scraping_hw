from bs4 import BeautifulSoup
import time
from dateutil import parser


class CssSelectorParser:
    def parse(self, content, current_url):
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
            #   delete all unnecessary html code before needed table with current team
            s = ''

            country = soup.find("table", {'class': "infobox"}).find("tr").find("th").text.strip(' \n\r')

            if country == 'Англия':
                s = '<span class="mw-headline" id="Текущий_состав_сборной">Текущий состав сборной</span>'
            else:
                s = '<span class="mw-headline" id="Текущий_состав">Текущий состав</span>'

            print(s)

            soup = BeautifulSoup(content.decode()[content.decode().find(s) :].encode(), 'html.parser')
            result, urls = self._team_parse(soup)
        elif 'Футболист' in table:
            result, urls = self._player_parse(soup, current_url)

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

    def _team_parse(self, data):
        table = data.find("table", {"class": "wikitable"})
        actual_web_links = []

        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')

            if len(cols) == 0 or len(cols) == 1:
                continue

            url = "https://ru.wikipedia.org" + cols[2].find("a").get("href")
            actual_web_links.append(url)

        return None, actual_web_links

    def _standart_text_data(self, text):
        while not text[-1].isalpha():
            text = text[: len(text) - 1]

        return text

    def _player_parse(self, data, current_url):
        player_data = {}
        club_career_ind = 0
        national_team_career_ind = 0
        last_needed_row_ind = 0

        player_data = {
            'url': current_url,
            'name': '',
            'height': 0,
            'position': '',
            'current_club': '',
            'club_caps': 0,
            'club_conceded': 0,
            'club_scored': 0,
            'national_caps': 0,
            'national_conceded': 0,
            'national_scored': 0,
            'national_team': ''    
        }

        infobox = data.find("table", {"class": "infobox"})
        rows = infobox.find_all('tr')

        #   Name
        name = rows[0].find('div', {'class': 'label'}).text.strip().split(' ')

        if len(name) > 2:
            name = name[:2]

        player_data['name'] = name[::-1]

        for row in rows[1:]:
            line_type = row.find('th')

            if line_type is None:
                continue

            line_type_text = self._standart_text_data(line_type.text.strip())

            if line_type_text == 'Родился':
                bday = row.find("span", {"class": "nowrap"}).find_all('a')
                bday[0] = bday[0].text
                bday[1] = bday[1].text

                months = ['января', "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
                day, month = bday[0].split(" ")
                year = bday[1]
                month_num = months.index(month) + 1

                birth_str = f"{year}.{month_num}.{day}"
                timestamp = parser.parse(birth_str).timestamp()

                player_data['birth'] = int(timestamp)
                player_data['birt_str'] = birth_str
            elif line_type_text == 'Рост':
                height = row.find("span", {"class": "no-wikidata"}).text.strip()

                while height[-1] != ']' and not height[-1].isnumeric():
                    height = height[:len(height) - 1]

                if height[-1] == ']':
                    ind = height.index('[')
                    height = height[:ind]

                player_data['height'] = int(height)
            elif line_type_text == 'Позиция':
                pos = row.find('a').text
                player_data['position'] = pos
            elif line_type_text == 'Клуб':
                club = row.find("span", {"class": "no-wikidata"}).text.strip(" ")
                player_data['current_club'] = club
            elif line_type_text == 'Клубная карьера':
                club_career_ind = rows.index(row)
            elif line_type_text == 'Национальная сборная':
                national_team_career_ind = rows.index(row)
            elif line_type_text == 'Международные медали':
                last_needed_row_ind = rows.index(row)

        #   Procceed club career
        for i in range(club_career_ind + 1, national_team_career_ind, 1):
            right_td = rows[i].find_all('td')[-1]
            text = right_td.text.strip()

            matches, goals = text.split(' ')
            goals = goals[1:-1]

            player_data["club_caps"] += int(matches)

            #   Для пропущенных голов для вратарей
            if player_data["position"] == "вратарь":
                if goals != '0' and goals != '?':
                    player_data['club_conceded'] += int(goals[1:])
            else:
                player_data["club_scored"] += int(goals)

        #   Procedd national career
        for i in range(last_needed_row_ind - 1, national_team_career_ind, -1):
            tds = rows[i].find_all("td")

            if len(right_td) == 0:
                continue

            right_td = tds[-1]
            team = tds[1].text.strip()

            player_data['national_team'] = team
            text = right_td.text.strip()

            matches, goals = text.split(" ")
            goals = goals[1:-1]

            player_data["national_caps"] += int(matches)

            #   Для пропущенных голов для вратарей
            if player_data["position"] == "вратарь":
                if goals != "0" and goals != "?":
                    player_data["national_conceded"] += int(goals[1:])
            else:
                player_data["national_scored"] += int(goals)

            break

        #   Check info in detail table

        if data.find(id="Клубная_статистика") is not None:
            tables = data.find_all("table", {"class": "wikitable"})

            for table in tables:
                last_row = table.find_all('tr')[-1]
                cols = last_row.find_all('td')

                if len(cols) != 0 and cols[0].text.strip() == 'Всего за карьеру':
                    if player_data["position"] == "вратарь":
                        pass
                    else:
                        matches = int(cols[-2].text.strip())
                        goals = int(cols[-1].text.strip())

                        if player_data['club_caps'] < matches:
                            player_data["club_caps"] = matches
                        if player_data['club_scored'] < goals:
                            player_data["club_scored"] = goals

        if data.find(id='Статистика_в_сборной') is not None:
            tables = data.find_all("table", {"class": "wikitable"})

            for table in tables:
                last_row = table.find_all("tr")[-1]
                cols = last_row.find_all("th")

                if len(cols) != 0 and cols[0].text.strip() == "Итого":
                    if player_data["position"] == "вратарь":
                        pass
                    else:
                        matches = int(cols[1].text.strip())
                        goals = int(cols[2].text.strip())

                        if player_data["national_caps"] < matches:
                            player_data["national_caps"] = matches
                        if player_data["national_scored"] < goals:
                            player_data["national_scored"] = goals

        return player_data, []
