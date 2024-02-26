import logging
import sys

from runner.simple_runner import SimpleRunner
from runner.css_parser import CssSelectorParser
from runner.file_sink import FileSink

def main():
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    args = sys.argv
    logger = logging.getLogger('Runner')
    seed_urls = [args[1]]
    parser = CssSelectorParser()
    sink = FileSink(args[2])
    runner = SimpleRunner(parser, sink, logger, seed_urls)
    runner.run()


if __name__ == '__main__':
    main()