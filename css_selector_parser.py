from bs4 import BeautifulSoup
import calendar
import datetime as DT
from urllib.parse import urljoin, urlparse


class CssSelectorParser:
    def _get_domain(url):
        netloc = urlparse(url).netloc
        scheme = urlparse(url).scheme
        domain = scheme + "://" + netloc

        return domain

    def parse(self, content, current_url):
        netloc = urlparse(current_url).netloc
        scheme = urlparse(current_url).scheme
        domain = scheme + "://" + netloc
        self._domain = domain
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

            if country in ['Англия', 'Чехия']:
                s = '<span class="mw-headline" id="Текущий_состав_сборной">Текущий состав сборной</span>'
            elif country in ['Дания', 'Швейцария', 'Хорватия']:
                s = '<span class="mw-headline" id="Состав">Состав</span>'
            elif country == 'Сербия':
                s = '<span class="mw-headline" id="Состав_сборной">Состав сборной</span>'
            else:
                s = '<span class="mw-headline" id="Текущий_состав">Текущий состав</span>'

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
                all_web_links.append(self._domain + url.get("href"))

        return None, all_web_links

    def _team_parse(self, data):
        tables = data.find_all("table", {"class": "wikitable"})
        actual_web_links = []
        size = 1

        if data.find(id='Недавние_вызовы') != None:
            size = 2    

        for i in range(size):
            for row in tables[i].find_all('tr')[1:]:
                cols = row.find_all('td')

                if len(cols) == 0 or len(cols) == 1:
                    continue

                url = self._domain + cols[2].find("a").get("href")
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
                start = DT.datetime(int(year), int(month_num), int(day), 0, 0, 0)

                utc_tuple = start.utctimetuple()
                utc_timestamp = calendar.timegm(utc_tuple)

                player_data["birth"] = utc_timestamp
                player_data['birt_str'] = birth_str
            elif line_type_text == 'Рост':
                height = row.text.strip().split('\n')[2]
                res_height = ''
                height_ind = 0

                while height[height_ind].isnumeric():
                    res_height += height[height_ind]
                    height_ind += 1

                if res_height[-1] == "]":
                    ind = res_height.index("[")
                    res_height = res_height[:ind]

                player_data["height"] = int(res_height)
            elif line_type_text == 'Позиция':
                pos = row.find('td').text.strip()
                player_data['position'] = pos
            elif line_type_text == 'Клуб':
                club = row.find("span", {"class": "no-wikidata"}).text.strip(" ")
                player_data['current_club'] = club
            elif line_type_text == 'Клубная карьера':
                club_career_ind = rows.index(row)
            elif line_type_text == 'Национальная сборная':
                national_team_career_ind = rows.index(row)

        if national_team_career_ind == 0:
            national_team_career_ind = len(rows)

        #   Procceed club career
        for i in range(club_career_ind + 1, national_team_career_ind, 1):
            td = rows[i].find_all('td')

            if (len(td) != 3):
                break

            right_td = td[-1]
            text = right_td.text.strip()

            matches, goals = '', ''
            ind = 0

            while text[ind] != '(':
                matches += text[ind]
                ind += 1

            ind += 1

            while text[ind] != ')':
                goals += text[ind]
                ind += 1

            if matches.find('?') == -1:
                player_data["club_caps"] += int(matches)

            #   Для пропущенных голов для вратарей
            if player_data["position"] == "вратарь":
                if goals != '0' and goals.find('?') == -1:
                    if goals.find("/") != -1:
                        goals = goals[: goals.index("/")]
                    player_data['club_conceded'] += int(goals[1:])
            else:
                if goals.find('?') == -1:
                    if goals.find("/") != -1:
                        goals = goals[: goals.index("/")]
                    player_data["club_scored"] += int(goals)

            # if td[0].find("abbr") is not None:
            #     break

        #   Procedd national career
        if national_team_career_ind != 0:
            for i in range(national_team_career_ind + 1, len(rows)):
                tds = rows[i].find_all("td")

                if len(tds) != 3:
                    break

                if tds[-1].find('span', {'class': 'reference-text'}) is not None:
                    break

                right_td = tds[-1]
                text = right_td.text.strip()
                team = tds[1].find_all('a')[-1]['title'].strip()

                if team.find('(') != -1:
                    team = team[:team.index('(')].strip(' ')
                    player_data["national_team"] = team
                    continue
                elif team.find('-') != -1:
                    team = team[: team.index("-")]
                    player_data["national_team"] = team
                    continue

                player_data['national_team'] = team

                matches, goals = "", ""
                ind = 0

                while text[ind] != "(":
                    matches += text[ind]
                    ind += 1

                ind += 1

                while text[ind] != ")":
                    goals += text[ind]
                    ind += 1

                if matches.find('?') == -1:
                    player_data["national_caps"] = int(matches)

                #   Для пропущенных голов для вратарей
                if player_data["position"] == "вратарь":
                    if goals != "0" and goals.find("?") == -1:
                        if goals.find('/') != -1:
                            goals = goals[: goals.index("/")]
                        player_data["national_conceded"] = int(goals[1:])
                else:
                    if goals.find("?") == -1:
                        if goals.find("/") != -1:
                            goals = goals[: goals.index("/")]
                        player_data["national_scored"] = int(goals)

                # if td[0].find("abbr") is not None:
                #     break

        #   Check info in detail table

        tables = data.find_all("table")

        for table in tables:
            last_row = table.find_all('tr')[-1]
            cols_th = last_row.find_all('th')
            cols_td = last_row.find_all("td")
            cols = []

            if len(cols_td) > 0:
                cols = cols_td
            elif len(cols_th) > 0:
                cols = cols_th

            if len(cols) != 0 and cols[0].text.strip() in ["Всего за карьеру", "Всего"]:
                matches = int(cols[-2].text.strip())
                if player_data["club_caps"] < matches:
                    player_data["club_caps"] = matches

                if player_data["position"] == "вратарь":
                    goals = cols[-1].text.strip()
                    if not goals[0].isnumeric():
                        goals = goals[1:]
                    goals = int(goals)

                    if player_data["club_conceded"] < goals:
                        player_data["club_conceded"] = goals
                else:
                    goals = int(cols[-1].text.strip())

                    if player_data['club_scored'] < goals:
                        player_data["club_scored"] = goals

        #   National team stats
        if (
            data.find(id="Статистика_в_сборной") is not None
            or data.find(id="Матчи_за_сборную") is not None
        ):
            tables = data.find_all("table", {"class": "wikitable"})

            for table in tables:
                last_row = table.find_all("tr")[-1]
                cols = last_row.find_all("th")

                if len(cols) != 0 and cols[0].text.strip() in ["Итого"]:
                    if player_data["position"] == "вратарь":
                        matches = int(cols[1].text.strip())

                        goals = cols[2].text.strip()
                        if not goals[0].isnumeric():
                            goals = goals[1:]
                        goals = int(goals)

                        if player_data["national_caps"] < matches:
                            player_data["national_caps"] = matches
                        if player_data["national_conceded"] < goals:
                            player_data["national_conceded"] = goals
                    else:
                        matches = int(cols[1].text.strip())
                        goals = int(cols[2].text.strip())

                        if player_data["national_caps"] < matches:
                            player_data["national_caps"] = matches
                        if player_data["national_scored"] < goals:
                            player_data["national_scored"] = goals

        return player_data, []
