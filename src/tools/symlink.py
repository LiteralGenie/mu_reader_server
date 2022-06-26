import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import logging
import multiprocessing
import re

from config import paths

UNLINK = 0

debug_file = paths.LOG_DIR / "komga_debug.log"
log = logging.basicConfig(
    filename="./debug.log",
    filemode="w+",
    encoding="utf-8",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
)


def allUnique(lst):
    pool = set()
    for x in lst:
        if x not in pool:
            pool.add(x)
        else:
            return x

    return True


if __name__ == "__main__":
    madokami_dirs = [
        Path("/media/anne/media_temp/madokami/"),
        Path("/media/anne/media_2/madokami/"),
    ]
    output_dir = Path("/home/anne/manga")
    output_dir.mkdir(parents=True, exist_ok=True)

    if UNLINK:
        logging.debug("unlinking...")
        old_links = [f for f in output_dir.rglob("*") if f.is_symlink()]
        [f.unlink() for f in old_links]
        assert all(not f.exists() for f in old_links)
        logging.debug("done unlinking")

    letters = list()
    for dir in madokami_dirs:
        letters.extend(dir.glob("*"))
    assert all(len(f.name) == 1 for f in letters)

    series = [s for l in letters for s in l.glob("*")]

    def process_series(s: str):
        # logging.debug(f'found series {s}')
        print(f"found series {s}")

        tmp = list(s.glob("**/*"))
        files = [f for f in tmp if not f.is_dir()]
        assert allUnique(files) is True

        series_name = re.sub(r'[.?:"]', "", s.name).strip()
        series_dir = output_dir / series_name
        series_dir.mkdir(exist_ok=True, parents=True)
        for f in files:
            file_name = re.sub(r'["?:]', "", f.name).strip()
            out_file = series_dir / file_name
            if out_file.exists():
                if UNLINK:
                    msg = f"link to file already exists: {out_file}\n"
                    msg += "\n\t".join(str(f) for f in files)
                    # logging.warning(msg)
                    print(msg)
            else:
                print(f"creating {f.name}")
                out_file.symlink_to(f)

    with multiprocessing.Pool(16) as pool:
        pool.map(process_series, series)
    # [process_series(x) for x in series]
