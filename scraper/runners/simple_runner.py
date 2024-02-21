import requests

from collections import deque
from datetime import datetime
from logging import Logger

from item import Item
from parsers.css_selector_parser import CssSelectorParser
from utils.file_sink import FileSink

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
        self._logger = logger
        self._seed_urls = seed_urls
        self._rate = rate
        self._max_tries = max_tries
        self._host_time_interval_sec = host_time_interval_sec

        self._host2start: dict[str, datetime] = {}

        self._seen = set()
        self._to_process = deque()
        for url in self._seed_urls:
            self._to_process.append(Item(url))
    
    def _check_time(self, item: Item) -> bool:
        interval = self._host2start.get(item.host, datetime.now()) - datetime.now() 
        return interval.total_seconds() > self._host_time_interval_sec
    
    def _process(self, item: Item) -> tuple[str | None, list[str]]:
        self._host2start[item.host] = datetime.now()
        resp = requests.get(item.url)
        return self._parser(resp.content, item.url1)

    def _write(self, item: Item, result: str, err: str | None):
        # TODO: change
        if err is not None:
            self._sink.write({'error': str(err), 'result': None, 'url': item.url})
        else:
            self._sink.write({'error': None, 'result': result, 'url': item.url})

    def run(self):
        while self._to_process:
            item = self._to_process.popleft()
            
            # for friendly
            if not self._check_time(item):
                self._to_process.append(item)
                continue

            try:
                result, next_urls = self._process(item)
            except Exception as e:  # TODO: change exception?, from request, from parser
                item.tries += 1

                self._logger.error('url=%s; tries=%d; err=%s;', item.url, item.tries, str(e))

                if item.tries > self._max_tries:
                    self._logger.info(
                        'url=%s; tries=%d; msg=%s', 
                        item.url, item.tries,
                        f"max_tries={self._max_tries} is reached"
                    )
                    self._write(item, err=e)
                else:
                    self._to_process.append(item)
            else:
                if result is not None:
                    self._write(result)
                for url in self._filter(next_urls):
                    self._to_process.append(Item(url))