from Runner import AsyncRunner
from css_selector_parser import CssSelectorParser
from FileSink import FileSink
import logging
import sys
import time
import asyncio


def main():
    logging.basicConfig(
        format="[%(asctime)s %(name)s %(levelname)s: %(message)s]",
        datefmt="%d-%m-%y %H:%M:%S",
        level="INFO",
    )

    logger = logging.getLogger("Runner")
    start_url = [sys.argv[1]]
    output_file_name = sys.argv[2]

    parser = CssSelectorParser()
    sink = FileSink(output_file_name)

    async def start_func():
        runner = AsyncRunner(
            parser, sink, logger, start_url, rate=10, max_tries=2, max_parallel=10
        )

        start = time.time()
        await runner.run()
        logger.info(f"Total duration is {time.time() - start}")

    asyncio.run(start_func())


if __name__ == "__main__":
    main()
