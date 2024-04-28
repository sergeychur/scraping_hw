import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup


class CssParser:
    def __init__(self):
        self._teams = {}
        
    def parse(self, content, cur_page_url):
        soup = BeautifulSoup(content, "html.parser")

        ln = soup.select_one("body div .infobox")["data-name"]

        if "Соревнование" in ln:
            return None, self._parse_chempoinship(soup, cur_page_url)

        if "Сборная" in ln:
            return None, self._parse_team(soup, cur_page_url)

        return self._parse_player(soup, cur_page_url), []

    def _parse_chempoinship(self, root, cur_page_url):
        self._teams = {}
        table = root.select("table.standard tr td:nth-child(1) > a")

        links = [ln.get("href") for ln in table]
        parsed = urlparse(cur_page_url)
        links = [urljoin(parsed.scheme + "://" + parsed.netloc, ln) for ln in links]

        return links

    def _parse_team(self, root, cur_page_url):
        parsed = urlparse(cur_page_url)
        
        pointer = root.find("span", id=re.compile("^Текущий_состав"))
        if not pointer:
            pointer = root.find("span", id=re.compile("^Состав"))
        pointer = pointer.parent

        while not (pointer.name and pointer.name == "table"):
            pointer = pointer.next_sibling

        table = pointer.tbody.select("tr")
        table = [ln.select_one("td:nth-child(3) > a") for ln in table]

        links = [ln.get("href") for ln in table if ln]
        links = [ln for ln in links if "index.php" not in ln]
        
        pointer = root.find("span", id=re.compile("^Недавние_вызовы"))
        if not pointer:
            links = [urljoin(parsed.scheme + "://" + parsed.netloc, ln) for ln in links]
        else:
            pointer = pointer.parent

            while not (pointer.name and pointer.name == "table"):
                pointer = pointer.next_sibling

            table = pointer.tbody.select("tr")
            table = [ln.select_one("td:nth-child(3) > a") for ln in table]

            links += [ln.get("href") for ln in table if ln]
            links = [ln for ln in links if "index.php" not in ln]

        
        links = [urljoin(parsed.scheme + "://" + parsed.netloc, ln) for ln in links]

        ln = unquote(cur_page_url).split("/")[-1].replace("_", " ").strip()
        for l in links:
            self._teams[l] = ln

        return links

    def _parse_player(self, root, cur_page_url):
        info = {}

        info["url"] = cur_page_url

        self._find_name(root, info)
        self._read_infobox(root, info)
        self._transform_height(info)
        self._find_club_caps(root, info)
        self._find_national_caps(root, info)
        self._find_national_team(cur_page_url, info)
        self._transform_birth(info)

        return info

    def _find_name(self, root, info) -> None:
        name = root.select_one(".infobox tbody tr .ts_Спортсмен_имя").text
        bracket = name.rfind("(")
        if bracket > 0:
            name = name[:bracket]
        info["name"] = list(map(str.strip, name.rsplit(" ", 1)))[::-1]

    def _read_infobox(self, root, info) -> None:
        infobox = root.select_one(".infobox-above").parent
        translate = {"Рост": "height", "Позиция": "position", "Клуб": "current_club", "Родился": "birth"}

        while infobox.th:
            if infobox.th.text in translate:
                ln = ""
                if infobox.th.text == "Позиция":
                    roles = infobox.select("a")
                    if len(roles) > 1:
                        ln = "\n".join([p.text.strip() for p in roles])
                    else:
                        ln = infobox.td.text
                else:
                    ln = infobox.td.text.strip()
                info[translate[infobox.th.text]] = ln.strip().replace("\n", ", ")
            infobox = infobox.next_sibling
            if not infobox.name:
                infobox = infobox.next_sibling
            if infobox.td and "infobox-image" in infobox.td.__dict__["attrs"]["class"]:
                infobox = infobox.next_sibling
            if not infobox.name:
                infobox = infobox.next_sibling

    def _transform_height(self, info) -> None:
        if "height" not in info:
            return
        info["height"] = info["height"].split()[0]
        bracket = info["height"].find("[")
        if bracket > 0:
            info["height"] = info["height"][:bracket]
        info["height"] = info["height"].replace(",", "")
        info["height"] = info["height"].split("—")[-1]
        info["height"] = int(info["height"])

    def _find_club_caps(self, root, info) -> None:
        pointer = root.select_one(".infobox table tbody tr")
        while "Клубная карьера" not in pointer.text:
            pointer = pointer.next_sibling
            if not pointer.name:
                pointer = pointer.next_sibling

        pointer = pointer.next_sibling
        if not pointer.name:
            pointer = pointer.next_sibling

        from_table = 0
        sc_from_table = 0
        cell = pointer.select_one("td:nth-child(3)")
        while cell:
            ln, sc = cell.text.strip().split("(")
            bracket = sc.find(")")
            sc = sc[:bracket].replace("−", "-").replace("–", "-")
            slash = sc.find("/")
            if slash > 0:
                sc = sc[:slash]
            if "?" in sc:
                sc = "0"
            if ln.strip().isdigit():
                from_table += int(ln)
                sc_from_table += int(sc)
            pointer = pointer.next_sibling
            if not pointer.name:
                pointer = pointer.next_sibling
            if not pointer:
                break
            cell = pointer.select_one("td:nth-child(3)")

        tables = root.select("table tbody tr")
        from_cell = 0
        sc_from_cell = 0
        for t in tables:
            if "infobox" in t.parent.parent.__dict__["attrs"].get("class", [""]):
                continue
            if not t.th:
                continue
            if t.th.text.strip() != "Клуб":
                t = t.next_sibling
                if not t:
                    continue
                if not t.name:
                    t = t.next_sibling
                if not t.th or t.th.text != "Клуб":
                    continue

            t_temp = t.parent.select_one("tr:last-child").select_one("th:last-child")
            if not t_temp:
                t_temp = t.parent.select_one("tr:last-child").select_one("td:last-child")
            t = t_temp

            t = t.previous_sibling
            if not t.name:
                t = t.previous_sibling
            if "−" in t.text or "-" in t.text:
                t = t.previous_sibling
                if not t.name:
                    t = t.previous_sibling
            from_cell = int("0" if "?" in t.text else t.text.strip())
            t = t.next_sibling
            if not t.name:
                t = t.next_sibling
            if "?" in t.text:
                sc_from_cell = 0
            else:
                sc_from_cell = int(t.text.strip().replace("−", "-").replace("–", "-"))
            break

        info["club_caps"] = max(from_table, from_cell)
        if sc_from_table < 0 or sc_from_cell < 0:
            info["club_conceded"] = abs(min(sc_from_cell, sc_from_table))
            info["club_scored"] = 0
        else:
            info["club_conceded"] = 0
            info["club_scored"] = max(sc_from_table, sc_from_cell)

    def _find_national_caps(self, root, info) -> None:
        pointer = root.select_one(".infobox table tbody tr")
        while "Национальная сборная" not in pointer.text:
            pointer = pointer.next_sibling
            if not pointer.name:
                pointer = pointer.next_sibling
            if not pointer:
                info["national_caps"] = 0
                info["national_conceded"] = 0
                info["national_scored"] = 0
                return

        pointer = pointer.next_sibling
        if not pointer.name:
            pointer = pointer.next_sibling

        from_table = 0
        sc_from_table = 0
        cell = pointer.select_one("td:nth-child(2)")
        while cell:
            if "до" not in cell.text:
                cell = cell.next_sibling
                if not cell.name:
                    cell = cell.next_sibling
                ln, sc = cell.text.strip().split("(")
                bracket = sc.find(")")
                sc = sc[:bracket].replace("−", "-").replace("–", "-")
                slash = sc.find("/")
                if slash > 0:
                    sc = sc[:slash]
                if "?" in sc:
                    sc = "0"
                if ln.strip().isdigit():
                    from_table += int(ln)
                sc_from_table += int(sc)

            pointer = pointer.next_sibling
            if not pointer.name:
                pointer = pointer.next_sibling
            if not pointer:
                break
            cell = pointer.select_one("td:nth-child(2)")

        info["national_caps"] = from_table
        if sc_from_table < 0:
            info["national_conceded"] = abs(sc_from_table)
            info["national_scored"] = 0
        else:
            info["national_conceded"] = 0
            info["national_scored"] = sc_from_table

    def _find_national_team(self, url, info):
        info["national_team"] = self._teams[url]
        del self._teams[url]
        """pointer = root.select_one(".infobox tbody tr td table tbody tr:last-child")
        possible = pointer.select_one("td:nth-child(2) > a")

        ln = possible["title"] if possible else ""
        while not ln or not re.search("[сС]борная .*? по футболу", ln):
            pointer = pointer.previous_sibling
            if not pointer:
                ln = ""
                break
            if not pointer.name:
                pointer = pointer.previous_sibling
            if not pointer:
                ln = ""
                break
            possible = pointer.select_one("td:nth-child(2) > a")
            if not possible:
                continue
            ln = possible["title"]

        ln = re.search("[сС]борная .*? по футболу", ln)
        ln = "С" + ln[0][1:] if ln else ""
        info["national_team"] = ln"""

    def _transform_birth(self, info):
        ln = info["birth"].split("(")[0].split("[")[0].strip()
        dictionary = {
            "января": "01",
            "февраля": "02",
            "марта": "03",
            "апреля": "04",
            "мая": "05",
            "июня": "06",
            "июля": "07",
            "августа": "08",
            "сентября": "09",
            "октября": "10",
            "ноября": "11",
            "декабря": "12",
        }
        for m in dictionary.items():
            ln = ln.replace(m[0], m[1])
        birth = datetime.strptime(ln, "%d %m %Y")
        info["birth"] = int(datetime.timestamp(birth))
