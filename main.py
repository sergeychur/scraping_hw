import logging
import time
import argparse
import asyncio

from runners.async_runner import AsyncRunner
from runners.simple_runner import SimpleRunner
from parsers.css_selector_parser import CssSelectorParser
from utils.file_sink import FileSink

def main():
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('result_filepath', default='./result.jsonl')
    args = parser.parse_args()

    logger = logging.getLogger('Runner')
    seed_urls = [args.url]
    #seed_urls = ['https://ru.wikipedia.org/wiki/%D0%93%D0%B0%D0%B9%D1%8F,_%D0%A5%D0%BE%D1%81%D0%B5_%D0%9B%D1%83%D0%B8%D1%81']
    parser = CssSelectorParser(logger)
    sink = FileSink(args.result_filepath)
    # runner = SimpleRunner(parser, sink, logger, seed_urls)
    # start = time.time()
    # runner.run()
    # logger.info(f'Total duration is {time.time() - start}')

    async def run_async_crawl():
        runner = AsyncRunner(parser, sink, logger, seed_urls, rate=1, max_tries=5, max_parallel=5)
        start = time.time()
        await runner.run()
        logger.info(f'Total duration is {time.time() - start}')
    asyncio.run(run_async_crawl())

if __name__ == '__main__':
    main()