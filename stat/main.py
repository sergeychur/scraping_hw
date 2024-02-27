import argparse
import json

from datetime import datetime,timedelta


def get_args():
    parser = argparse.ArgumentParser(description='calc certain stat about footbool players')
    parser.add_argument('result_filepath', default='./result.jsonl')
    args = parser.parse_args()
    return args.result_filepath

def get_name(names):
    return names[1] + " " + names[0]

def calc_stats(filepath):
    """
    имя игрока младше 25 лет, сыгравшего больше всего матчей за за клубную карьеру (club_caps)
    имя игрока младше 25 лет, забившего больше всего голов за клубную карьеру (club_scored)
    имя самого высокого игрока, забившего больше 10 голов (height)

    имя самого старшего вратаря (bith)
    имя игрока сыгравшего больше всего матчей за сборную (national_caps)
    имя игрока забившего больше всего голов за сборную (national_scored)
    """
    current = [
        ['', 0],
        ['', 0],
        ['', 0],

        ['', 0],
        ['', 0],
        ['', 0]
    ]   
    with open(filepath) as file:
        for line in file.readlines():
            player = json.loads(line)
            birth = player['birth']
            birth_date = datetime.utcfromtimestamp(birth)
            younger_25 = (datetime.now() - birth_date) < timedelta(days=25*365)

            if younger_25 and player['club_caps'] > current[0][1]:
                current[0][0] = get_name(player['name'])
                current[0][1] = player['club_caps']
            
            if younger_25 and player['club_scored'] > current[1][1]:
                current[1][0] = get_name(player['name'])
                current[1][1] = player['club_scored']
            
            if player['club_scored'] + player['national_scored'] > 10 and player['height'] > current[2][1]:
                current[2][0] = get_name(player['name'])
                current[2][1] = player['height']
            
            if player['position'] == 'вратарь' and (not current[3][0] or player['birth'] < current[2][1]):
                current[3][0] = get_name(player['name'])
                current[3][1] = player['birth']
            
            if player['national_caps'] > current[4][1]:
                current[4][0] = get_name(player['name'])
                current[4][1] = player['national_caps']
            
            if player['national_scored'] > current[5][1]:
                current[5][0] = get_name(player['name'])
                current[5][1] = player['national_scored']
    return [lst[0] for lst in current]



def main():
    result_filepath = get_args()
    print(result_filepath)
    result = calc_stats(result_filepath)
    with open('stat_result.txt', 'w') as file:
        for name in result:
            file.write(name + '\n')


if __name__ == '__main__':
    main()