from urllib.parse import urljoin
from bs4 import BeautifulSoup


class CssSelectorParser:
    def parse(self, content: str, cur_page_url: str) -> tuple[str | None, list[str]]:
        soup = BeautifulSoup(content) 

        player_stat = soup.find(id='Статистика_выступлений')
        if player_stat is not None:
            return self.parse_player(player_stat.parent)

        teams = soup.find(id="Квалифицировались_в_финальный_турнир")
        if teams is not None:
            return None, self._parse_teams(teams.parent, cur_page_url)
        
        players = soup.find(id="Текущий_состав")
        if players is not None:
            return None, self._parse_players(players.parent, cur_page_url)
        
        return None, []
    
    def _parse_player(soup):
        player_stat = soup.find(id='Статистика_выступлений').parent
        stat_table = player_stat.find_next_sibling('table')

        surname, name = soup.select_one(".mw-page-title-main").text.split(', ')
        height = int(soup.find(attrs={"data-wikidata-property-id":"P2048"}).contents[0])
        position = soup.find(attrs={"data-wikidata-property-id":"P413"}).text.lower().strip()
        club = soup.find(attrs={"data-wikidata-property-id":"P54"}).text.strip()

        last_row = player_stat.select_one('tr:last-child')
        club_caps = int(last_row.select_one('td:nth-child(10)').text)
        if position == 'вратарь':
            club_conceded = int(last_row.select_one('td:nth-child(11)').text)
            club_scored = 0
        else:
            club_conceded = 0
            club_scored = int(last_row.select_one('td:nth-child(11)').text)
        



    
    def _parse_teams(teams_h, cur_page_url: str) -> list[str]:
        urls: list[str] = []
        table = teams_h.find_next_sibling('table')
        for t in table.select('td:first-child>a'):
            urls.append(urljoin(cur_page_url, t['href']))
        return urls
    
    def _parse_players(players_h, cur_page_url: str) -> list[str]:
        urls: list[str] = []
        table = players_h.find_next_sibling('table')
        for t in table.select('td:nth-child(3)>a'):
            urls.append(urljoin(cur_page_url, t['href']))
        return urls