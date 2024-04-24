import logging
import re
from datetime import datetime
from urllib.parse import unquote, urljoin

from runner import Item


class Parser:
    # Все селекторы - css
    TEAM_SELECTOR = 'table.standard tr td:nth-child(1) > a'
    PLAYER_SELECTOR = 'tr > td:nth-child(3) > a[href]'

    # Информация о футболисте
    INFOBOX_SELECTOR = 'table.infobox[data-name="Футболист"]'
    HEIGHT_SELECTOR = 'span[data-wikidata-property-id="P2048"]'
    POSITION_SELECTOR = '[data-wikidata-property-id="P413"]'

    TABLE_SELECTOR = 'table > tbody'
    # селектор для последнего столбца (если смотерть в контексте использования,
    # то это в таблице, где сработал селектор HEAD_TABLE_SELECTOR и выполнились условия)
    TAIL_TABLE_SELECTOR = 'tr:last-child > th'
    SECOND_TRY_SELECTOR = 'tr:last-child > td'

    def __init__(self, domain='https://ru.wikipedia.org/'):
        self._logger = logging.getLogger('pasrer')
        self.DOMAIN = domain

    # ---------------------------------------------------------------------------------------

    def parse(self, item):
        choice = self.__make_choice(item.url)
        if choice == 'championship':
            result = self._parse_championship_page(item.content)
            self._logger.info(f'Scraped championship {unquote(item.url)}, count of items: {len(result)}')
            return result
        elif choice == 'team':
            result = self._parse_team_page(item.content)
            self._logger.info(f'Scraped team {unquote(item.url)}, count of items: {len(result)}')
            return result
        elif choice == 'player':
            result = self._parse_player_page(item.content, item.url)
            self._logger.info(f'Scraped player {unquote(item.url)}')
            return result

    @staticmethod
    def __make_choice(url):
        last = unquote(url).split('/')[-1].lower()
        if 'чемпионат' in last:
            return 'championship'
        elif 'сборная' in last:
            return 'team'
        else:
            return 'player'

    # ---------------------------------------------------------------------------------------

    def _parse_championship_page(self, soup):
        selected = soup.select(self.TEAM_SELECTOR)
        answer = self.__get_items(selected)
        return answer

    def _parse_team_page(self, soup):
        answer = []
        for table in self.__get_table_pointer(soup):
            selected = table.select(self.PLAYER_SELECTOR)
            answer.extend(self.__get_items(selected))

        return answer

    def _parse_player_page(self, soup, url):
        result = {
            'url': url
        }
        result.update(self.__get_player_name(url))
        result.update(self.__get_player_info(soup))
        if 'Жота' in result['name']:
            result['name'] = result['name'].reverse()
        return result

    # ---------------------------------------------------------------------------------------

    def __get_player_info(self, soup):
        infobox = soup.select_one(self.INFOBOX_SELECTOR)

        answer = {
            'height': self.__get_player_height(infobox),
            'position': self.__get_player_position(infobox),
            'current_club': self.__get_club_name(infobox),
            'national_team': self.__get_national_team(infobox),
            'birth': self.__get_birth(infobox)
        }

        caps_goals = self.__get_caps_and_goals(infobox, soup)
        answer.update({
            'club_caps': caps_goals['club_caps'],
            'national_caps': caps_goals['national_caps']
        })
        if answer['position'] == 'вратарь':
            answer.update({
                'club_conceded': caps_goals['club_goals'],
                'club_scored': 0,
                'national_conceded': caps_goals['national_goals'],
                'national_scored': 0
            })
        else:
            answer.update({
                'club_conceded': 0,
                'club_scored': caps_goals['club_goals'],
                'national_conceded': 0,
                'national_scored': caps_goals['national_goals']
            })

        return answer

    @staticmethod
    def __get_birth(infobox):
        birth = infobox.select_one('span.bday').text
        return int(datetime.strptime(birth, '%Y-%m-%d').timestamp())

    @staticmethod
    def __get_national_team(infobox):
        for th in infobox.select('tr > th'):
            if 'национальная сборная' in th.contents[0].text.lower():
                sibling = th.parent
                while sibling := sibling.find_next_sibling('tr'):
                    if ' (до ' in sibling.text:
                        continue
                    links = sibling.select('a[href]')
                    urls = list(map(lambda x: unquote(x.get('href')), links))
                    for url in urls:
                        name = url.split('/')[-1].replace('_', ' ')
                        if re.match(r'сборная .+ по футболу', name.lower()):
                            return name

    @staticmethod
    def __get_player_name(url):
        last = unquote(url).split('/')[-1]
        stop = last.find('(')
        if stop == -1:
            stop = len(last)
        clean_last = list(filter(bool, re.split(r'[\_\,]', last[:stop])))
        surname, name = clean_last[0], ' '.join(clean_last[1:])
        if not name:
            surname, name = name, surname
        return {
            'name': [surname, name]
        }

    def __get_player_height(self, infobox):
        try:
            height = infobox.select_one(self.HEIGHT_SELECTOR).contents[0].text.strip()
            height = height[:4] if ',' in height else height[:3]
            return float(height.replace(',', '.')) * 100 if ',' in height else int(height)
        except Exception:
            return None

    def __get_player_position(self, infobox):
        try:
            positions = []
            for node in infobox.select_one(self.POSITION_SELECTOR).contents:
                text = node.text.strip()
                if text:
                    positions.append(text)
            return ' '.join(positions)
        except Exception:
            return None

    @staticmethod
    def __get_club_name(infobox):
        for th in infobox.select('tr > th'):
            if th.text.lower().strip() == 'клуб':
                return th.find_next_sibling('td').text.strip()

    def __get_caps_and_goals(self, infobox, soup):
        club_infobox = self.__get_career_from_infobox(infobox, 'клубная карьера')
        club_page = self.__get_career_from_page(soup, 'клуб')

        national_infobox = self.__get_career_from_infobox(infobox, 'национальная сборная')
        national_page = self.__get_career_from_page(soup, 'сборная')

        return {
            'club_caps': max(club_infobox[0], club_page[0]),
            'club_goals': max(club_infobox[1], club_page[1]),
            'national_caps': max(national_infobox[0], national_page[0]),
            'national_goals': max(national_infobox[1], national_page[1])
        }

    def __get_career_from_infobox(self, infobox, s):
        '''
        s - какая именно карьера - клубная или в национальной сборной
        '''
        caps, goals = 0, 0
        for th in infobox.select('tr > th'):
            if s in th.contents[0].text.lower():
                sibling = th.parent
                while sibling := sibling.find_next_sibling('tr'):
                    if not sibling.has_attr('class'):
                        break
                    if ' (до ' in sibling.text:
                        continue
                    try:
                        tmp = self.__get_from_str(sibling.select_one('td:nth-child(3)').text.strip())
                        caps += int(tmp[0])
                        goals += int(tmp[1])
                    except Exception:
                        pass
        if goals < 0:
            goals *= -1
        return (caps, goals)

    def __get_career_from_page(self, soup, s):
        '''
        s - какая именно карьера - клубная или в национальной сборной
        '''
        def norma(n):
            if '?' in n:
                return 0
            return abs(int(n))

        def is_relevant_table(s):
            keywords = ['молодёжные клубы', 'национальная сборная', 'информация о клубе', 'общая информация', 'родился']
            return not any(map(lambda x: x in s, keywords))
        res = ('0', '0')
        for tbody in soup.select(self.TABLE_SELECTOR):
            splited = list(map(lambda x: x.text.lower().strip(), tbody.select('tr > th')))
            if s in splited and is_relevant_table(splited):
                # попали в таблицу клубной карьеры или сборной
                selected = tbody.select(self.TAIL_TABLE_SELECTOR)
                if not selected:
                    selected = tbody.select(self.SECOND_TRY_SELECTOR)
                row = list(map(lambda x: x.text.strip(), selected))
                nums = self.__get_from_str(row)
                try:
                    res = (nums[-2], nums[-1]) if 'сух' not in tbody.text.lower() else (nums[-3], nums[-2])
                except Exception:
                    pass
                break
        return tuple(map(norma, res))

    # ---------------------------------------------------------------------------------------

    @staticmethod
    def __get_table_pointer(soup):
        table_names = ['Текущий_состав', 'Игроки', 'Состав', 'Состав_сборной', 'Текущий_состав_сборной', 'Недавние_вызовы']
        tables = []
        for id in table_names:
            pointer = soup.find('span', id=id)
            if pointer:
                tables.append(pointer.parent.find_next_sibling('table'))
        return tables

    def __get_items(self, selected):
        urls = map(lambda x: x.get('href'), selected)
        urls = list(set(map(lambda x: urljoin(self.DOMAIN, x), urls)))
        items = list(map(lambda x: Item(url=x), urls))

        return items

    def check(self, s):
        if not s:
            return False
        if '?' in s:
            return True
        return s.isdigit() or s[1:].isdigit()

    def __get_from_str(self, s):
        if isinstance(s, str):
            s = re.split('[ ()/]', s)
        replaced = map(lambda x: re.sub(r'[—–−]', '-', x), s)
        filtered = list(filter(self.check, replaced))
        return filtered
