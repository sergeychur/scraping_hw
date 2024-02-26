from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup
import re


class NothingFinded(Exception):
    pass


class CssSelectorParser:
    def __init__(self) -> None:
        self.url2info_from_teampage: dict[str, dict] = {}

    def parse(self, content: str, cur_page_url: str) -> tuple[dict | None, list[str]]:
        soup = BeautifulSoup(content, 'html.parser')
        parsers = [self._parse_teams, self._parse_players, self._parse_player]
        for parser in parsers:
            try:
                return parser(soup, cur_page_url)
            except (AttributeError, IndexError):
                pass
        raise NothingFinded

    def _parse_player(self, soup, cur_page_url: str) -> tuple[dict[str], list[str]]:
        info_from_teampage = self.url2info_from_teampage[cur_page_url]

        name, surname = soup.select_one('.ts_Спортсмен_имя').text.split()
        height = int(soup.find(attrs={"data-wikidata-property-id":"P2048"}).contents[0].text.split()[0])
        position = soup.find(attrs={"data-wikidata-property-id":"P413"}).text.lower().strip()
        club = soup.find(attrs={"data-wikidata-property-id":"P54"}).text.strip()
        stat = self._player_stat(soup, position, info_from_teampage)
        national_team = info_from_teampage['team_name']
        birth = int(datetime.strptime(soup.select_one(".bday").text, "%Y-%m-%d").timestamp())

        return {
            'url': cur_page_url,
            'name': [surname, name],
            'height': height,
            'position': position,
            'current_club': club,
            'club_caps': stat['club_caps'],
            'club_conceded': stat['club_conceded'],
            'club_scored': stat['club_scored'],
            'national_caps': stat['national_caps'],
            'national_conceded': stat['national_conceded'],
            'national_scored': stat['national_scored'],
            'national_team': national_team,
            'birth': birth
        }, []
    
    def _player_stat(self, soup, position: str, info_from_teampage: dict) -> dict:
        result = {}
        player_stat = self._player_stat_from_player(soup)

        club_caps, club_goals = self._player_clubstat_from_table(soup)
        result['club_caps'] = max(club_caps, player_stat.get('club_caps', 0))
        club_goals = max(abs(club_goals), player_stat.get('club_goals', 0))
        if position == 'вратарь':
            result['club_conceded'] = club_goals
            result['club_scored'] = 0
        else:
            result['club_conceded'] = 0
            result['club_scored'] = club_goals

        national_caps, national_goals = self._national_games_goals_from_player(soup)
        result['national_caps'] = max(
            national_caps, 
            info_from_teampage['team_caps'], 
            player_stat.get('national_caps', 0)
        )
        national_goals = max(
            national_goals,
            info_from_teampage['team_goals'],
            player_stat.get('national_goals', 0)
        )
        if position == 'вратарь':
            result['national_conceded'] = national_goals
            result['national_scored'] = 0
        else:
            result['national_conceded'] = 0     
            result['national_scored'] = national_goals
        return result
    
    def _player_stat_from_player(self, soup) -> dict[str, int]:
        def aggregate_stats(table, text) -> tuple[int, int]:
            tag = table.find(lambda tag: tag.name == "tr" and text in tag.text)
            if tag is None:
                return 0, 0
            games, goals = 0, 0
            tag = tag.find_next_sibling('tr')
            while tag is not None and tag.get('class'):
                gms, gls  = map(int, re.findall(r'\d+', tag.select_one('td:last-child').text))
                games += gms
                goals += gls
                tag = tag.find_next_sibling('tr')
            return games, goals     

        result = {}
        table = soup.select_one(".ts-Спортивная_карьера-table")
        if table is None:
            return result
        
        club_games, club_goals = aggregate_stats(table, 'Клубная карьера')
        result['club_caps'] = club_games
        result['club_goals'] = club_goals

        national_games, national_goals = aggregate_stats(table, 'Национальная сборная')
        result['national_caps'] = national_games
        result['national_goals'] = national_goals
        return result
            
    def _player_clubstat_from_table(self, soup) -> tuple[int, int]:
        ids = ['Статистика_выступлений', 'Статистика']
        # TODO: add log not found
        for id in ids:
            result = soup.find(id=id)
            if result is not None:
                break
        if result is None:
            return 0, 0
        table = result.parent.find_next_sibling('table')
        return self._club_games_goals_from_player_table(table)
    
    def _club_games_goals_from_player_table(self, table) -> tuple[int, int]:
        last_row = table.select_one('tr:last-child')
        tags = last_row.find_all('td')
        if not tags:
            tags = last_row.find_all('th')
        club_caps, goals = tags[-2].text.strip(), tags[-1].text.strip()

        if club_caps.isdigit():
            club_caps = int(club_caps)
        else:
            club_caps = 0
        return club_caps, int(goals)
    
    def _national_games_goals_from_player(self, soup) -> tuple[int, int]:
        stat = soup.select_one("#Матчи_за_сборную")
        if stat is None:
            return 0, 0
        stat = stat.parent.find_next_sibling("p").text
        numbers = re.findall(r'\d+', stat)
        return int(numbers[0]), int(numbers[1])
    
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
        for row in table.find_all('tr')[1:]:
            link = row.select_one('td:nth-child(3)>a')
            if link is None:
                continue
            url = urljoin(cur_page_url, link['href'])
            team_goals = abs(int(re.search(r'\d+', row.select_one('td:nth-child(6)').text).group()))
            team_caps = int(row.select_one('td:nth-child(5)').text.strip())

            self.url2info_from_teampage[url] = {
                'team_name': team_name,
                'team_goals': team_goals,
                'team_caps': team_caps
            }
            urls.append(url)
        return None, urls
    


"""
import requests
url = ''
content = requests.get(url).content
soup = BeautifulSoup(content)
parser = CssSelectorParser()

def get_soup(url):
    return BeautifulSoup(requests.get(url).content)
"""