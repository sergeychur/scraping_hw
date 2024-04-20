import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class CssParser:
    def parse(self, content, cur_page_url):
        soup = BeautifulSoup(content, "html.parser")

        if "Чемпионат" in soup.title.text:
            return None, self._parse_chempoinship(soup, cur_page_url)

        if "Сборная" in soup.title.text:
            return None, self._parse_team(soup, cur_page_url)

        return self._parse_player(soup, cur_page_url), []

    def _parse_chempoinship(self, root, cur_page_url):
        table = root.select("table.standard tr td:nth-child(1) > a")

        links = [ln.get("href") for ln in table]
        links = [urljoin("https://ru.wikipedia.org/", ln) for ln in links]

        return links

    def _parse_team(self, root, cur_page_url):
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
        links = [urljoin("https://ru.wikipedia.org/", ln) for ln in links]

        return links

    def _parse_player(self, root, cur_page_url):
        info = {}

        info["url"] = cur_page_url

        self._find_name(root, info)
        self._read_infobox(root, info)
        self._transform_height(info)

        return info

    def _find_name(self, root, info) -> None:
        name = root.title.text
        name = name[: name.rfind("—") - 1]
        bracket = name.rfind("(")
        if bracket > 0:
            name = name[:bracket]
        info["name"] = list(map(str.strip, name.split(",")))
        if len(info["name"]) < 2:
            info["name"] = list(map(str.strip, info["name"][0].split()))

    def _read_infobox(self, root, info) -> None:
        infobox = root.select_one(".infobox-above").parent
        translate = {"Рост": "height", "Позиция": "position", "Клуб": "current_club"}

        while infobox.th:
            if infobox.th.text in translate:
                ln = ""
                if infobox.th.text == "Позиция":
                    ln = "\n".join([p.text for p in infobox.select("a")])
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
