from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime, timezone

class PlayerParser:
    def __init__(self, logger):
        self._logger = logger
        self.team_players = dict()
        self.national_teams = dict()
        self.months_translation = {
            "января": 1,
            "февраля": 2,
            "марта": 3,
            "апреля": 4,
            "мая": 5,
            "июня": 6,
            "июля": 7,
            "августа": 8,
            "сентября": 9,
            "октября": 10,
            "ноября": 11,
            "декабря": 12
        }

    def parse(self, content, current_page_link=None):
        soup = BeautifulSoup(content, "html.parser")
        main_table = soup.select_one("table.infobox")
        if main_table is None:
            raise Exception("Table not found")
        main_table = main_table.attrs.get("data-name")
        if "Соревнование" in main_table:
            next = self._parse_main_page(soup, current_page_link)
            return None, next
        elif "Сборная" in main_table:
            next = self._parse_team(soup, current_page_link)
            return None, next
        elif "Футболист" in main_table:
            result = self._parse_player(soup, current_page_link)
            return result, []
        return None, []

    def _parse_main_page(self, page, current_page_link):
        next_urls = {}
        for element in page.select("td[style] a[href][title]"):
            if "Сборная" in element["title"] and element["title"] not in list(self.national_teams.values()):
                next_urls[urljoin(current_page_link, element["href"])] = element["title"]
        self.national_teams.update(next_urls)
        return list(next_urls.keys())

    def _parse_team(self, page, current_page_link):

        team_name = self.national_teams[current_page_link]
        players = []
        tables = []

        for label in (r"[С,с]остав", r"Недавние_вызовы"):
            table = page.find(attrs={"id": re.compile(label)})
            if table is None:
                continue
            table = table.find_parent(re.compile(r"h\d"))
            tables.append(table.find_next_sibling("table"))

        for table in tables:
            rows = table.select("tr")
            for row in rows[1:]:
                elements = row.select("td")
                if len(elements) not in [7, 8]:
                    continue
                player = urljoin(current_page_link, elements[2].select_one("a")["href"])
                players.append(player)
                self.team_players[player] = team_name
        return players

    def _find_table(self, page, label_text):
        target_element = page.find(attrs={'id': label_text})
        if target_element is None:
            return None
        target_element = target_element.find_parent(re.compile(r'h\d'))
        table = target_element.find_next_sibling('table')
        return table

    def _parse_player(self, page, current_page_link):
        main_table = page.select_one('table.infobox')
        base_data = self._parse_main_table(main_table, current_page_link)
        table = self._find_table(page, re.compile(r'Клубная'))
        if table is None:
            return base_data
        rows = table.select('tr')
        header = rows[0].select("th")
        header = [element.text.strip("\n").strip() for element in header]
        if not any(
            [
                (
                    "Лига" == element or
                    "Кубок лиги" == element or
                    "Чемпионат" == element or
                    "Кубки" == element or
                    "Кубок" == element or
                    "Клуб" == element
                ) and "УЕФА" not in element
                for element in header
            ]
        ):
            return base_data
        last_row = rows[-1].select("td")
        if len(last_row) <= 2:
            last_row = rows[-1].select("th")
        win_matches = int(last_row[-2].text.replace('−', '-').replace("\n", "").replace("−", "-"))
        goals = int(last_row[-1].text.replace("\n", "").replace("−", "-"))
        if goals < 0:
            base_data["club_conceded"] = max(abs(goals), base_data["club_conceded"])
        else:
            base_data["club_scored"] = max(abs(goals), base_data["club_scored"])
        base_data["club_caps"] = max(win_matches, base_data["club_caps"])
        return base_data
    

    def _parse_name(self, table):
        name = table.select_one("div div.label").text.split()[::-1]
        if len(name) > 2:
            name[1] = " ".join(name[1:][::-1])
            name = name[:2]
        return name

    def _parse_birth_date(self, table, link):
        birth_date = table.find(text=re.compile(r"Родился\s?"))
        if birth_date is None:
            self._logger.error(f"No age info for {link}")
            return None
        row = birth_date.find_parent("tr")
        age = row.select("span.nowrap a")
        date = " ".join([element.text for element in age[:2]])
        date_list = date.split()
        date_list[1] = self.months_translation[date_list[1]]
        day, month, year = date_list
        utc_seconds = datetime(int(year), month, int(day), tzinfo=timezone.utc).timestamp()
        return int(utc_seconds)

    def _parse_height(self, table, link):
        height = table.find(text=re.compile(r"Рост\s?"))
        if height is None:
            self._logger.warning(f"No height info for {link}")
            return None
        height = height.find_parent("tr")
        height = height.select_one("span").text
        numbers_list = [int(number) for number in re.findall(r"-?\d+\.?\d*", height)]
        return max(numbers_list)

    def _parse_position(self, table, link):
        position = table.find(text=re.compile(r"Позиция\s?"))
        if position is None:
            self._logger.error(f"No position info for {link}")
            return None
        position = position.find_parent("tr")
        position = position.select("td")[-1].text.strip("\n")
        return position

    def _parse_club(self, table, link):
        club = table.find(text=re.compile(r"Клуб\s?"))
        if club is None:
            self._logger.error(f"No club info for {link}")
            return None
        club = club.find_parent("tr")
        club = club.select("a")[-1].text
        return club


    def _parse_main_table(self, table, link):
        result = {
            "url": link,
            "name": self._parse_name(table),
            "birth": self._parse_birth_date(table, link),
            "height": self._parse_height(table, link),
            "position": self._parse_position(table, link),
            "current_club": self._parse_club(table, link),
        }
        result = self._parse_match_data(table, result, link)
        result["national_team"] = self.team_players.get(link, "Unknown")
        return result

    
    def _parse_match_data(self, table, result, link):
        match_table = table.select_one("table.ts-Спортивная_карьера-table")
        matches = match_table.select("tr")
        is_club_match = False
        is_national_match = False
        club_match_counter, national_match_counter = 0, 0
        missed_club_goal_counter, scored_club_goal_counter = 0, 0
        missed_national_goal_counter, scored_national_goal_counter = 0, 0
        for row in matches:
            probe = row.select_one("th")
            if probe is not None:
                if "Клубная карьера" in probe.text:
                    is_club_match = True
                    is_national_match = False
                elif "Национальная сборная" in probe.text:
                    is_club_match = False
                    is_national_match = True
                continue
            probe = row.select("td")
            if probe is None or len(probe) < 3:
                continue
            pattern = r"[−,-]?\d+"
            match = re.findall(pattern, probe[2].text)
            mathes_count = int(match[0] if len(match) > 0 else 0)
            goals_count = int(match[1].replace("−", "-") if len(match) == 2 else 0)
            national_team = None
            if is_club_match:
                club_match_counter += mathes_count
                if "вратарь" in result["position"]:
                    missed_club_goal_counter += abs(goals_count)
                else:
                    scored_club_goal_counter += goals_count
            elif is_national_match:
                national_team = probe[1].select("a")[-1]["title"]
                if "(до" in national_team or "(до" in probe[1].text or "Флаг" in national_team or "Молодёжная" in national_team or "Олимпийская сборная" in national_team:
                    continue
                national_match_counter += mathes_count
                if "вратарь" in result["position"]:
                    missed_national_goal_counter += abs(goals_count)
                else:
                    scored_national_goal_counter += goals_count
            else:
                self._logger.error(f"Row missing in main table for {link}")

        result["club_caps"] = club_match_counter
        result["club_conceded"] = missed_club_goal_counter
        result["club_scored"] = scored_club_goal_counter
        result["national_caps"] = national_match_counter
        result["national_conceded"] = missed_national_goal_counter
        result["national_scored"] = scored_national_goal_counter

        return result