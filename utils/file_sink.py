import json
from typing import Any, Dict


class FileSink:
    def __init__(self, path: str):
        self._file = open(path, "w")

    def write(self, item: Dict[str, Any]) -> None:
#        self._file.write(json.dumps(item, ensure_ascii=False, indent=2) + "\n")
        self._file.write(json.dumps(item, ensure_ascii=False) + "\n")

    def __del__(self):
        self._file.close()
