import argparse
import logging
import time
from parser.parser import Parser

from runner.simple_runner import SimpleRunner
from utils.file_sink import FileSink
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description='Process seed URL and path to result')
    parser.add_argument('seed_url', metavar='seed_url', type=str, help='seed url to parse')
    parser.add_argument('path_to_result', metavar='path_to_result', type=str, help='path to save the result')
    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    logger = logging.getLogger('runner')

    parsed = urlparse(args.seed_url)
    domain = parsed.scheme + '://' + parsed.netloc
    parser = Parser(domain)

    sink = FileSink(args.path_to_result)
    runner = SimpleRunner(parser, sink, logger, [args.seed_url])
    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')


if __name__ == '__main__':
    main()
