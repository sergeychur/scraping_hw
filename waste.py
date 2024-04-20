import re
import requests
from bs4 import BeautifulSoup


def parse_team_page(soup):
    pointer = soup.find('span', id=re.compile('^Текущий_состав'))
    if not pointer:
        pointer = soup.find('span', id=re.compile('^Состав'))
    pointer = pointer.parent
    while not (pointer.name and pointer.name == 'table'):
        pointer = pointer.next_sibling

    table = pointer.tbody.select('tr')
    selected_players = [ln.select_one('td:nth-child(3) > a[class!=new]') for ln in table]
    urls = list(filter(lambda ln: ln, selected_players))
    urls = list(x.get('href') for x in urls)
    return urls
    # urls_join_domain = list(map(lambda x: urljoin(self.DOMAIN, x), urls))
    # player_items = list(map(lambda x: Item(url=x, status='team'), urls_join_domain))
    # return cleaned_answer


response = requests.get('https://ru.wikipedia.org/wiki/%D0%A1%D0%B1%D0%BE%D1%80%D0%BD%D0%B0%D1%8F_%D0%90%D0%BB%D0%B1%D0%B0%D0%BD%D0%B8%D0%B8_%D0%BF%D0%BE_%D1%84%D1%83%D1%82%D0%B1%D0%BE%D0%BB%D1%83')
soup = BeautifulSoup(response.text, 'html.parser')
urls = parse_team_page(soup)
print(urls)
