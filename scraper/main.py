import time
import logging

from parsers.css_selector_parser import CssSelectorParser
from utils.file_sink import FileSink
from runners.simple_runner import SimpleRunner


def main():
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    logger = logging.getLogger('Runner')

    seed_urls = ['https://ru.wikipedia.org/wiki/%D0%A7%D0%B5%D0%BC%D0%BF%D0%B8%D0%BE%D0%BD%D0%B0%D1%82_%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D1%8B_%D0%BF%D0%BE_%D1%84%D1%83%D1%82%D0%B1%D0%BE%D0%BB%D1%83_2024']
    # seed_urls = ['https://ru.wikipedia.org/wiki/%D0%A1%D0%B1%D0%BE%D1%80%D0%BD%D0%B0%D1%8F_%D0%9F%D0%BE%D1%80%D1%82%D1%83%D0%B3%D0%B0%D0%BB%D0%B8%D0%B8_%D0%BF%D0%BE_%D1%84%D1%83%D1%82%D0%B1%D0%BE%D0%BB%D1%83']
    
    parser = CssSelectorParser(logging.getLogger('Parser'))
    sink = FileSink('./result.jsonl', './parse_logs.jsonl')
    runner = SimpleRunner(parser, sink, logger, seed_urls, max_tries=1)

    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')


if __name__ == '__main__':
    main()