from urllib.parse import urljoin, urlparse, unquote
from datetime import datetime
from logging import Logger
from players.player_storage import PlayerStorage
from bs4 import BeautifulSoup
import re


class NothingFinded(Exception):
    pass


class CssSelectorParser:
    _correct_teamtable_fileds = [
        {'№'}, 
        {'Позиция'}, 
        {'Игрок'}, 
        {'Дата рождения / возраст'}, 
        {'Матчи', 'Игры'}, 
        {'Голы'}, 
        {'Клуб'}
    ]

    def __init__(self, logger, player_storage) -> None:
        self.logger = logger.getChild('CssSelectorParser')
        self.player_storage = player_storage

    def parse(self, content, cur_page_url):
        soup = BeautifulSoup(content, 'html.parser')
        parsers = [self._parse_mainpage, self._parse_teampage, self._parse_player]
        err_mes = ''
        for parser in parsers:
            try:
                return parser(soup, cur_page_url)
            except (AttributeError, IndexError, NothingFinded) as e:
                err_mes += str(e) + ';'
                err = e
        raise NothingFinded("bad page, nothing founded;" + err_mes) from err

    def _parse_mainpage(self, soup, cur_page_url):
        table = soup.find(id="Квалифицировались_в_финальный_турнир").parent.find_next_sibling('table')
        urls = []
        for t in table.select('td:first-child>a'):
            urls.append(urljoin(cur_page_url, t['href']))
        return None, urls

    def _parse_teampage(self, soup, cur_page_url):
        table_names = ['Текущий_состав', 'Игроки', 'Состав', 'Состав_сборной']
        table = self._find_tag_by_id(soup, table_names).parent.find_next_sibling('table')
        next_table = table.find_next_sibling('table')
        if self._is_correct_team_table(next_table):
            tables = [table, next_table]
        else:
            tables = [table]
        teamname = unquote(urlparse(cur_page_url).path).split('/')[-1].replace('_', ' ')
        urls = []
        for table in tables:
            urls += self._urls_from_team_table(table, cur_page_url, teamname)
        return None, urls

    def _parse_player(self, soup, cur_page_url):
        player_info = self._player_info(soup, cur_page_url)
        birth = int(datetime.strptime(soup.select_one(".bday").text, "%Y-%m-%d").timestamp())
        player_info['birth'] = birth
        return self.player_storage.extend_player(cur_page_url, player_info), []
    
    def _is_correct_team_table(self, table):
        if table is None:
            return False
        fields = [th.text.strip() for th in table.tr.find_all('th')]
        need = self._correct_teamtable_fileds
        if len(fields) < len(need):
            return False
        for i in range(len(need)):
            if fields[i] not in need[i]:
                return False
        return True

    def _urls_from_team_table(self, table, cur_page_url, teamname):
        urls = []
        for row in table.find_all('tr')[1:]:
            link = row.select_one('td:nth-child(3)>a')
            if link is None:
                continue
            player_name, player_surname = self._get_player_name_surname(link['title'])
            url = urljoin(cur_page_url, link['href'])
            self.player_storage.add_player(
                url, 
                {
                    'name': player_name,
                    'surname': player_surname,
                    'national_team': teamname
                }
            )
            urls.append(url)
        return urls

    def _get_player_name_surname(self, text):
        idx = text.find('(')
        if idx != -1:
            text = text[:idx]

        if ',' in text:
            names = text.split(',')[::-1]
        else:
            names = text.split()
        if len(names) >= 2:
            return names[0].strip(), names[1].strip()
        return names[0].strip(), ""
    
    def _int_from_str(self, s, regstr = r'\d+'):
        """
        return int from s if it exists in else 0
        """
        s = re.search(regstr, s)
        if s is None:
            return 0
        return int(s.group())

    def _find_tag_by_id(self, soup, ids):
        for id in ids:
            result = soup.find(id=id)
            if result is not None:
                return result
        return None
    
    def _player_info(self, soup, url) -> dict:
        result = self._info_from_player_card(soup)

        club_caps, club_goals = self._player_clubstat_from_stattable(soup, url)
        result['club_caps'] = max(club_caps, result.get('club_caps', 0))

        club_goals = max(abs(club_goals), result.get('club_goals', 0))
        if result['position'] == 'вратарь':
            result['club_conceded'] = club_goals
            result['club_scored'] = 0
        else:
            result['club_conceded'] = 0
            result['club_scored'] = club_goals

        national_goals = result.get('national_goals', 0)
        if result['position'] == 'вратарь':
            result['national_conceded'] = national_goals
            result['national_scored'] = 0
        else:
            result['national_conceded'] = 0     
            result['national_scored'] = national_goals
        return result
    
    def _get_player_height(self, player_card):
        height_tag = player_card.find(attrs={"data-wikidata-property-id":"P2048"})
        if height_tag is None:
            return 0
        height = height_tag.contents[0].text.split()[0]
        return max(map(int, re.findall(r'\d+', height)))
    
    def _get_position(self, player_card):
        tag = player_card.find(attrs={"data-wikidata-property-id":"P413"})
        a_tags = tag.find_all('a')
        if len(a_tags) <= 1:
            return tag.text.lower().strip()
        positions = [tag.text.lower().strip() for tag in a_tags]
        return ' '.join(positions)
    
    def _info_from_player_card(self, soup):
        def get_games_goals(tag):
            values_str = tag.select_one('td:last-child').text.strip()
            gls_str = re.search(r'\(.*\)', values_str)
            if gls_str is None:
                gls = 0
            else:
                gls = self._int_from_str(gls_str.group())
            return self._int_from_str(values_str, r'^\d+'), gls

        def aggregate_info(table, text, national=False):
            tag = table.find(lambda tag: tag.name == "tr" and text in tag.text)
            if tag is None:
                return 0, 0
            games, goals = 0, 0
            tag = tag.find_next_sibling('tr')
            while tag is not None and tag.get('class'):
                teamname_td = tag.select_one('td:nth-child(2)')
                if not (national and '(' in teamname_td.text):
                    gms, gls = get_games_goals(tag)
                    games += gms
                    goals += gls
                tag = tag.find_next_sibling('tr')
            return games, goals     

        player_card = soup.select_one('[data-name="Футболист"]')
        if player_card is None:
            raise NothingFinded('player card not founded')
        result = {}
        result['height'] = self._get_player_height(player_card)
        result['position'] = self._get_position(player_card)
        result['current_club'] = player_card.find(attrs={"data-wikidata-property-id":"P54"}).text.strip()

        table = player_card.select_one(".ts-Спортивная_карьера-table")        
        club_games, club_goals = aggregate_info(table, 'Клубная карьера')
        result['club_caps'] = club_games
        result['club_goals'] = club_goals

        national_games, national_goals = aggregate_info(table, 'Национальная сборная', national=True)
        result['national_caps'] = national_games
        result['national_goals'] = national_goals
        return result
    
    def _player_clubstat_from_stattable(self, soup, url):
        result = self._find_tag_by_id(soup, ['Статистика_выступлений', 'Статистика'])
        if result is None:
            self.logger.warning(f'stattable not found: url={url}')
            return 0, 0
        table = result.parent.find_next_sibling('table')
        return self._club_games_goals_from_player_stattable(table)
    
    def _club_games_goals_from_player_stattable(self, table):
        last_row = table.select_one('tr:last-child')
        tags = last_row.find_all('td')
        if not tags or len(tags) < 2:
            last = table.select_one('tr:nth-child(2)').select_one('th:last-child').text.strip()
            tags = last_row.find_all('th')
            if last != 'Голы':
                tags = tags[:-1]
        club_caps, goals = tags[-2].text.strip(), tags[-1].text.strip()
        return self._int_from_str(club_caps), self._int_from_str(goals)


def for_test(url):
    import requests
    import logging
    content = requests.get(url).content
    soup = BeautifulSoup(content)
    parser = CssSelectorParser(logging.getLogger('Parser'), PlayerStorage())
    return parser, parser._parse_player(soup, url)