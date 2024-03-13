from Runner import SimpleRunner
from css_selector_parser import CssSelectorParser
from FileSink import FileSink
import logging
import sys
import time


def main():
    logging.basicConfig(
        format='[%(asctime)s %(name)s %(levelname)s: %(message)s]',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )

    logger = logging.getLogger('Runner')
    start_url = [sys.argv[1]]
    output_file_name = sys.argv[2]

    parser = CssSelectorParser()
    sink = FileSink(output_file_name)
    runner = SimpleRunner(parser, sink, logger, start_url)

    start = time.time()
    runner.run()
    logger.info(f'total duration is {time.time() - start}')


if __name__ == '__main__':
    main()
