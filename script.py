import json
from dateutil import parser
import sys
import datetime as DT
import calendar


def main():
    data = []

    file = sys.argv[1]

    with open(file, encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    start = DT.datetime(1999, 1, 1, 0, 0, 0)
    utc_tuple = start.utctimetuple()
    years_25 = calendar.timegm(utc_tuple)

    matches = 0
    goals = 0
    height = 0
    first_player = None
    second_player = None
    third_player = None
    fourth_player = None
    fifth_player = None
    sixth_player = None
    years = 10**11

    for player in data:
        if 'error' in player.keys():
            continue

        if player['birth'] > years_25 and matches < player['club_caps']:
            matches = player["club_caps"]
            first_player = player

    for player in data:
        if "error" in player.keys():
            continue

        if (
            player["birth"] > years_25
            and goals < player["club_scored"]
        ):
            goals = player["club_scored"]
            second_player = player

    for player in data:
        if "error" in player.keys():
            continue

        if player['club_scored'] + player['national_scored'] > 10 and height < player['height']:
            height = player["height"]
            third_player = player

    for player in data:
        if "error" in player.keys():
            continue

        if player['position'] == 'вратарь' and years > player['birth']:
            years = player["birth"]
            fourth_player = player

    matches = 0

    for player in data:
        if "error" in player.keys():
            continue

        if matches < player["national_caps"]:
            matches = player["national_caps"]
            fifth_player = player

    goals = 0

    for player in data:
        if "error" in player.keys():
            continue

        if goals < player["national_scored"]:
            goals = player["national_scored"]
            sixth_player = player

    print(first_player['name'])
    print(second_player['name'])
    print(third_player['name'])
    print(fourth_player['name'])
    print(fifth_player['name'])
    print(sixth_player['name'])


if __name__ == '__main__':
    main()
