import time
from collections import deque

import requests
from bs4 import BeautifulSoup

from runner import Item
from runner.simple_rate_limiter import SimpleRateLimiter
from urllib.parse import unquote


class SimpleRunner:
    def __init__(self, parser, sink, logger, seed_urls, rate=100, max_tries=5):
        self._parser = parser
        self._sink = sink
        self._logger = logger
        self._rate_limiter = SimpleRateLimiter(rate)

        self._max_tries = max_tries

        self._seen = set()
        self._items_to_load = deque()
        for seed_url in seed_urls:
            self._add(Item(seed_url))

        self._start_time = None

    def run(self):
        self._logger.info('Start')
        self._start_time = time.time()
        while self._items_to_load:
            current_item = self._items_to_load.pop()
            if content := self._load_page(current_item):
                current_item.content = BeautifulSoup(content, 'html.parser')
            else:
                continue
            try:
                extracted = self._parser.parse(current_item)
                if isinstance(extracted, dict):
                    self._sink.write(extracted)
                    self._logger.info(f'Scraped player {unquote(current_item.url)}')
                    continue
                if not extracted:
                    self._logger.info(f'Not scraped from url {unquote(current_item.url)}')
                    continue
                self._logger.info(f'Scraped from url {unquote(current_item.url)} items: {len(extracted)}')
                for item in extracted:
                    self._add(item)
                self._seen.add(current_item.url)
            except Exception as exep:
                self._logger.error(f'Failed to scrape {unquote(current_item.url)}, exception: {exep}')

    def _load_page(self, item):
        time.sleep(self._rate_limiter.get_delay())
        item.start = time.time()

        try:
            response = requests.get(item.url, timeout=60)
            response.raise_for_status()
        except Exception:
            item.tries += 1
            if item.tries >= self._max_tries:
                self._logger.warning(f'Download tries limit exceeded {unquote(item.url)} DURATION {time.time() - item.start}')
                return None
            else:
                self._logger.info(f'One more try {unquote(item.url)} DURATION {time.time() - item.start}')
                return self._load_page(item)
        self._logger.info(f'Loaded page: {unquote(item.url)}')
        return response.text

    def _add(self, item: Item) -> None:
        self._items_to_load.appendleft(item)
        self._seen.add(item)
