import logging
import sys
import time

from parsers.parser import CssParser
from runners.runner import SimpleRunner
from utils.file_sink import FileSink


def main(argv: list[str]):
    logging.basicConfig(
        format="[%(asctime)s] %(name)s %(levelname)s: %(message)s", datefmt="%d-%m-%y %H:%M:%S", level="INFO"
    )
    logger = logging.getLogger("Runner")

    seed_urls = [argv[1]]

    parser = CssParser()

    sink = FileSink(argv[2])

    runner = SimpleRunner(parser, sink, logger, seed_urls)

    start = time.time()
    runner.run()
    logger.info(f"Total duration is {time.time() - start}")


if __name__ == "__main__":
    main(sys.argv)
