from collections import deque
import requests
import time

from SimpleRateLimiter import SimpleRateLimiter


class Item:
    def __init__(self, url, tries=0):
        self.url = url
        self.start = None
        self.tries = tries


class SimpleRunner:
    def __init__(self, parser, sink, logger, seed_urls, rate=100, max_tries=100):
        self._logger = logger.getChild("SyncRunner")
        self._parser = parser
        self._sink = sink

        self._rate_limiter = SimpleRateLimiter(rate)
        self._seen = set()
        self._to_process = deque()
        for elem in seed_urls:
            self._submit(Item(elem))
        self._max_tries = max_tries

    def _download(self, item):
        time.sleep(self._rate_limiter.get_delay())
        resp = requests.get(item.url, timeout=60)
        resp.raise_for_status()
        content = resp.content
        return self._parser.parse(content, item.url)

    def _submit(self, item):
        self._to_process.append(item)
        self._seen.add(item.url)

    def run(self):
        while self._to_process:
            item = self._to_process.popleft()
            item.start = time.time()
            self._logger.info(f"Start: {item.url}")
            try:
                result, next_links = self._download(item)
                item.end = time.time()
            except Exception as e:
                item.tries += 1
                item.end = time.time()
                duration = item.end - item.start
                if item.tries >= self._max_tries:
                    self._logger.error(
                        f"Fail: {item.url} {e}. Tries = {item.tries}. Duration: {duration}"
                    )
                    self._write(item, error=str(e))
                    continue
                self._logger.warning(
                    f"Postpone: {item.url} {e}. Tries = {item.tries}. Duration: {duration}"
                )
                continue
            self._logger.info(
                f"Success: {item.url}. Tries = {item.tries}. Duration: {item.end - item.start}"
            )
            if result:
                self._logger.info(f"Write {result}")
                self._write(result)
            for elem in next_links:
                if elem in self._seen:
                    continue
                self._submit(Item(elem))

    def _write(self, result=None, error=None):
        if result is None and error is None:
            raise RuntimeError("Invalid result. Both result and error are None")
        self._sink.write(result)
