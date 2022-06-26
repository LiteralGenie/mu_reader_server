import logging
import multiprocessing
import time

from config import paths


def configure_logging(name_fn=None):
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    name_fn = name_fn or (lambda d: f'logs_{int(time.time())}_{d["pid"]}.log')
    data = dict(pid=multiprocessing.current_process().pid)
    debug_file = paths.LOG_DIR / name_fn(data)

    logging.basicConfig(
        filename=debug_file,
        filemode="w+",
        encoding="utf-8",
        format="%(asctime)s,%(msecs)03d %(levelname)s %(message)s",
        datefmt=r"%H:%M:%S",
        level=logging.DEBUG,
    )
