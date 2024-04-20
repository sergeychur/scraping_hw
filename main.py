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
    logger = logging.getLogger('Runner')
    seed_url = ['https://ru.wikipedia.org/wiki/%D0%A7%D0%B5%D0%BC%D0%BF%D0%B8%D0%BE%D0%BD%D0%B0%D1%82_%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D1%8B_%D0%BF%D0%BE_%D1%84%D1%83%D1%82%D0%B1%D0%BE%D0%BB%D1%83_2024']
    parser = Parser()
    sink = FileSink('./result.jsonl')
    runner = SimpleRunner(parser, sink, logger, seed_url)
    start = time.time()
    runner.run()
    logger.info(f'Total duration is {time.time() - start}')


if __name__ == '__main__':
    main()
