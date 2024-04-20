import logging
from urllib.parse import urljoin

from runner import Item


class Parser:
    # Все селекторы - css
    TEAM_SELECTOR = 'table.standard tr td:nth-child(1) > a'
    PLAYER_SELECTOR = 'table.wikitable.mw-datatable > tbody > tr > td:nth-child(3) > a[href]'
    DOMAIN = 'https://ru.wikipedia.org/'

    def __init__(self):
        self.logger = logging.getLogger('parser')

    def parse(self, item):
        match self.__make_choice(item.content):
            case 'championship':
                return self._parse_championship_page(item.content)
            case 'team':
                self.logger.info(f'team: {item.url}')
                return self._parse_team_page(item.content)
            case 'player':
                # TODO try block (except - this is not player)
                return []
        return 1   # TODO clean

    def _parse_championship_page(self, soup):
        selected = soup.select(self.TEAM_SELECTOR)
        answer = self.__get_items(selected)
        return answer

    def _parse_team_page(self, soup):
        table = self.__get_table_pointer(soup)
        selected = table.select('tr > td:nth-child(3) > a[href]')

        answer = self.__get_items(selected)

        print(list(item.url for item in answer))
        return answer

    def _parse_player_page(self, soup):
        pass

    @staticmethod
    def __make_choice(soup):
        title = soup.select_one('span[class="mw-page-title-main"]').text.lower()
        if 'чемпионат' in title:
            return 'championship'
        elif 'сборная' in title:
            return 'team'
        else:
            return 'player'

    @staticmethod
    def __get_table_pointer(soup):
        table_names = ['Текущий_состав', 'Игроки', 'Состав', 'Состав_сборной']
        for id in table_names:
            pointer = soup.find('span', id=id)
            if pointer:
                break
        table = pointer.parent.find_next_sibling('table')
        return table

    def __get_items(self, selected):
        urls = map(lambda x: x.get('href'), selected)
        urls_join_domain = list(set(map(lambda x: urljoin(self.DOMAIN, x), urls)))
        items = list(map(lambda x: Item(url=x), urls_join_domain))

        return items
