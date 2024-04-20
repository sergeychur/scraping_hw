import logging
import re
from urllib.parse import unquote, urljoin

from runner import Item


class Parser:
    # Все селекторы - css
    TEAM_SELECTOR = 'table.standard tr td:nth-child(1) > a'
    PLAYER_SELECTOR = 'tr > td:nth-child(3) > a[href]'
    TITLE_SELECTOR = 'span[class="mw-page-title-main"]'

    DOMAIN = 'https://ru.wikipedia.org/'

    def __init__(self):
        self.logger = logging.getLogger('parser')

    # ---------------------------------------------------------------------------------------

    def parse(self, item):
        match self.__make_choice(item.content):
            case 'championship':
                return self._parse_championship_page(item.content)
            case 'team':
                self.logger.info(f'team: {item.url}')
                return self._parse_team_page(item.content)
            case 'player':
                # TODO try block (except - this is not player)
                return self._parse_player_page(item.content, item.url)
        return 1   # TODO clean

    def __make_choice(self, soup):
        title = soup.select_one(self.TITLE_SELECTOR).text.lower()
        if 'чемпионат' in title:
            return 'championship'
        elif 'сборная' in title:
            return 'team'
        else:
            return 'player'

    # ---------------------------------------------------------------------------------------

    def _parse_championship_page(self, soup):
        selected = soup.select(self.TEAM_SELECTOR)
        answer = self.__get_items(selected)
        return answer

    def _parse_team_page(self, soup):
        table = self.__get_table_pointer(soup)
        selected = table.select(self.PLAYER_SELECTOR)

        answer = self.__get_items(selected)

        return answer

    def _parse_player_page(self, soup, url):
        result = {
            'url': url
        }
        result.update(self.__get_player_name(url))
        result.update(self.__get_player_info(soup))
        return result

    # ---------------------------------------------------------------------------------------

    @staticmethod
    def __get_player_name(url):
        last = unquote(url).split('/')[-1].replace('_', ' ')
        clean_last = last[:last.find('(')].split(',')
        surname, name = clean_last[0], ' '.join(clean_last[1:]).strip()
        return {
            'name': [surname, name]
        }

    def __get_player_info(self, soup):
        answer = dict()
        infobox = soup.select_one('table.infobox[data-name="Футболист"]')

        try:
            height = infobox.select_one('span[data-wikidata-property-id="P2048"]').contents[0].text
            height = re.split('[- ]', height)[0]
            answer['height'] = int(height)
        except Exception:
            answer['height'] = None

        try:
            position = infobox.select_one('[data-wikidata-property-id="P413"]').text.strip()
            answer['position'] = ', '.join(position.split('\n'))
        except Exception:
            answer['position'] = None

        def get_relevant_info(elem):
            pass
        return answer

    @staticmethod
    def __get_table_pointer(soup):
        table_names = ['Текущий_состав', 'Игроки', 'Состав', 'Состав_сборной', 'Текущий_состав_сборной']
        for id in table_names:
            pointer = soup.find('span', id=id)
            if pointer:
                break
        table = pointer.parent.find_next_sibling('table')
        return table

    def __get_items(self, selected):
        urls = map(lambda x: x.get('href'), selected)
        urls = filter(lambda x: 'index.php' not in x, urls)  # delete not existed pages
        urls = list(set(map(lambda x: urljoin(self.DOMAIN, x), urls)))
        items = list(map(lambda x: Item(url=x), urls))

        return items
