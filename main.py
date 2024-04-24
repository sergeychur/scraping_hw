import logging
import time
import argparse
import asyncio

from runner import AsyncRunner
from pageparser import PlayerParser
from writer import ResultWriter

def setup_logging():
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level=logging.INFO,
    )
    return logging.getLogger('Runner')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Asynchronous Web Crawler")
    parser.add_argument('url', help="The URL to start crawling from")
    parser.add_argument('result_path', default='./result.jsonl', help="The filepath where results will be saved")
    return parser.parse_args()

async def run_async_crawl(url, result_path, logger):
    seed_urls = [url]
    url_parser = PlayerParser(logger)
    writer = ResultWriter(result_path)
    runner = AsyncRunner(url_parser, writer, logger, seed_urls, rate=10, max_tries=5, max_parallel=50)
    
    start = time.time()
    await runner.run()
    logger.info(f'Parsing took {time.time() - start}')

def main():
    logger = setup_logging()
    args = parse_arguments()
    asyncio.run(run_async_crawl(args.url, args.result_path, logger))

if __name__ == '__main__':
    main()
