import aiohttp
import asyncio
from aiolimiter import AsyncLimiter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Item():
    def __init__(self, url: str, num_tries: int = 0):
        self.url = url
        self.num_tries = num_tries
        self.start = None

    class Config:
        allow_mutation = False

class AsyncRunner:
    def __init__(self, parser, writer, logger, seed_urls, rate=100, max_parallel=5, max_tries=25):
        self.logger = logger.getChild('AsyncRunner')
        self.parser = parser
        self.writer = writer
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.rate_limiter = AsyncLimiter(max_rate=rate, time_period=1)
        self.seen_urls = set(seed_urls)
        self.max_tries = max_tries
        self.tasks = set()

    async def fetch_and_parse(self, item):
        try:
            print(item.url)
            async with self.semaphore:
                await self.rate_limiter.acquire()
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                    async with session.get(item.url) as response:
                        response.raise_for_status()
                        content = await response.text()
                        return self.parser.parse(content.encode(), str(response.url)), None
        except Exception as e:
            return None, e

    async def process_item(self, item):
        if item.num_tries >= self.max_tries:
            self.logger.exception(f'Failed: {item.url} after {item.num_tries} attempts.')
            self.writer.write({'url': item.url, 'error': 'Max retries exceeded', 'tries': item.num_tries})
            return

        result, error = await self.fetch_and_parse(item)
        if error is not None:
            self.logger.warning(f'Error fetching {item.url}: {error}. Retrying...')
            item.num_tries += 1
            if item.num_tries < self.max_tries:
                await self.process_item(item)
            return
        
        result, next = result
        if result is not None:
            result.update({'url': item.url})
            self.writer.write(result)
            self.logger.info(f'Success: {item.url} in {item.num_tries} tries.')
        if next is None:
            return
        for next_url in next:
            if next_url not in self.seen_urls:
                self.seen_urls.add(next_url)
                await self.process_item(Item(url=next_url))

    async def run(self):
        tasks = [self.process_item(Item(url=url)) for url in self.seen_urls]
        await asyncio.gather(*tasks)
