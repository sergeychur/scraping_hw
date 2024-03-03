from bs4 import BeautifulSoup
from runner import Item


class Parser:
    # all selectors are css selectors
    TEAM_SELECTOR = 'table.standard tr td:nth-child(1) a[href]'
    PLAYER_SELECTOR = 'table.wikitable.mw-datatable > tbody > tr > td:nth-child(3) > a'

    def _parse_championship(self, soup):
        team_urls = soup.select(self.TEAM_SELECTOR)


    def parse(self, item):
        if item.status == 'championship':
            self._parse_championship

