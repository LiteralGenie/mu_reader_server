import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import logging
import sqlite3
import sys
import time
from re import I

import requests
import utils
from classes import database
from config import paths
from urlpath import URL

###

ROOT_DIR = Path(__file__).parent

###

debug_file = paths.LOG_DIR / f"mu_scrape_{time.time():.0f}.log"
log = logging.basicConfig(
    filename=debug_file,
    filemode="w+",
    encoding="utf-8",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
)

###

search_db_file = paths.DATA_DIR / "search_db.json"
with open(search_db_file) as file:
    search_db = json.load(file)

db = sqlite3.connect(paths.DB_FILE)
cursor = db.cursor()

###

MU_API = URL("https://api.mangaupdates.com/v1")


@utils.limit(calls=1, period=1, scope="mu")
def search(id: int):
    ep = MU_API / "series" / str(id)
    resp = requests.get(str(ep))
    data = resp.json()
    assert resp.status_code == 200

    logging.debug(f"fetched series [{id}] from [{ep}]")
    return data


###

ids = set()
for x in search_db.values():
    ids.update(x["ids"])
ids = list(ids)
ids.sort()

for (idx, id) in enumerate(ids):
    print(f"{idx:05d} / {len(ids)}", end="\r")

    try:
        result = cursor.execute(f"SELECT id FROM series WHERE id={id}").fetchone()
        if result is None:
            data = search(id)
            database.insert_series(data, cursor, op="REPLACE")
    except Exception as e:
        logging.exception(f"Error processing [{id=}]\n{e}")
        continue
    if idx % 100 == 0:
        db.commit()

db.close()

###
