import re
from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin, urlparse

from runner.footbal_player import Player


class CssSelectorParser:

    def _parse_root_page(self, root, domain):
        links = []
        table_elems = root.select("table.standard.sortable a")
        for e in table_elems:
            if e.has_attr('title') and 'Сборная' in e['title']:
                links.append(urljoin(domain, e['href']))
        return [], links

    def _parse_team_table(self, table, logger):
        rows = table.find_all(['th', 'tr'])
        links = []
        if rows is None:
            return links

        for row in rows:
            if row is None:
                continue

            player_params = []
            for value in row:
                if isinstance(value, Tag) and value.a is not None:
                    if value.find('span', {'class': 'bday'}):
                        player_params.append(value.span['title'])
                        continue
                    if value.a.has_attr('href') and value.a.has_attr('title'):
                        player_params.append(value.a['href'])
                        player_params.append(value.a['title'])

            player_params = player_params[2:5]
            if player_params:
                player = Player(*player_params)
                if player.is_url_exists():
                    links.append(player.get_url())
                else:
                    logger.warning(f'Player page with {player.get_url()} does not exist. Skipping...')

        return links

    def _find_table_under_heading(self, header):
        next_node = header
        while True:
            next_node = next_node.next_sibling
            if next_node is None:
                return None
            if isinstance(next_node, Tag):
                if next_node.name == "table":
                    return next_node

    def _parse_team_page(self, root, domain, logger):
        links = []
        Player.set_domain(domain)
        header = root.find('span', {'id': 'Текущий_состав'})
        if header is None:
            header = root.find('span', {'id': 'Текущий_состав_сборной'})
        if header is not None:
            table = self._find_table_under_heading(header.parent)
            if table is not None:
                links.extend(self._parse_team_table(table, logger))

        header = root.find('span', {'id': 'Недавние_вызовы'})
        if header is not None:
            table = self._find_table_under_heading(header.parent)
            if table is not None:
                links.extend(self._parse_team_table(table, logger))

        return [], links

    def _parse_player_page(self, root, url):
        player = Player.pop_player(url)
        footbal_player_table = root.find('table', {'data-name': 'Футболист'})
        height = footbal_player_table.find('span', {'data-wikidata-property-id': 'P2048'}).text[:3]
        player.set_height(height)
        position = footbal_player_table.find('span', {'data-wikidata-property-id': 'P413'}).text
        player.set_position(position)

        club = footbal_player_table.find('span', {'data-wikidata-property-id': 'P54'})
        tmp = [a for a in club]
        player.set_club(tmp[-1].text)

        header = root.find('span', {'id': 'Клубная_карьера_2'})
        if header is None:
            header = root.find('span', {'id': 'Статистика_выступлений'})

        if header is not None:
            table = self._find_table_under_heading(header.parent)
            if table is not None:
                rows = table.find_all(['th', 'td'])
                f = False
                l = []
                for row in rows:
                    if 'Всего' in row.text or f:
                        f = True
                        if row.text.strip():
                            l.append(row.text.strip())
                if len(l) > 1:
                    player.set_club_caps(int(l[-2].strip()))
                    player.set_club_goals(int(l[-1].strip().replace('−', '-').replace('–', '-')))

        table_elems = root.select_one("table.ts-Спортивная_карьера-table.threecolumns.stripped")
        club_section = False
        national_section = False
        goals_sum = games_sum = 0
        national_info = []
        for tr in table_elems.tbody:
            if isinstance(tr, Tag) and tr.th is not None and 'Клубная карьера' in tr.th:
                club_section = True
            if  isinstance(tr, Tag) and tr.th is not None and 'Национальная сборная' in tr.th:
                club_section = False
                national_section = True
            l = []
            if club_section:
                for td in tr:
                    if isinstance(td, Tag):
                        l.append(td.text.strip())
                if l:
                    try:
                        games, goals = l[-1].split(' ')
                        goals_sum += int(goals[1:-1].replace('−', '-').replace('–', '-'))
                        games_sum += int(games)
                    except Exception as e:
                        pass
            if national_section:
                for td in tr:
                    if isinstance(td, Tag):
                        tmp = []
                        if td.a is not None:
                            for a in td:
                                if isinstance(a, Tag):
                                    if a.has_attr('title'):
                                        tmp.append(a)
                            if tmp:
                                l.append(tmp[-1]['title'])
                        else:
                            l.append(td.text.strip())
                if l and 'н.' in l[0]:
                    national_info = l

        if len(national_info)>1 and not('(' in national_info[-2]):
            games, goals = national_info[-1].split(' ')
            player.set_national_team(national_info[-2])
            player.set_national_goals(int(goals[1:-1].replace('−', '-').replace('–','-')))
            player.set_national_caps(int(games))

        player.set_club_goals(goals_sum)
        player.set_club_caps(games_sum)
        return player, []

    def parse(self, content, url, logger):
        soup = BeautifulSoup(content, 'html.parser')
        netloc = urlparse(url).netloc
        scheme = urlparse(url).scheme
        domain = scheme + '://' + netloc
        page_title = soup.select_one('div.mw-content-ltr.mw-parser-output').table['data-name']
        if page_title is not None and 'Соревнование' in page_title:
            result, links = self._parse_root_page(soup, domain)
            return result, links

        if page_title is not None and 'Сборная' in page_title:
            result, links = self._parse_team_page(soup, domain, logger)
            return result, links

        # else
        result, links = self._parse_player_page(soup, url)
        return result, links
