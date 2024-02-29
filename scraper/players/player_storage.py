class PlayerStorage:
    def __init__(self):
        self.players = {}
    
    def add_player(self, url, info):
        self.players[url] = {
            'url': url,
            'name': [info['surname'], info['name']],
            'national_team': info['national_team']
        }

    def extend_player(self, url, info):
        player = self.players[url]
        player['height'] = info['height']
        player['position'] = info['position']
        player['current_club'] = info['current_club']
        player['club_conceded'] = info['club_conceded']
        player['club_scored'] = info['club_scored']
        player['national_caps'] = info['national_caps']
        player['national_conceded'] = info['national_conceded']
        player['national_scored'] = info['national_scored']
        player['birth'] = info['birth']
        self.players[url] = player
        return player