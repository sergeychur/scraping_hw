import asyncio
import time
import logging
import argparse

from parsers.css_selector_parser import CssSelectorParser
from utils.file_sink import FileSink
from runners.simple_runner import SimpleRunner
from runners.async_runner import AsyncRunner
from players.player_storage import PlayerStorage


def get_args():
    parser = argparse.ArgumentParser(description='parse footbol players from wiki')
    parser.add_argument('url')
    parser.add_argument('result_filepath', default='./result.jsonl')
    args = parser.parse_args()
    return args.url, args.result_filepath


async def run_async_crawl(parser, sink, logger, seed_urls):
        runner = AsyncRunner(parser, sink, logger, seed_urls, max_tries=2, max_parallel=10, rate=100)
        start = time.time()
        await runner.run()
        logger.info(f'Total duration is {time.time() - start}')


def main():
    url, result_filepath = get_args()
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    logger = logging.getLogger('Runner')

    seed_urls = [url]
    
    storage = PlayerStorage()
    parser = CssSelectorParser(logging.getLogger('Parser'), storage)
    sink = FileSink(result_filepath, './parse_logs.jsonl')

    # rate=100, duration: 261.0369007587433
    runner = SimpleRunner(parser, sink, logger, seed_urls, max_tries=1, rate=1)
    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')

    # duration: 78.7185070514679
    # asyncio.run(run_async_crawl(parser, sink, logger, seed_urls))

if __name__ == '__main__':
    main()
