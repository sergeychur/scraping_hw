import json
from pathlib import Path

class ResultWriter:
    def __init__(self, path: str | Path):
        self.__file = open(path, 'w', encoding="utf-8")

    def write(self, item):
        self.__file.write(f"{json.dumps(item, ensure_ascii=False)}\n")

    def __del__(self):
        self.__file.close()

