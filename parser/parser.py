from bs4 import BeautifulSoup
from runner import Item
from urllib.parse import urljoin
import re


class Parser:
    # all selectors are css selectors
    TEAM_SELECTOR = 'table.standard tr td:nth-child(1) > a'
    PLAYER_SELECTOR = 'table.wikitable.mw-datatable > tbody > tr > td:nth-child(3) > a[href]'
    DOMAIN = 'https://ru.wikipedia.org/'

    def _parse_championship_page(self, soup):
        selected_teams = soup.select(self.TEAM_SELECTOR)
        urls = map(lambda x: x.get('href'), selected_teams)
        urls_join_domain = list(map(lambda x: urljoin(self.DOMAIN, x), urls))
        team_items = list(map(lambda x: Item(url=x, status='team'), urls_join_domain))
        cleaned_answer = list(set(team_items))
        return cleaned_answer

    def _parse_team_page(self, soup):
        pointer = soup.find('span', id=re.compile('^Текущий_состав'))
        if not pointer:
            pointer = soup.find('span', id=re.compile('^Состав'))
        pointer = pointer.parent
        while not (pointer.name and pointer.name == 'table'):
            pointer = pointer.next_sibling

        selected_players = pointer.select('tbody tr tr:nth-child(3) > a')

        selected_players = list(set(soup.select(self.PLAYER_SELECTOR)))
        urls = map(lambda x: x.get('href'), selected_players)
        urls_join_domain = list(map(lambda x: urljoin(self.DOMAIN, x), urls))
        player_items = list(map(lambda x: Item(url=x, status='team'), urls_join_domain))
        cleaned_answer = list(set(player_items))
        return cleaned_answer

    def parse(self, item):
        soup = BeautifulSoup(item.content, 'html.parser')
        match item.status:
            case 'championship':
                return self._parse_championship_page(soup)
            case 'team':
                return self._parse_team_page(soup)


