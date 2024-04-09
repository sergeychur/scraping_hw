from bs4 import BeautifulSoup
import calendar
import datetime as DT
from urllib.parse import urljoin, urlparse


class CssSelectorParser:
    def parse(self, content, current_url):
        netloc = urlparse(current_url).netloc
        scheme = urlparse(current_url).scheme
        domain = scheme + "://" + netloc
        self._domain = domain
        soup = BeautifulSoup(content, "html.parser")
        table = soup.select_one("table.infobox")

        result = None
        urls = []

        if table is None:
            raise Exception("404")

        table = table.attrs.get("data-name")

        if "Соревнование футбольных сборных" in table:
            result, urls = self._main_page_parse(soup)
        elif "Сборная страны по футболу" in table:
            #   delete all unnecessary html code before needed table with current team
            s = ""

            country = (
                soup.find("table", {"class": "infobox"})
                .find("tr")
                .find("th")
                .text.strip(" \n\r")
            )

            if country in ["Англия", "Чехия"]:
                s = '<span class="mw-headline" id="Текущий_состав_сборной">Текущий состав сборной</span>'
            elif country in ["Дания", "Швейцария", "Хорватия"]:
                s = '<span class="mw-headline" id="Состав">Состав</span>'
            elif country == "Сербия":
                s = '<span class="mw-headline" id="Состав_сборной">Состав сборной</span>'
            elif country == "Украина":
                s = '<span class="mw-headline" id="Состав">Состав</span>'
            else:
                s = '<span class="mw-headline" id="Текущий_состав">Текущий состав</span>'

            soup = BeautifulSoup(
                content.decode()[content.decode().find(s) :].encode(), "html.parser"
            )
            result, urls = self._team_parse(soup)
        elif "Футболист" in table:
            result, urls = self._player_parse(soup, current_url)

        return result, urls

    def _main_page_parse(self, data):
        """Find table with all teams that will participate, find all links in row and take the last that goes to country team page"""

        team_table = data.find("table", {"class": "standard sortable"})
        all_web_links = []

        for row in team_table.find_all("tr")[1:]:
            col = row.find("td")
            url = col.select("a")[-1]

            if url is not None:
                all_web_links.append(self._domain + url.get("href"))

        return None, all_web_links

    def _team_parse(self, data):
        tables = data.find_all("table", {"class": "wikitable"})
        actual_web_links = []
        size = 1

        if data.find(id="Недавние_вызовы") != None:
            size = 2

        for i in range(size):
            for row in tables[i].find_all("tr")[1:]:
                cols = row.find_all("td")

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
            "url": current_url,
            "name": "",
            "height": 0,
            "position": "",
            "current_club": "",
            "club_caps": 0,
            "club_conceded": 0,
            "club_scored": 0,
            "national_caps": 0,
            "national_conceded": 0,
            "national_scored": 0,
            "national_team": "",
        }

        infobox = data.find("table", {"class": "infobox"})
        rows = infobox.find_all("tr")

        #   Name
        name = rows[0].find("div", {"class": "label"}).text.strip().split(" ")

        if len(name) > 2:
            name = [" ".join([name[0], name[1]]), name[2]]

        player_data["name"] = name[::-1]

        for row in rows[1:]:
            line_type = row.find("th")

            if line_type is None:
                continue

            line_type_text = self._standart_text_data(line_type.text.strip())

            if line_type_text == "Родился":
                bday = row.find("span", {"class": "nowrap"}).find_all("a")
                bday[0] = bday[0].text
                bday[1] = bday[1].text

                months = [
                    "января",
                    "февраля",
                    "марта",
                    "апреля",
                    "мая",
                    "июня",
                    "июля",
                    "августа",
                    "сентября",
                    "октября",
                    "ноября",
                    "декабря",
                ]
                day, month = bday[0].split(" ")
                year = bday[1]
                month_num = months.index(month) + 1

                birth_str = f"{year}.{month_num}.{day}"
                start = DT.datetime(int(year), int(month_num), int(day), 0, 0, 0)

                utc_tuple = start.utctimetuple()
                utc_timestamp = calendar.timegm(utc_tuple)

                player_data["birth"] = utc_timestamp
                player_data["birt_str"] = birth_str
            elif line_type_text == "Рост":
                height = row.text.strip().split("\n")[2]
                res_height = ""
                height_ind = 0

                while height[height_ind].isnumeric():
                    res_height += height[height_ind]
                    height_ind += 1

                if res_height[-1] == "]":
                    ind = res_height.index("[")
                    res_height = res_height[:ind]

                player_data["height"] = int(res_height)
            elif line_type_text == "Позиция":
                pos = row.find("td").text.strip()
                player_data["position"] = pos
            elif line_type_text == "Клуб":
                club = row.find("span", {"class": "no-wikidata"}).text.strip(" ")
                player_data["current_club"] = club
            elif line_type_text == "Клубная карьера":
                club_career_ind = rows.index(row)
            elif line_type_text == "Национальная сборная":
                national_team_career_ind = rows.index(row)

        if national_team_career_ind == 0:
            national_team_career_ind = len(rows)

        #   Procceed club career
        for i in range(club_career_ind + 1, national_team_career_ind, 1):
            td = rows[i].find_all("td")

            if len(td) != 3:
                break

            right_td = td[-1]
            text = right_td.text.strip()

            matches, goals = "", ""
            ind = 0

            while text[ind] != "(":
                matches += text[ind]
                ind += 1

            ind += 1

            while text[ind] != ")":
                goals += text[ind]
                ind += 1

            if matches.find("?") == -1:
                player_data["club_caps"] += int(matches)

            #   Для пропущенных голов для вратарей
            if player_data["position"] == "вратарь":
                if goals != "0" and goals.find("?") == -1:
                    if goals.find("/") != -1:
                        goals = goals[: goals.index("/")]
                    player_data["club_conceded"] += int(goals[1:])
            else:
                if goals.find("?") == -1:
                    if goals.find("/") != -1:
                        goals = goals[: goals.index("/")]
                    player_data["club_scored"] += int(goals)

            # if td[0].find("abbr") is not None:
            #     break

        #   Procedd national career

        if national_team_career_ind != 0:
            national_teams = []
            national_matches = []
            national_goals = []
            national_conceded = []

            for i in range(national_team_career_ind + 1, len(rows)):
                tds = rows[i].find_all("td")

                if len(tds) != 3:
                    break

                if tds[-1].find("span", {"class": "reference-text"}) is not None:
                    break

                right_td = tds[-1]
                text = right_td.text.strip()

                team_line = tds[1].find_all("a")[-1]["title"].strip()
                team_line_text = tds[1].find_all("a")[-1].text.strip()

                if (
                    len(team_line) > 0
                    and team_line.find("Флаг") == -1
                    and team_line.find("(") == -1
                    and team_line_text.find("(") == -1
                ):
                    national_teams.append(team_line)

                    matches, goals = "", ""
                    ind = 0

                    while text[ind] != "(":
                        matches += text[ind]
                        ind += 1

                    ind += 1

                    while text[ind] != ")":
                        goals += text[ind]
                        ind += 1

                    if matches.find("?") == -1:
                        national_matches.append(int(matches))
                        # player_data["national_caps"] = int(matches)

                    #   Для пропущенных голов для вратарей
                    if player_data["position"] == "вратарь":
                        if goals.find("?") != -1:
                            national_conceded.append(0)
                        else:
                            if goals.find("/") != -1:
                                goals = goals[: goals.index("/")]
                            # player_data["national_conceded"] = int(goals[1:])
                            if not goals[0].isnumeric():
                                national_conceded.append(int(goals[1:]))
                            else:
                                national_conceded.append(int(goals))

                    else:
                        if goals.find("?") != -1:
                            national_goals.append(0)
                        else:
                            if goals.find("/") != -1:
                                goals = goals[: goals.index("/")]
                            # player_data["national_scored"] = int(goals)
                            national_goals.append(int(goals))

            selected_national_teams = []
            selected_national_goals = []
            selected_national_matches = []
            selected_national_conceded = []

            # print(national_teams)
            # print(national_matches)
            # print(national_goals)
            # print(national_conceded)

            for i in range(len(national_teams)):
                if not (
                    national_teams[i].find("(") != -1
                    or national_teams[i].find("Молодёжная") != -1
                    or national_teams[i].find("Олимпийская") != -1
                    or national_teams[i].find("en:") != -1
                ):
                    selected_national_teams.append(national_teams[i])
                    selected_national_matches.append(national_matches[i])

                    if player_data["position"] == "вратарь":
                        selected_national_conceded.append(national_conceded[i])
                    else:
                        selected_national_goals.append(national_goals[i])

            if len(selected_national_teams) > 0:
                restricted_national_teams = [
                    "Сборная Каталонии по футболу",
                    "Сборная Арубы по футболу",
                    "Сборная ДР Конго по футболу",
                    "Сборная Ирландии по футболу",
                    "Сборная Северной Македонии по футболу",
                ]

                for restricted_team in restricted_national_teams:
                    if restricted_team in selected_national_teams:
                        ind = selected_national_teams.index(restricted_team)

                        selected_national_teams.pop(ind)
                        selected_national_matches.pop(ind)

                        if player_data["position"] == "вратарь":
                            selected_national_conceded.pop(ind)
                        else:
                            selected_national_goals.pop(ind)

                player_data["national_caps"] = selected_national_matches[0]
                player_data["national_team"] = selected_national_teams[0]

                if player_data["position"] == "вратарь":
                    player_data["national_conceded"] = selected_national_conceded[0]
                else:
                    player_data["national_scored"] = selected_national_goals[0]
            else:
                raise Exception("Player has not played for national team yet")

        #   Check info in detail table

        tables = data.find_all("table")

        for table in tables:
            last_row = table.find_all("tr")[-1]
            cols_th = last_row.find_all("th")
            cols_td = last_row.find_all("td")
            cols = []

            if len(cols_td) > len(cols_th):
                cols = cols_td
            else:
                cols = cols_th

            if (
                len(cols_th) != 0
                and cols_th[0].text.strip() in ["Всего за карьеру", "Всего"]
            ) or (
                len(cols_td) != 0
                and cols_td[0].text.strip() in ["Всего за карьеру", "Всего"]
            ):
                matches = cols[-2].text.strip()
                goals = 0
                is_diff_location = False

                if not matches[0].isnumeric():
                    goals = int(matches[1:])
                    matches = int(cols[-3].text.strip())
                    is_diff_location = True
                else:
                    matches = int(cols[-2].text.strip())

                if player_data["club_caps"] < matches:
                    player_data["club_caps"] = matches

                if player_data["position"] == "вратарь":
                    if not is_diff_location:
                        goals = cols[-1].text.strip()
                        if not goals[0].isnumeric() and goals != "?":
                            goals = goals[1:]
                        elif goals == "?":
                            goals = "0"
                        goals = int(goals)

                    if player_data["club_conceded"] < goals:
                        player_data["club_conceded"] = goals
                else:
                    goals = int(cols[-1].text.strip())

                    if player_data["club_scored"] < goals:
                        player_data["club_scored"] = goals

                break

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
