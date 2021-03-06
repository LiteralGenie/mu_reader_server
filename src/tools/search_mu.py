import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import logging
import random
import time

import requests
import utils
from config import paths
from urlpath import URL

debug_file = paths.LOG_DIR / "mu_search.log"
log = logging.basicConfig(
    filename=debug_file,
    filemode="w+",
    encoding="utf-8",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
)


db_file = paths.DATA_DIR / "search_db.json"
with open(db_file) as file:
    db = json.load(file)


MU_API = URL("https://api.mangaupdates.com/v1")


@utils.limit(calls=1, period=1, scope="mu")
def _search(name: str):
    ep = MU_API / "series" / "search"
    resp = requests.post(str(ep), json=dict(search=name))
    data = resp.json()
    assert resp.status_code == 200

    logging.debug(f"fetching [{name}] from [{ep}]")
    db[name] = dict(
        time=time.time(), ids=[x["record"]["series_id"] for x in data["results"]]
    )
    if random.random() < 0.05:
        logging.info("dumping db")
        with open(db_file, "w+") as file:
            json.dump(db, file, indent=2)

    return data


def search(name: str):
    name = name.lower()
    logging.debug(f"Searching for [{name}]")

    if name in db:
        return db[name]
    else:
        logging.info(f"cache miss for [{name}]")
        return _search(name)


start = time.time()
series_dir = Path("/home/anne/manga")
series = list(series_dir.glob("*"))
for i, s in enumerate(series):
    logging.info(f"processing [{s.name}]")
    print(f"[{time.time()-start:.1f}s] {i:05d} / {len(series)}...", end="\r")

    try:
        assert s.is_dir()
        data = search(s.name)
        continue
    except Exception as e:
        logging.exception(e)
