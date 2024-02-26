import re
from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin, urlparse

from runner.footbal_player import Player


class CssSelectorParser:
    _players_table_columns = ['№', 'Позиция', 'Игрок', 'Дата рождения / возраст', 'Матчи', 'Голы', 'Клуб']

    def _parse_root_page(self, root, domain):
        links = []
        table_elems = root.select("table.standard.sortable a")
        for e in table_elems:
            if e.has_attr('title') and 'Сборная' in e['title']:
                links.append(urljoin(domain, e['href']))
                break
        return [], links

    def _parse_team_page(self, root, domain):
        links = []
        tables = root.select('table.wikitable')
        Player.set_domain(domain)
        for table in tables:
            is_player_table = True
            index = 0
            for th in table.tbody.tr:
                stripped_text = th.text.strip()
                if stripped_text:
                    print(stripped_text)
                    if stripped_text != self._players_table_columns[index]:
                        is_player_table = False
                    index += 1
                    if index == len(self._players_table_columns):
                        break

            if is_player_table:
                for row_counter, tr in enumerate(table.tbody):
                    player_params = []
                    if row_counter == 0:
                        continue
                    column_counter = 0
                    for td in tr:
                        for tag in td:
                            if isinstance(tag, Tag):
                                if column_counter == 1 and tag.a is not None:
                                    tag = tag.a
                                if column_counter == 1 and tag.has_attr('title') and tag.has_attr('href'):
                                    player_params.append(tag['href'].strip())
                                    player_params.append(tag['title'].strip())
                                    column_counter += 1
                                    break
                                else:
                                    if tag.has_attr('title'):
                                        if column_counter == 5:
                                            player_params.append(tag.text.strip())
                                        else:
                                            player_params.append(tag['title'].strip())
                                        column_counter += 1
                                        break
                            else:
                                if tag.strip() and column_counter != 0:
                                    player_params.append(tag.strip())
                                    column_counter += 1
                                    break

                    if player_params:
                        player = Player(*player_params[:7])
                        if player.is_url_exists():
                            links.append(player.get_url())

        return [], links

    def _player_page_get_club_inf(self, tr, tag):
        l = []
        if tag is not None:
            if 'Всего за карьеру' in tag.text:
                l = []
                for td in tr:
                    if td.text is not None and td.text.strip():
                        l.append(td.text)
        return l

    def _parse_player_page(self, root, url):
        player = Player.pop_player(url)
        height = root.find('span', {'data-wikidata-property-id': 'P2048'}).text[:3]
        player.set_height(int(height))
        position = root.find('span', {'data-wikidata-property-id': 'P413'}).text
        if position and position is not None:
            player.set_position(position)
        tr_tags = root.select('tr')
        for tr in tr_tags:
            l = self._player_page_get_club_inf(tr, tr.td)
            if not l:
                l = self._player_page_get_club_inf(tr, tr.th)
            if len(l)>1:
                player.set_club_caps(int(l[-2].strip()))
                player.set_club_goals(int(l[-1].strip().replace('−', '-')))
                break
        table_elems = root.select_one("table.ts-Спортивная_карьера-table.threecolumns.stripped")
        club_section = False
        national_section = False
        goals_sum = games_sum = 0
        club = ''
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
                        club = l[-2]
                        games, goals = l[-1].split(' ')
                        goals_sum += int(goals[1:-1].replace('−', '-'))
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
                if l:
                    national_info = l

        if len(national_info)>1 and not('(' in national_info[-2]):
            games, goals = national_info[-1].split(' ')
            player.set_national_team(national_info[-2])
            player.set_national_goals(int(goals[1:-1].replace('−', '-')))
            player.set_national_caps(int(games))

        player.set_club_goals(goals_sum)
        player.set_club_caps(games_sum)
        player.set_club(club.replace('→  ', ''))
        return player, []

    def parse(self, content, url):
        soup = BeautifulSoup(content, 'html.parser')
        netloc = urlparse(url).netloc
        scheme = urlparse(url).scheme
        domain = scheme + '://' + netloc
        page_title = soup.select_one('div.mw-content-ltr.mw-parser-output').table['data-name']
        if page_title is not None and 'Соревнование' in page_title:
            result, links = self._parse_root_page(soup, domain)
            return result, links

        if page_title is not None and 'Сборная' in page_title:
            result, links = self._parse_team_page(soup, domain)
            return result, links

        # else
        result, links = self._parse_player_page(soup, url)
        return result, links
