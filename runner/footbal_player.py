import json
from datetime import datetime


class Player:
    players = {}

    def __init__(self, position, page_url, full_name, birth, games_number, goals, club, national_team):
        self.url = 'https://ru.wikipedia.org' + page_url
        self.name = full_name.replace(',', '').split(' ')[:2]
        self.height = None
        self.position = position.split(' ')[0].lower()
        self.current_club = club
        self.club_caps = 0
        self.club_conceded = 0
        self.club_scored = 0
        self.national_caps = int(games_number)
        if self.position == 'вратарь':
            if goals[0] == '−' or goals[0] == '-':
                self.national_conceded = int(goals[1:])
            else:
                self.national_conceded = int(goals)
            self.national_scored = 0
        else:
            self.national_conceded = 0
            self.national_scored = int(goals)
        self.national_team = national_team
        self.birth = int(datetime.strptime(birth, "%Y-%m-%d").timestamp())

        if self.is_url_exists():
            self.players[self.url] = self

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def get_url(self):
        return self.url

    def is_url_exists(self):
        return not('redlink=1' in self.url)

    @classmethod
    def pop_player(cls, url):
        player = cls.players[url]
        del cls.players[url]
        return player
    
    def set_height(self, height):
        self.height = int(height)

    def set_club_caps(self, club_caps):
        self.club_caps = max(int(club_caps), self.club_caps)

    def set_club_goals(self, club_goals):
        if self.position == 'вратарь':
            club_goals *= -1
            self.club_conceded = max(int(club_goals), self.club_conceded)
        else:
            self.club_scored = max(int(club_goals), self.club_scored)

    def set_national_caps(self, national_caps):
        self.national_caps = max(int(national_caps), self.national_caps)

    def set_national_goals(self, national_goals):
        if self.position == 'вратарь':
            national_goals *= -1
            self.national_conceded = max(int(national_goals), self.national_conceded)
        else:
            self.national_scored = max(int(national_goals), self.national_scored)