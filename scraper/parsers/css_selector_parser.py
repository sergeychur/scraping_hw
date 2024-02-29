from urllib.parse import urljoin
from datetime import datetime
from logging import Logger
from bs4 import BeautifulSoup
import re

class NothingFinded(Exception):
    pass


class CssSelectorParser:
    _correct_teamtable_fileds = ['№', 'Позиция', 'Игрок', 'Дата рождения / возраст', 'Матчи', 'Голы', 'Клуб']

    def __init__(self, logger) -> None:
        self.logger = logger.getChild('CssSelectorParser')
        self.url2info_from_teampage = {}

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
        tables = self._find_tag_by_id(['Текущий_состав', 'Игроки']).parent.find_next_siblings(
            'table',
            attrs={'class': 'wikitable'}
        )
        urls = []
        tables = [table for table in tables if self._is_correct_team_table(table)]
        if not tables:
            raise NothingFinded("correct team tables not found")
        for table in tables:
            urls += self._urls_from_team_table(table, cur_page_url)
        return None, urls

    def _parse_player(self, soup, cur_page_url):
        info_from_teampage = self.url2info_from_teampage[cur_page_url]
        player_info = self._player_info(soup, cur_page_url)
        birth = int(datetime.strptime(soup.select_one(".bday").text, "%Y-%m-%d").timestamp())
        return {
            'url': cur_page_url,
            'name': [info_from_teampage['surname'], info_from_teampage['name']],
            'height': player_info['height'],
            'position': player_info['position'],
            'current_club': player_info['club'],
            'club_caps': player_info['club_caps'],
            'club_conceded': player_info['club_conceded'],
            'club_scored': player_info['club_scored'],
            'national_caps': player_info['national_caps'],
            'national_conceded': player_info['national_conceded'],
            'national_scored': player_info['national_scored'],
            'national_team': player_info['national_team'],
            'birth': birth
        }, []
    
    def _is_correct_team_table(self, table):
        fields = [th.text.strip() for th in table.tr.find_all('th')]
        need = self._correct_teamtable_fileds
        return fields[:len(need)] == need

    def _urls_from_team_table(self, table, cur_page_url):
        urls = []
        for row in table.find_all('tr')[1:]:
            link = row.select_one('td:nth-child(3)>a')
            if link is None:
                continue
            player_name, player_surname = self._get_player_name_surname(link['title'])
            url = urljoin(cur_page_url, link['href'])
            team_goals = abs(self._int_from_str(row.select_one('td:nth-child(6)').text))
            team_caps = int(row.select_one('td:nth-child(5)').text.strip())
            self.url2info_from_teampage[url] = {  # TODO: change
                'name': player_name,
                'surname': player_surname,
                'team_goals': team_goals,
                'team_caps': team_caps
            }
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
        result = {}
        card_info = self._info_from_player_card(soup)

        club_caps, club_goals = self._player_clubstat_from_stattable(soup, url)
        result['club_caps'] = max(club_caps, card_info.get('club_caps', 0))
        club_goals = max(abs(club_goals), card_info.get('club_goals', 0))
        if card_info['position'] == 'вратарь':
            result['club_conceded'] = club_goals
            result['club_scored'] = 0
        else:
            result['club_conceded'] = 0
            result['club_scored'] = club_goals

        result['national_caps'] = card_info.get('national_caps', 0)
        national_goals = card_info.get('national_goals', 0)
        if card_info['position'] == 'вратарь':
            result['national_conceded'] = national_goals
            result['national_scored'] = 0
        else:
            result['national_conceded'] = 0     
            result['national_scored'] = national_goals
        result['national_team'] = card_info['national_team']
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
                return 0, 0, ''
            national_team, team_finded = '', False
            games, goals = 0, 0
            tag = tag.find_next_sibling('tr')
            while tag is not None and tag.get('class'):
                teamname_td = tag.select_one('td:nth-child(2)')
                if not (national and '(' in teamname_td.text):
                    if national and not team_finded:
                        national_team = teamname_td.find_all('a')[-1]['title']
                        team_finded = True
                    gms, gls = get_games_goals(tag)
                    games += gms
                    goals += gls
                tag = tag.find_next_sibling('tr')
            return games, goals, national_team     

        result = {}
        table = soup.select_one(".ts-Спортивная_карьера-table")
        if table is None:
            raise NothingFinded('player card table not founded')
        result['height'] = self._get_player_height(table)
        result['position'] = self._get_position(table)
        result['club'] = soup.find(attrs={"data-wikidata-property-id":"P54"}).text.strip()
        
        club_games, club_goals, _ = aggregate_info(table, 'Клубная карьера')
        result['club_caps'] = club_games
        result['club_goals'] = club_goals

        national_games, national_goals, national_team = aggregate_info(table, 'Национальная сборная', national=True)
        result['national_caps'] = national_games
        result['national_goals'] = national_goals
        result['national_team'] = national_team
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
