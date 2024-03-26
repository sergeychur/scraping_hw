from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime


class CssSelectorParser:
    def __init__(self, logger):
        self._logger = logger
        self.comand_dict = dict()
        self.national_dict = dict()

    def parse(self, content, cur_page_url=None):
        soup = BeautifulSoup(content, 'html.parser')
        main_table = soup.select_one('table.infobox')
        if main_table is None:
            raise Exception('404')
        main_table = main_table.attrs.get('data-name')
        if 'Соревнование футбольных' in main_table:
            next = self._parse_main_page(soup, cur_page_url)
            return None, next
        elif 'Сборная' in main_table:
            next = self._parse_team(soup, cur_page_url)
            return None, next
        elif 'Футболист' in main_table:
            result = self._parse_player(soup, cur_page_url)
            return result, []
        return None, []

    def _parse_main_page(self, page_data, cur_page_url):
        next = [(urljoin(cur_page_url, elem['href']), elem['title'])
                for elem in page_data.select('td[style] a[href][title]')
                if 'Сборная' in elem['title']][:21]
        self.national_dict.update(dict(next))
        return [obj[0] for obj in next]

    def _find_table_use_sibling(self, page, label_text):
        target_element = page.find(attrs={'id': re.compile(label_text)})
        if target_element is None:
            return None
        target_element = target_element.find_parent(re.compile(r'h\d'))
        table = target_element.find_next_sibling('table')
        return table

    def _parse_team(self, page_data, cur_page_url):
        players = []
        team_name = self.national_dict[cur_page_url]
        tables = [self._find_table_use_sibling(page_data, text) for text in (r'[С,с]остав', r'Недавние_вызовы')]
        for table in tables:
            if table is None:
                continue
            rows = table.select('tr')
            for row in rows[1:]:
                elements = row.select('td')
                if len(elements) != 7 and len(elements) != 8:
                    continue
                player_link = elements[2].select_one('a')['href']
                players.append(urljoin(cur_page_url, player_link))
                self.comand_dict[players[-1]] = team_name
        return players


    def _parse_player(self, page_data, cur_page_url):

        #Извлечем основную таблицу, оттуда получим имя и фамилию
        main_table = page_data.select_one('table.infobox')
        base_data = self._parse_main_table(main_table, cur_page_url) # все нужные сведения об игроке отсюда получены, если всё хорошо



        #работа с таблицей матчев за сборную, здесь надо будет дальше уточнить все значения
        tables = page_data.select('tbody')

        # pattern_nationaltable = r'Матчи (.*?) за сборную Англии'
        # for table in tables:
        #     buf_result = table.find(text=re.compile(pattern_nationaltable))
        #     if buf_result is None:
        #         continue

        #club_signature = ['Выступление', 'Лига', 'Кубок', 'Кубок лиги', 'Еврокубки', 'Прочее', 'Итого']
        for table in tables:
            rows = table.select('tr')
            header = rows[0].select('th')
            if len(header) == 0:
                continue
            else:
                header = [obj.text.strip('\n').strip() for obj in header]
                flags = any([('Лига' == obj or
                              'Кубок лиги' == obj or
                              'Чемпионат' == obj or
                              'Кубки' == obj or
                              'Кубок' == obj or
                              'Клуб' == obj) and 'УЕФА' not in obj for obj in header])
                if not flags:
                    continue
                last_row = rows[-1].select('td')
                if len(last_row) <= 2:
                    last_row = rows[-1].select('th')
                matches_advanced = int(last_row[-2].text.replace('−', '-').replace('\n', '').replace('−', '-'))
                goals_advanced = int(last_row[-1].text.replace('\n', '').replace('−', '-'))
                if goals_advanced < 0:
                    base_data['club_conceded'] = max(abs(goals_advanced), base_data['club_conceded'])
                else:
                    base_data["club_scored"] = max(abs(goals_advanced), base_data["club_scored"])
                base_data['club_caps'] = max(matches_advanced, base_data['club_caps'])
                return base_data
        return base_data


    def _parse_main_table(self, table, url):
        result = {}
        name = table.select_one('div div.label').text
        result['name'] = name.split()[::-1]
        if len(result['name']) > 2:
            result['name'][1] = ' '.join(result['name'][1:][::-1])
            result['name'] = result['name'][:2]
        result['url'] = url
        probe_el = table.find(text=re.compile(r'Родился\s?'))
        if probe_el is None:
            self._logger.error(f'Не найден возраст для {url}')
        months_translation = {
            "января": 1,
            "февраля": 2,
            "марта": 3,
            "апреля": 4,
            "мая": 5,
            "июня": 6,
            "июля": 7,
            "августа": 8,
            "сентября": 9,
            "октября": 10,
            "ноября": 11,
            "декабря": 12
        }
        row = probe_el.find_parent('tr')
        age = row.select('span.nowrap a')
        date = ' '.join([obj.text for obj in age[:2]])
        date_list = date.split()
        date_list[1] = months_translation[date_list[1]]
        day, month, year = date_list
        utc_seconds = datetime(int(year), month, int(day)).timestamp()
        result['birth'] = int(utc_seconds)

        probe_el = table.find(text=re.compile(r'Рост\s?'))
        if probe_el is None:
            self._logger.warning(f'Не найден рост для {url}')
            result['height'] = '?'
        else:
            row = probe_el.find_parent('tr')
            height = row.select_one('span').text
            pattern = r'-?\d+\.?\d*'
            numbers_list = re.findall(pattern, height)
            numbers_list = [int(number) for number in numbers_list]
            result['height'] = max(numbers_list)

        probe_el = table.find(text=re.compile(r'Позиция\s?'))
        if probe_el is None:
            self._logger.error(f'Не найдена позиция для {url}')
        row = probe_el.find_parent('tr')
        position = row.select('td')[-1].text.strip('\n')
        result['position'] = position

        probe_el = table.find(text=re.compile(r'Клуб\s?'))
        if probe_el is None:
            self._logger.error(f'Не найден клуб для {url}')
        row = probe_el.find_parent('tr')
        club = row.select('a')[-1].text
        result['current_club'] = club

        match_table = table.select_one('table.ts-Спортивная_карьера-table')
        matches = match_table.select('tr')
        club_flag = False
        national_flag = False
        club_match_counter, national_match_counter = 0, 0
        missed_club_goal_counter, scored_club_goal_counter = 0, 0
        missed_national_goal_counter, scored_national_goal_counter = 0, 0
        for row in matches:
            probe = row.select_one('th')
            if probe is not None:
                if 'Клубная карьера' in probe.text:
                    club_flag = True
                    national_flag = False
                elif 'Национальная сборная' in probe.text:
                    club_flag = False
                    national_flag = True
                continue
            probe = row.select('td')
            if probe is None or len(probe) < 3:
                continue
            pattern = r'[−,-]?\d+'
            match = re.findall(pattern, probe[2].text)
            mathes_count = int(match[0] if len(match) > 0 else 0)
            gouls_count = int(match[1].replace('−', '-') if len(match) == 2 else 0)
            nation_team = None
            if club_flag:
                club_match_counter += mathes_count
                if 'вратарь' in position:
                    missed_club_goal_counter += abs(gouls_count)
                else:
                    scored_club_goal_counter += gouls_count
            elif national_flag:
                nation_team = probe[1].select('a')[-1]['title']
                if '(до' in nation_team or '(до' in probe[1].text or 'Флаг' in nation_team or 'Молодёжная' in nation_team or 'Олимпийская сборная' in nation_team:
                    continue
                national_match_counter += mathes_count
                if 'вратарь' in position:
                    missed_national_goal_counter += abs(gouls_count)
                else:
                    scored_national_goal_counter += gouls_count
            else:
                self._logger.error(f' В основной таблице для {url} пропущена строка по какой-то причине')

        result['national_team'] = self.comand_dict[url]
        result["club_caps"] = club_match_counter
        result["club_conceded"] = missed_club_goal_counter
        result["club_scored"] = scored_club_goal_counter
        result["national_caps"] = national_match_counter
        result["national_conceded"] = missed_national_goal_counter
        result["national_scored"] = scored_national_goal_counter

        return result