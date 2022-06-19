import logging
import multiprocessing
import time

from config import paths


def configure_logging():
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    proc = multiprocessing.current_process()
    debug_file = paths.LOG_DIR / f'logs_{int(time.time())}_{proc.pid}.log'
    logging.basicConfig(
        filename=debug_file,
        filemode='w+',
        encoding='utf-8',
        format='%(asctime)s,%(msecs)03d %(levelname)s %(message)s',
        datefmt=r'%H:%M:%S',
        level=logging.DEBUG
    )
