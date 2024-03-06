import json
from datetime import datetime
from urllib.parse import urljoin


class Player:
    players = {}
    DOMAIN = 'https://ru.wikipedia.org'

    def __init__(self, page_url, full_name, birth):
        self.url = urljoin(self.DOMAIN, page_url)
        if '(' in full_name:
            full_name = full_name[:full_name.find('(')]
        splited_fullname = full_name.replace(',', '').split(' ')
        self.name = ['', '']
        self.name[0] = splited_fullname[0].strip()
        self.name[1] = ' '.join(splited_fullname[1:]).strip()
        self.height = None
        self.position = None
        self.current_club = None
        self.club_caps = 0
        self.club_conceded = 0
        self.club_scored = 0
        self.national_caps = 0
        self.national_conceded = 0
        self.national_scored = 0
        self.national_team = None
        self.birth = int(datetime.strptime(birth, "%Y-%m-%d").timestamp())
        if self.is_url_exists():
            self.players[self.url] = self

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def pop_player(cls, url):
        player = cls.players[url]
        del cls.players[url]
        if player.name[1] == 'Жота':
            player.name[0], player.name[1] = player.name[1], player.name[0]
        return player

    @classmethod
    def set_domain(cls, domain):
        cls.DOMAIN = domain

    def get_url(self):
        return self.url

    def is_url_exists(self):
        return not('redlink=1' in self.url)
    
    def set_height(self, height):
        self.height = int(height.split(' ')[0])

    def set_club_caps(self, club_caps):
        self.club_caps = max(int(club_caps), self.club_caps)

    def set_club_goals(self, club_goals):
        if self.position == 'вратарь':
            club_goals *= -1
            self.club_conceded = max(int(club_goals), self.club_conceded)
        else:
            self.club_scored = max(int(club_goals), self.club_scored)

    def set_national_caps(self, national_caps):
        self.national_caps = int(national_caps)

    def set_national_goals(self, national_goals):
        if self.position == 'вратарь':
            national_goals *= -1
            self.national_conceded = max(int(national_goals), self.national_conceded)
        else:
            self.national_scored = max(int(national_goals), self.national_scored)

    def set_national_team(self, team):
        self.national_team = team

    def set_position(self, position):
        self.position = position

    def set_club(self, club):
        self.current_club = club
