from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup
import re


class CssSelectorParser:
    def __init__(self) -> None:
        self.url2national_team: dict[str, str] = {}

    def parse(self, content: str, cur_page_url: str) -> tuple[dict | None, list[str]]:
        soup = BeautifulSoup(content)
        parsers = [self._parse_teams, self._parse_players, self._parse_player]
        for parser in parsers:
            try:
                return parser(soup, cur_page_url)
            except (AttributeError, IndexError):
                pass
        return None, []
    
    def _parse_player(self, soup, cur_page_url: str) -> tuple[dict[str], list[str]]:
        player_stat = soup.find(id='Статистика_выступлений').parent

        surname, name = soup.select_one(".mw-page-title-main").text.split(', ')
        height = int(soup.find(attrs={"data-wikidata-property-id":"P2048"}).contents[0])
        position = soup.find(attrs={"data-wikidata-property-id":"P413"}).text.lower().strip()
        club = soup.find(attrs={"data-wikidata-property-id":"P54"}).text.strip()

        last_row = player_stat.find_next_sibling('table').select_one('tr:last-child')
        club_caps = int(last_row.select_one('td:nth-child(10)').text)
        if position == 'вратарь':
            club_conceded = abs(int(last_row.select_one('td:nth-child(11)').text))
            club_scored = 0
        else:
            club_conceded = 0
            club_scored = abs(int(last_row.select_one('td:nth-child(11)').text))

        national_stat_txt = soup.select_one("#Матчи_за_сборную").parent.find_next_sibling("p").text
        numbers = re.findall(r'\d+', national_stat_txt)
        national_caps = int(numbers[0])
        if position == 'вратарь':
            national_conceded = int(numbers[1])
            national_scored = 0
        else:
            national_conceded = 0     
            national_scored = int(numbers[1])
        
        national_team = self.url2national_team[cur_page_url]
        birth = int(datetime.strptime(soup.select_one(".bday").text, "%Y-%m-%d").timestamp())

        return {
            'url': cur_page_url,
            'name': [surname, name],
            'height': height,
            'position': position,
            'current_club': club,
            'club_caps': club_caps,
            'club_conceded': club_conceded,
            'club_scored': club_scored,
            'national_caps': national_caps,
            'national_conceded': national_conceded,
            'national_scored': national_scored,
            'national_team': national_team,
            'birth': birth
        }, []

    
    def _parse_teams(self, soup, cur_page_url: str) -> tuple[None, list[str]]:
        table = soup.find(id="Квалифицировались_в_финальный_турнир").parent.find_next_sibling('table')

        urls: list[str] = []
        for t in table.select('td:first-child>a'):
            urls.append(urljoin(cur_page_url, t['href']))
        return None, urls
    
    def _parse_players(self, soup, cur_page_url: str) -> tuple[None, list[str]]:
        table = soup.find(id="Текущий_состав").parent.find_next_sibling('table')
        team_name = soup.select_one('.mw-page-title-main').text

        urls: list[str] = []
        for t in table.select('td:nth-child(3)>a'):
            url = urljoin(cur_page_url, t['href'])
            self.url2national_team[url] = team_name
            urls.append(url)
        return None, urls