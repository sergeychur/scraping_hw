import time
from collections import deque
from urllib.parse import unquote

import requests

from runners.utils import Item
from utils.simple_rate_limiter import SimpleRateLimiter


class SimpleRunner:
    def __init__(self, parser, sink, logger, seed_urls, rate=5, max_tries=5):
        self._logger = logger.getChild("SyncRunner")
        self._parser = parser
        self._sink = sink

        self._rate_limiter = SimpleRateLimiter(rate)
        self._seen = set()
        self._to_process = deque()

        for elem in seed_urls:
            self._submit(Item(elem))

        self._max_tries = max_tries

    def _submit(self, item):
        self._to_process.appendleft(item)
        self._seen.add(item)

    def _download(self, item):
        time.sleep(self._rate_limiter.get_delay())
        resp = requests.get(item.url, timeout=60)
        resp.raise_for_status()
        content = resp.content
        return self._parser.parse(content, resp.url)

    def run(self):
        while self._to_process:
            item = self._to_process.pop()
            item.start = time.time()
            self._logger.info(f"Start: {unquote(item.url)}")

            try:
                result, next = self._download(item)
                item.end = time.time()

            except Exception as e:
                item.tries += 1
                item.end = time.time()
                duration = item.end - item.start
                if item.tries >= self._max_tries:
                    self._logger.error(f"Fail: {unquote(item.url)} {e}. Tries = {item.tries}. Duration: {duration}")
                    self._write(item, error=str(e))
                    continue
                self._logger.warning(f"Postpone: {unquote(item.url)} {e}. Tries = {item.tries}. Duration: {duration}")
                self._submit(item)
                continue

            self._logger.info(f"Success: {unquote(item.url)}. Tries = {item.tries}. Duration: {item.end - item.start}")

            if result:
                self._write(item, result=result)

            for elem in next:
                if elem in self._seen:
                    continue
                self._submit(Item(elem))

    def _write(self, item, result=None, error=None):
        if result is None and error is None:
            raise RuntimeError("Invalid result. Both result and error are None")

        if error:
            self._sink.write({"url": unquote(item.url), "error": error})
            return

        self._sink.write(result)
