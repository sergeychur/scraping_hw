import logging
import time

from runner.simple_runner import SimpleRunner
from parser.parser import Parser
from utils.file_sink import FileSink


def main():
    logging.basicConfig(
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%d-%m-%y %H:%M:%S',
        level='INFO',
    )
    logger = logging.getLogger('runner')
    seed_urls = [
        'https://ru.wikipedia.org/wiki/%D0%A0%D0%B0%D0%BC%D0%B0%D0%B4%D0%B0%D0%BD%D0%B8,_%D0%AE%D0%BB%D1%8C%D0%B1%D0%B5%D1%80',
        'https://ru.wikipedia.org/wiki/%D0%9A%D1%80%D0%B8%D1%88%D1%82%D0%B8%D0%B0%D0%BD%D1%83_%D0%A0%D0%BE%D0%BD%D0%B0%D0%BB%D0%B4%D1%83',
        'https://ru.wikipedia.org/wiki/%D0%9D%D0%B5%D0%BB%D1%8C%D1%81%D1%81%D0%BE%D0%BD,_%D0%92%D0%B8%D0%BA%D1%82%D0%BE%D1%80',
        # 'https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B9%D0%B2%D0%B0%D0%BB%D1%8C%D0%B4,_%D0%9D%D0%B8%D0%BA%D0%BE%D0%BB%D0%B0%D1%81',
        # 'https://ru.wikipedia.org/wiki/%D0%A0%D0%B0%D1%88%D1%84%D0%BE%D1%80%D0%B4,_%D0%9C%D0%B0%D1%80%D0%BA%D1%83%D1%81',
        # 'https://ru.wikipedia.org/wiki/%D0%A9%D0%B5%D0%BD%D1%81%D0%BD%D1%8B%D0%B9,_%D0%92%D0%BE%D0%B9%D1%86%D0%B5%D1%85'
        'https://ru.wikipedia.org/wiki/%D0%A7%D0%B5%D0%BC%D0%BF%D0%B8%D0%BE%D0%BD%D0%B0%D1%82_%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D1%8B_%D0%BF%D0%BE_%D1%84%D1%83%D1%82%D0%B1%D0%BE%D0%BB%D1%83_2024'
    ]
    parser = Parser()
    sink = FileSink('./result.jsonl')
    runner = SimpleRunner(parser, sink, logger, seed_urls)
    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')


if __name__ == '__main__':
    main()
