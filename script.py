import json
from dateutil import parser


def main():
    data = []

    with open("results.jsonl", encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    matches = 0
    goals = 0
    height = 0
    years_25 = int(parser.parse(f"1999.1.1").timestamp())
    first_player = None
    second_player = None
    third_player = None
    fourth_player = None
    fifth_player = None
    sixth_player = None
    years = 10**11

    for player in data:
        if player['error'] is not None:
            continue

        if player['result']['birth'] > years_25 and matches < player['result']['club_caps']:
            matches = player["result"]["club_caps"]
            first_player = player["result"]

    for player in data:
        if player["error"] is not None:
            continue

        if (
            player["result"]["birth"] > years_25
            and goals < player["result"]["club_scored"]
        ):
            goals = player["result"]["club_scored"]
            second_player = player["result"]

    for player in data:
        if player['error'] is not None:
            continue

        if player['result']['club_scored'] + player['result']['national_scored'] > 10 and height < player['result']['height']:
            height = player["result"]["height"]
            third_player = player["result"]

    for player in data:
        if player['error'] is not None:
            continue

        if player['result']['position'] == 'вратарь' and years > player['result']['birth']:
            years = player['result']["birth"]
            fourth_player = player["result"]

    matches = 0

    for player in data:
        if player['error'] is not None:
            continue

        if matches < player["result"]["national_caps"]:
            matches = player["result"]["national_caps"]
            fifth_player = player["result"]

    goals = 0

    for player in data:
        if player["error"] is not None:
            continue

        if goals < player["result"]["national_scored"]:
            goals = player["result"]["national_scored"]
            sixth_player = player["result"]

    print(first_player['name'])
    print(second_player['name'])
    print(third_player['name'])
    print(fourth_player['name'])
    print(fifth_player['name'])
    print(sixth_player['name'])

if __name__ == '__main__':
    main()
