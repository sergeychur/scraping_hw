import logging
import time
import argparse

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
    #seed_urls = ['https://ru.wikipedia.org/wiki/%D0%A3%D0%B8%D0%BB%D1%8C%D1%8F%D0%BC%D1%81,_%D0%9D%D0%B8%D0%BA%D0%BE']
    parser = CssSelectorParser(logger)
    sink = FileSink(args.result_filepath)
    runner = SimpleRunner(parser, sink, logger, seed_urls)
    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')

if __name__ == '__main__':
    main()