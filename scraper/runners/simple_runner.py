import time
import requests

from collections import deque
from datetime import datetime
from logging import Logger

from item import Item
from parsers.css_selector_parser import CssSelectorParser
from utils.file_sink import FileSink
from utils.simple_rate_limiter import SimpleRateLimiter

'''
Runner обходит страницы:
    - делает запрос и получает контент
    - одает контент парсеру и получает нужную информацию и дочерние страницы
    - сохраняет нужную информацию  с помощью sink (кто выбирает формат сохранения?)
    - проходит по страницам

нужную информацию извлекает парсер
дочерние страницы выбирает парсер
'''


class SimpleRunner:
    def __init__(
            self, parser: CssSelectorParser, 
            sink: FileSink, logger: Logger, 
            seed_urls: list[str], rate: int = 100, 
            max_tries: int = 5, host_time_interval_sec: float = 1
        ) -> None:
        self._parser = parser
        self._sink = sink
        self._logger = logger.getChild('SyncRunner')

        self._rate_limiter = SimpleRateLimiter(rate)
        self._max_tries = max_tries

        self._seen: set[str] = set()
        self._to_process: deque[Item] = deque()
        for url in seed_urls:
            self._submit(Item(url))

    def _submit(self, item: Item) -> None:
        self._to_process.append(item)
        self._seen.add(item.url)

    def _download(self, item: Item) -> tuple[str, list[str] | None]:
        time.sleep(self._rate_limiter.get_delay())
        resp = requests.get(item.url, timeout=60)
        resp.raise_for_status()
        content = resp.content
        return self._parser.parse(content, resp.url)

    def run(self):
        while self._to_process:
            item = self._to_process.popleft()
            item.start = time.time()
            self._logger.info(f'start: {item.url}') 

            try:
                result, next_urls = self._download(item)
                item.end = time.time()
            except Exception as e:  # TODO: change exception?, from request, from parser
                item.tries += 1
                item.end = time.time()
                duration = item.end - item.start

                if item.tries >= self._max_tries:
                    self._logger.info(f'fail: {item.url} {e}. tries={item.tries}. duration={duration}')
                    self._write(item, err=str(e))
                    continue

                self._logger.warning(f'postpone: {item.url} {e}. tries={item.tries}. duration={duration}')
                self._to_process.append(item)
            else:
                self._logger.info(f'success: {item.url}. tries={item.tries}. duration={item.end - item.start}')
                if result is not None:
                    self._write(item, result)
                for url in next_urls:
                    if url not in self._seen:
                        self._to_process.append(Item(url))
    
    def _write(self, item: Item, result: str, err: str | None) -> None:
        # TODO: change
        if result is None and err is None:
            raise RuntimeError('Invalid result. Both result and error are None')
        to_write = {'tries': item.tries, 'result': result, 'error': err}
        self._sink.write(to_write)