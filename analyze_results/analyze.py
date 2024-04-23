'''
Запросы:
(1) club_caps       - имя игрока младше 25 лет, сыгравшего больше всего матчей за клубную карьеру;
(2) club_scored     - имя игрока, забившего больше всего голов за клубную карьеру;
(3) height          - имя самого высокого игрока, забившего больше 10 голов;
(4) birth           - имя самого старшего вратаря;
(5) national_caps   - имя игрока, сыгравшего больше всего матчей за сборную;
(6) national_scored - имя игрока, забившего больше всего голов за сборную.
'''
import argparse
import json
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description='Process seed URL and path to result')
    parser.add_argument('parsing_result', metavar='parsing_result', type=str, help='file with players stats')
    parser.add_argument('path_to_result', metavar='path_to_result', type=str, help='path to save the result')
    args = parser.parse_args()

    answer = [('', 0) for _ in range(6)]
    answer[3] = ('', datetime.now(timezone.utc).timestamp())

    with open(args.parsing_result, 'r') as f:
        lines = f.readlines()
    for line in lines:
        player = json.loads(line)

        answer[0] = update_1(player, answer[0])
        answer[1] = update_2(player, answer[1])
        answer[2] = update_3(player, answer[2])
        answer[3] = update_4(player, answer[3])
        answer[4] = update_5(player, answer[4])
        answer[5] = update_6(player, answer[5])
    with open(args.path_to_result, 'w') as f:
        for elem in answer:
            f.write(f'{elem[0]}\n')


def update_1(player, current):
    current_timestamp = datetime.now(timezone.utc).timestamp()
    years = (current_timestamp - player['birth']) // (60 * 60 * 24 * 365.25)
    if years < 25:
        if player['club_caps'] > current[1]:
            return (player['name'][1], player['club_caps'])
    return current


def update_2(player, current):
    if player['club_scored'] > current[1]:
        return (player['name'][1], player['club_scored'])
    return current


def update_3(player, current):
    if not player['height']:
        return current
    if player['club_scored'] + player['national_scored'] > 10:
        if player['height'] > current[1]:
            return (player['name'][1], player['height'])
    return current


def update_4(player, current):
    if player['position'] == 'вратарь' and player['birth'] < current[1]:
        return (player['name'][1], player['birth'])
    return current


def update_5(player, current):
    if player['national_caps'] > current[1]:
        return (player['name'][1], player['national_caps'])
    return current


def update_6(player, current):
    if player['national_scored'] > current[1]:
        return (player['name'][1], player['national_scored'])
    return current


if __name__ == '__main__':
    main()
