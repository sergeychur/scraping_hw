import aiohttp
import asyncio
import time

from utils.simple_rate_limiter import SimpleRateLimiter
from runners.item import Item


class AsyncRunner:
    def __init__(self, parser, sink, logger, seed_urls, rate=100, max_parallel=5, max_tries=5) -> None:
        self._logger = logger.getChild('AsyncRunner')
        self._parser = parser
        self._sink = sink

        self._semaphore = asyncio.Semaphore(max_parallel)
        self._in_air = set()
        self._rate_limiter = SimpleRateLimiter(rate)
        self._seen = set()
        self._seed_urls = seed_urls
        self._max_tries = max_tries
        self._future_to_item = {}

    def _submit(self, item):
        item.start = time.time()
        item.tries += 1
        future = asyncio.ensure_future(self._download(item))
        self._in_air.add(future)
        self._future_to_item[future] = item
        self._logger.info(f'start: {item.url}')
        self._seen.add(item.url)
    
    async def _download(self, item):
        async with self._semaphore:
            await asyncio.sleep(self._rate_limiter.get_delay())
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.get(item.url) as resp:
                    resp.raise_for_status()
                    content = await resp.text()
                    return self._parser.parse(content.encode(), str(resp.url), item.extra_info)
    
    async def run(self):
        for url in self._seed_urls:
            self._submit(Item(url))
        while self._in_air:
            done, in_air = await asyncio.wait(self._in_air, return_when=asyncio.FIRST_COMPLETED)
            self._in_air = in_air
            for future in done:
                item = self._future_to_item.pop(future)
                try:
                    result, next_urls = future.result()
                except Exception as e:
                    duration = time.time() - item.start
                    if item.tries >= self._max_tries:
                        self._write(item, error=str(e))
                        self._logger.exception(f'fail: {item.url}. tries={item.tries}. duration={duration}. error={e}')
                    else:
                        self._submit(item)
                        self._logger.warning(f'postpone: {item.url}. tries={item.tries}. duration={duration}. error={e}')
                else:
                    if result is not None:
                        self._write(item, result)
                    for next_item in next_urls:
                        if next_item['url'] not in self._seen:
                            self._submit(Item(next_item['url'], next_item['extra_info']))
                    self._logger.info(f'success: {item.url}. tries={item.tries}. duration={time.time() - item.start}')
    
    def _write(self, item: Item, result = None, error = None) -> None:
        if result is None and error is None:
            raise RuntimeError('Invalid result. Both result and error are None')
        to_write = {'url': item.url,'tries': item.tries, 'result': result, 'error': error}
        self._sink.write(to_write)
