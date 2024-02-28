import time
import logging
import argparse

from parsers.css_selector_parser import CssSelectorParser
from utils.file_sink import FileSink
from runners.simple_runner import SimpleRunner


def get_args():
    parser = argparse.ArgumentParser(description='parse footbol players from wiki')
    parser.add_argument('url')
    parser.add_argument('result_filepath', default='./result.jsonl')
    args = parser.parse_args()
    return args.url, args.result_filepath


def main():
    url, result_filepath = get_args()
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    logger = logging.getLogger('Runner')

    seed_urls = [url]
    
    parser = CssSelectorParser(logging.getLogger('Parser'))
    sink = FileSink(result_filepath, './parse_logs.jsonl')
    runner = SimpleRunner(parser, sink, logger, seed_urls, max_tries=5, rate=1)

    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')


if __name__ == '__main__':
    main()
