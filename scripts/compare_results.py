import json
import sys
import traceback
from urllib.parse import unquote

def load_result(path_to_file):
    with open(path_to_file) as f:
        result = {}
        for elem in map(lambda x: json.loads(x), f):
            cur_url = elem.get('url')
            if cur_url is None:
                raise RuntimeError('Result element has to include url field')
            result[cur_url] = elem
        return result


if len(sys.argv) != 3:
    raise ValueError(f'Usage: {sys.argv[0]} <path to expected result> <path to real result>')


expected = load_result(sys.argv[1])
real = load_result(sys.argv[2])

fields_to_compare = [
    'name',
    'height',
    'position',
    'current_club',
    'club_caps',
    'club_conceded',
    'club_scored',
    'national_caps',
    'national_conceded',
    'national_scored',
    'national_team',
    'birth',
]

has_fails = False

for url, expected_value in expected.items():
    real_value = real.get(url)
    if real_value is None:
        print(f'Real result doesn\'t contain element for url {unquote(url)}')
        has_fails = True
        continue
    for field in fields_to_compare:
        expected_field_value = expected_value.get(field)
        real_field_value = real_value.get(field)
        if expected_field_value != real_field_value:
            print(f'URL: {unquote(url)}. Expected value for field {field} = {expected_field_value} while real is {real_field_value}')
            has_fails = True
            continue

exit(0 if not has_fails else -1)
