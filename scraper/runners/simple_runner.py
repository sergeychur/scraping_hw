import time
import requests

from collections import deque
from runners.item import Item
from utils.simple_rate_limiter import SimpleRateLimiter


class SimpleRunner:
    def __init__(self, parser, sink, logger, seed_urls, rate = 100, max_tries: int = 5):
        self._parser = parser
        self._sink = sink
        self._logger = logger.getChild('SyncRunner')

        self._rate_limiter = SimpleRateLimiter(rate)
        self._max_tries = max_tries

        self._seen= set()
        self._to_process= deque()
        for url in seed_urls:
            self._submit(Item(url))

    def _submit(self, item) -> None:
        self._to_process.append(item)
        self._seen.add(item.url)

    def _download(self, item):
        time.sleep(self._rate_limiter.get_delay())
        resp = requests.get(item.url, timeout=60)
        resp.raise_for_status()
        content = resp.content
        return self._parser.parse(content, resp.url, item.extra_info)

    def run(self):
        while self._to_process:
            item = self._to_process.popleft()
            item.start = time.time()
            self._logger.info(f'start: {item.url}') 

            try:
                item.tries += 1
                result, next_urls = self._download(item)
                item.end = time.time()
            except Exception as e:
                item.end = time.time()
                duration = item.end - item.start
                if item.tries >= self._max_tries:
                    self._logger.error(f'fail: {item.url}. tries={item.tries}. duration={duration}. error={e}')
                    self._write(item, err=str(e))
                    continue

                self._logger.warning(f'postpone: {item.url}. tries={item.tries}. duration={duration}. error={e}')
                self._to_process.append(item)
            else:
                self._logger.info(f'success: {item.url}. tries={item.tries}. duration={item.end - item.start}')
                if result is not None:
                    self._write(item, result)
                for next_item in next_urls:
                    if next_item['url'] not in self._seen:
                        self._to_process.append(Item(next_item['url'], next_item['extra_info']))
    
    def _write(self, item: Item, result = None, err = None) -> None:
        if result is None and err is None:
            raise RuntimeError('Invalid result. Both result and error are None')
        to_write = {'url': item.url,'tries': item.tries, 'result': result, 'error': err}
        self._sink.write(to_write)